"""Fixed-budget external reference for the additional attribution campaign."""
import argparse,hashlib,json,sys,time
from pathlib import Path
from multiprocessing import Pool
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from algorithms.minion_adapter import LSHADE_M
from problems.continuous.cec_problem import CECProblem,FESLimitProblem
from scripts.cec_harness.run_camino_alterno import PROBLEMS
OPTIONS={'population_size':180,'memory_size':6,'archive_size_ratio':2.6,'minimum_population_size':4,'reduction_strategy':'linear','x_tol':0.0,'f_tol':-1.0,'bound_strategy':'random'}
def one(suite,f,budget,seed):
 a=LSHADE_M(FESLimitProblem(CECProblem(suite,f,10),max_fes=budget),population_size=180,max_iterations=10**9,seed=seed,minion_options=OPTIONS)
 a.execute();assert 0<a.fes_used<=budget
 return float(a.get_best_solution().fitness()),int(a.fes_used)
def cell(job):
 suite,f,budget,dest,identity=job;p=Path(dest)/str(budget)/f'{suite}_F{f}.json'
 if p.exists():
  r=json.loads(p.read_text());assert r['identity']==identity and len(r['errors'])==51;return str(p),'skip'
 start=time.monotonic();vals=[one(suite,f,budget,13000+i) for i in range(51)]
 r={'identity':identity,'suite':suite,'function':f,'dim':10,'budget':budget,'seeds':list(range(13000,13051)),'options':OPTIONS,'backend':'minionpy 1.9.1','errors':[x[0] for x in vals],'fes_used':[x[1] for x in vals],'seconds':time.monotonic()-start}
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r));tmp.replace(p);return str(p),'done'
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('command',choices=['smoke','run']);ap.add_argument('--out');ap.add_argument('--freeze');args=ap.parse_args()
 if args.command=='smoke':
  a=one('CEC2014',1,5000,99000);b=one('CEC2014',1,5000,99000);assert a==b;print(json.dumps({'deterministic':True,'fes_used':a[1],'budget':5000}))
 else:
  frozen=json.loads(Path(args.freeze).read_text())
  for rel,h in frozen['source_sha256'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h
  identity=hashlib.sha256(Path(args.freeze).read_bytes()).hexdigest()
  with Pool(2) as pool:
   for i,r in enumerate(pool.imap_unordered(cell,[(s,f,b,args.out,identity) for b in [5000,50000] for s,f in PROBLEMS]),1):print(i,142,*r,flush=True)
