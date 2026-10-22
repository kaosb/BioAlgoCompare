"""Fixed additional contrasts; refuses incomplete campaigns."""
from pathlib import Path
import argparse,json,itertools
import numpy as np
from scipy.stats import rankdata
ROOT=Path(__file__).resolve().parents[2]

def exact(a,b):
 d=np.where(np.asarray(a)<1e-8,0.,a)-np.where(np.asarray(b)<1e-8,0.,b);d=d[d!=0]
 if not len(d):return 1.,0.
 weights=np.rint(2*rankdata(abs(d))).astype(int)
 counts=np.zeros(int(weights.sum())+1,dtype=np.int64);counts[0]=1;used=0
 for w in weights:
  prev=counts[:used+1].copy();counts[w:w+used+1]+=prev;used+=int(w)
 observed=min(int(weights[d>0].sum()),int(weights[d<0].sum()))
 p=min(1.,2*int(counts[:observed+1].sum())/2**len(d))
 r=float((weights[d<0].sum()-weights[d>0].sum())/weights.sum())
 return p,r

def holm(ps):
 order=np.argsort(ps);out=np.zeros(len(ps));v=0.
 for rank,i in enumerate(order):v=max(v,(len(ps)-rank)*ps[i]);out[i]=min(v,1.)
 return out

def selftest():
 for d in [np.array([1.,-2.,3.]),np.array([1.,-1.,2.,0.]),np.array([0.,0.]),np.array([1.,1.,1.])]:
  a=d+10;b=np.full(len(d),10.);p,r=exact(a,b);non=d[d!=0]
  if not len(non):assert (p,r)==(1.,0.);continue
  w=rankdata(abs(non));obs=min(w[non>0].sum(),w[non<0].sum());hit=0
  for bits in itertools.product([0,1],repeat=len(w)):
   z=sum(w*np.array(bits));hit+=min(z,w.sum()-z)<=obs
  assert abs(p-hit/2**len(w))<1e-14
 assert exact([1,1,1],[2,2,2])[1]==1.

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--controls',type=Path);ap.add_argument('--lshade',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--selftest',action='store_true');args=ap.parse_args();selftest()
 if args.selftest:print('Exact distribution and sign checks passed');raise SystemExit
 problems=[(s,f) for s,n in [('CEC2014',30),('CEC2017',30),('CEC2022',12)] for f in range(1,n+1) if not(s=='CEC2017' and f==2)]
 contrasts=[('C1_shared','C1_div'),('CTRLg','C1_shared'),('C3p','C1_shared'),('REPLAY','PERMUTED'),('C3p','LSHADE'),('C1_shared','LSHADE')]
 report={'method':'conditional exact Wilcoxon; Holm per 71 functions per contrast/configuration','new_confirmatory_claim':False,'configurations':{}}
 for pair in ['GWOGA','DEGA','PSOACO']:
  for budget in [5000,50000]:
   rows=[]
   for suite,f in problems:
    cell=json.loads((args.controls/pair/str(budget)/f'{suite}_F{f}.json').read_text());external=json.loads((args.lshade/str(budget)/f'{suite}_F{f}.json').read_text());old=json.loads((ROOT/'results/cooperative/camino_alterno_v06'/f'{pair}_{budget}'/f'{suite}_F{f}.json').read_text())
    assert len(cell['seeds'])==51 and cell['seeds']==external['seeds']==list(range(13000,13051))
    data={**old['errors'],**cell['errors'],'LSHADE':external['errors']}
    assert data['C3p']==old['errors']['C3p']==data['REPLAY']
    rows.append((suite,f,data,cell,external))
   cfg={'contrasts':{},'changed_runs':sum(sum(n>0 for n in x[3]['changed_windows']) for x in rows),'total_runs':71*51,'lshade_fes_range':[min(min(x[4]['fes_used']) for x in rows),max(max(x[4]['fes_used']) for x in rows)]}
   for a,b in contrasts:
    stats=[exact(x[2][a],x[2][b]) for x in rows];adj=holm([v[0] for v in stats]);effects=[v[1] for v in stats];counts=[sum(p<.05 and r>0 for p,r in zip(adj,effects)),sum(p>=.05 for p in adj),sum(p<.05 and r<0 for p,r in zip(adj,effects))]
    mags=[]
    for x in rows:
     ma,mb=[float(np.median(np.where(np.asarray(x[2][k])<1e-8,0.,x[2][k]))) for k in [a,b]];mags.append((ma-mb)/max(ma,mb,1e-8))
    cfg['contrasts'][a+'/'+b]={'better_equal_worse':counts,'median_rank_biserial':float(np.median(effects)),'median_normalized_difference':float(np.median(mags)),'per_function':[{'suite':x[0],'function':x[1],'p_exact':v[0],'p_holm':float(p),'r':v[1],'d':d} for x,v,p,d in zip(rows,stats,adj,mags)]}
   report['configurations'][f'{pair}_{budget}']=cfg
 args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2,default=lambda value: value.item())+'\n');print(args.out)
