"""Additional attribution controls; preserves historical campaigns and RNG streams."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from multiprocessing import Pool
from pathlib import Path
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.cec_harness.run_camino_alterno import _specs, _run_arm, PROBLEMS, PAIRS
from cooperative.orchestrator import CooperativeRunner
from cooperative.functional_intent import PRESETS_V2
from problems.continuous.cec_problem import CECProblem,FESLimitProblem

class TracedRunner(CooperativeRunner):
    def __init__(self,*args,mode='trace',schedule=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.mode=mode; self.schedule=schedule; self.index=0; self.trace=[]
        self.record()
    def record(self):
        self.trace.append({'fes':int(self.problem.fes),'own':{e['name']:e['budget'].fes for e in self.solvers},'states':{n:c.intent for n,c in self._controllers.items()}})
    def _control_point_parametric(self):
        if self.mode=='trace':super()._control_point_parametric()
        elif self.mode=='replay':
            self.index+=1
            row=self.schedule[self.index]
            assert row['fes']==self.problem.fes
            assert row['own']=={e['name']:e['budget'].fes for e in self.solvers}
            for name,intent in row['states'].items():
                if intent is None:self._controllers[name].reset()
                else:self._controllers[name].set_intent(intent)
        elif self.mode!='neutral':raise ValueError(self.mode)
        self.record()
    def run(self):
        out=super().run()
        # Terminal row closes the final interval; no new action is applied.
        self.record();out['schedule']=self.trace
        if self.mode=='replay':assert len(self.trace)==len(self.schedule)
        return out

def exposure(schedule):
    counts=Counter()
    for a,b in zip(schedule,schedule[1:]):
        for name,intent in a['states'].items():counts[(name,intent)]+=b['own'][name]-a['own'][name]
    return counts

def permute(schedule,seed):
    out=json.loads(json.dumps(schedule));rng=np.random.default_rng(seed+987_000_000)
    for name in schedule[0]['states']:
        groups=defaultdict(list)
        for i,(a,b) in enumerate(zip(schedule,schedule[1:])):
            if a['states'][name] is not None:groups[b['own'][name]-a['own'][name]].append(i)
        for ids in groups.values():
            labels=[schedule[i]['states'][name] for i in ids]
            labels=[labels[j] for j in rng.permutation(len(labels))]
            for i,label in zip(ids,labels):out[i]['states'][name]=label
    assert exposure(out)==exposure(schedule)
    assert [[v is None for v in r['states'].values()] for r in out]==[[v is None for v in r['states'].values()] for r in schedule]
    changed=sum(a['states']!=b['states'] for a,b in zip(out,schedule))
    return out,changed

def run_one(pair,suite,f,budget,seed,mode='trace',schedule=None):
    a,b=pair.split('+')
    runner=TracedRunner(FESLimitProblem(CECProblem(suite,f,10),max_fes=budget),_specs(a,b),
        transfer_every=500,gate_enabled=True,seed=seed,transfer_mode='parametric',
        intent_mode='source',presets=PRESETS_V2,mode=mode,schedule=schedule)
    result=runner.run();assert result['fes_used']==budget
    return result

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj));tmp.replace(path)

def cell(job):
    pair,suite,f,budget,out,identity,kind=job
    path=Path(out)/pair.replace('+','')/str(budget)/f'{suite}_F{f}.json'
    if path.exists():
        old=json.loads(path.read_text());assert old['identity']==identity and len(old['seeds'])==51
        return str(path),'skip'
    original=json.loads((ROOT/'results/cooperative/camino_alterno_v06'/f"{pair.replace('+','')}_{budget}"/f'{suite}_F{f}.json').read_text())
    # Bridge the old independent portfolio before reusing its paired results.
    a,b=pair.split('+');bridge,_=_run_arm('C1_div',a,b,suite,f,budget,13000,{})
    assert bridge==original['errors']['C1_div'][0],('portfolio bridge',pair,suite,f,budget)
    errors=defaultdict(list);changed=[];traces=[];t0=time.monotonic()
    for idx in range(51):
        seed=13000+idx
        if kind in ('executor','all'):
            neutral=run_one(pair,suite,f,budget,seed,'neutral');errors['C1_shared'].append(neutral['best_fitness'])
        if kind in ('exposure','all'):
            traced=run_one(pair,suite,f,budget,seed)
            assert traced['best_fitness']==original['errors']['C3p'][idx],('trace bridge',pair,suite,f,budget,seed)
            replay=run_one(pair,suite,f,budget,seed,'replay',traced['schedule'])
            assert replay['best_fitness']==traced['best_fitness'],('identity replay',pair,suite,f,budget,seed)
            assert replay['schedule']==traced['schedule']
            shuffled,n=permute(traced['schedule'],seed)
            other=run_one(pair,suite,f,budget,seed,'replay',shuffled)
            for arm,result in [('C3p',traced),('REPLAY',replay),('PERMUTED',other)]:errors[arm].append(result['best_fitness'])
            changed.append(n);traces.append({'seed':seed,'source':traced['schedule'],'permuted':shuffled})
    result={'identity':identity,'pair':pair,'suite':suite,'fnum':f,'budget':budget,'dim':10,'seeds':list(range(13000,13051)), 'errors':dict(errors),'changed_windows':changed,'bridge_portfolio':True,'seconds':time.monotonic()-t0}
    if traces:
        import gzip
        tp=path.with_suffix('.traces.json.gz');tp.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(tp,'wt') as stream:json.dump(traces,stream)
        result['trace_sha256']=hashlib.sha256(tp.read_bytes()).hexdigest()
    write(path,result);return str(path),'done'

def smoke():
    report=[]
    for pair in PAIRS:
        r=run_one(pair,'CEC2014',1,5000,99001)
        q=run_one(pair,'CEC2014',1,5000,99001,'replay',r['schedule'])
        assert r['best_fitness']==q['best_fitness'] and r['schedule']==q['schedule']
        shuffled,n=permute(r['schedule'],99001)
        z=run_one(pair,'CEC2014',1,5000,99001,'replay',shuffled)
        neutral=run_one(pair,'CEC2014',1,5000,99001,'neutral')
        assert all(all(v is None for v in row['states'].values()) for row in neutral['schedule'])
        report.append({'pair':pair,'identity_replay':True,'fes':z['fes_used'],'exposure_conserved':exposure(shuffled)==exposure(r['schedule']),'changed_windows':n})
    # Synthetic case guarantees a non-degenerate shuffle without optimizer outcomes.
    rows=[{'fes':i*10,'own':{'A':i*5},'states':{'A':x}} for i,x in enumerate([None,'INTENSIFY','DIVERSIFY','INTENSIFY','DIVERSIFY',None])]
    q,n=permute(rows,99000);assert n>0 and exposure(rows)==exposure(q)
    print(json.dumps({'smoke':report,'synthetic_changed_windows':n}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['smoke','run']);ap.add_argument('--out');ap.add_argument('--freeze');ap.add_argument('--jobs',type=int,default=8);ap.add_argument('--kind',choices=['executor','exposure','all'],default='executor');args=ap.parse_args()
    if args.command=='smoke':smoke()
    else:
        frozen=json.loads(Path(args.freeze).read_text())
        for relative,h in frozen['source_sha256'].items():assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==h,relative
        identity=hashlib.sha256(Path(args.freeze).read_bytes()).hexdigest()+':'+args.kind
        jobs=[(pair,suite,f,budget,args.out,identity,args.kind) for budget in [5000,50000] for pair in PAIRS for suite,f in PROBLEMS]
        with Pool(args.jobs) as pool:
            for i,result in enumerate(pool.imap_unordered(cell,jobs),1):print(i,len(jobs),*result,flush=True)
