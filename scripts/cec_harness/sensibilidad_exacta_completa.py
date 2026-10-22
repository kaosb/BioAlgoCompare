"""Sensibilidad posterior exacta en 6816 pruebas. No reemplaza la primaria.

Distribución condicional por coeficientes de producto (1+z**r), rangos
promedio duplicados, ceros excluidos. Hasta 51 signos: int64 no desborda.
La simetría de diferencias y la independencia entre corridas siguen siendo
supuestos; no se agrega una familia global ni se cambia el estimando.
Implementación independiente del generador histórico (tablas_paper_v13.py).
Lee results/cooperative/camino_alterno_v06/ y escribe en --salida:
SENSIBILIDAD_COMPLETA.json, cambios_exactos_completos.csv y g1_sensibilidad_completa.csv
Con --esperado compara con el resultado
registrado (docs/preregistro_fase_positiva/extension_21oct2026/SENSIBILIDAD_EXACTA_ESPERADA.json).

Uso: .venv/bin/python scripts/cec_harness/sensibilidad_exacta_completa.py --salida DIR [--esperado RUTA]
"""
import argparse
from pathlib import Path
import json, numpy as np
from scipy.stats import wilcoxon
ROOT=Path(__file__).resolve().parents[2]  # raíz del repositorio
BASE=ROOT
_ap=argparse.ArgumentParser(); _ap.add_argument('--salida',required=True); _ap.add_argument('--esperado'); _ap.add_argument('--pocos-pares',help='CSV p_signos de la sensibilidad parcial (opcional)')
ARGS=_ap.parse_args(); OUT=Path(ARGS.salida); OUT.mkdir(parents=True,exist_ok=True)
pairs={'det':('CTRLg','CTRLn'),'noninf':('CTRLg','C1_div'),'harm':('CTRLn_noSL','C1_div'),'sl':('CTRLg','CTRLg_noSL'),'mem':('CTRLg','CTRLg_nomem'),'ben':('BENg','BENn'),'mod':('MODg','MODn'),'c2':('C2p','C1_div'),'c3':('C3p','C1_div'),'c3c2':('C3p','C2p'),'c3abl':('C3p','ABL'),'c1div_sbs':('C1_div','SBS'),'c3p_sbs':('C3p','SBS'),'bendiv':('BENn','C1_div'),'benn_sbs':('BENn','SBS'),'beng_abl':('BENg','ABL')}
def r2(v):
 order=np.argsort(v); out=np.zeros(len(v),dtype=int); i=0
 while i<len(v):
  j=i+1
  while j<len(v) and v[order[j]]==v[order[i]]:j+=1
  out[order[i:j]]=i+1+j;i=j
 return out

def exact(d):
 if not len(d):return 1.,0.
 w=r2(abs(d)); dist=np.zeros(sum(w)+1,dtype=np.int64);dist[0]=1
 for a in w:dist[a:]+=dist[:-a].copy()
 obs=min(sum(w[d<0]),sum(w[d>0]));p=min(1.,2*int(sum(dist[:obs+1]))/(2**len(d)))
 return p,float((sum(w[d<0])-sum(w[d>0]))/sum(w))
def holm_reject(p):
 rejected=set()
 for k,i in enumerate(sorted(range(len(p)),key=lambda i:p[i])):
  if p[i]>=.05/(len(p)-k):break
  rejected.add(i)
 return rejected
report={'n_total':0,'n_small':0,'changed_small':[],'changed_full':[],'g1':[],'small_p_mismatch':[]}
csv=__import__('csv');expected=list(csv.DictReader(open(ARGS.pocos_pares))) if ARGS.pocos_pares else []
lookup={(x['par'],int(x['presupuesto']),x['contraste'],x['funcion']):float(x['p_signos']) for x in expected}
for pair in ['GWOGA','DEGA','PSOACO']:
 for budget in [5000,50000]:
  fs=sorted((BASE/f'results/cooperative/camino_alterno_v06/{pair}_{budget}').glob('CEC*_F*.json'));cells=[json.loads(f.read_text()) for f in fs]
  def arr(c,k):return np.where(np.array(c['errors'][k])<1e-8,0,c['errors'][k])
  wins=sum(np.sign(np.median(arr(c,'C0_A'))-np.median(arr(c,'C0_B'))) for c in cells);sbs='C0_A' if wins<=0 else 'C0_B'
  contrasts={}
  for name,(a,b) in pairs.items():
   if b=='SBS':b=sbs
   orig=[];small=[];full=[];effects=[];ns=[]
   for f,c in zip(fs,cells):
    x,y=arr(c,a),arr(c,b);d=x-y;d=d[d!=0];ns.append(len(d));report['n_total']+=1
    p=float(wilcoxon(x,y,zero_method='wilcox',method='auto').pvalue) if len(d) else 1.
    pe,e=exact(d);orig.append(p);full.append(pe);effects.append(e);small.append(pe if len(d)<=20 else p)
    if 0<len(d)<=20:
     report['n_small']+=1
     if lookup and pe!=lookup[(pair,budget,name,f.stem)]:report['small_p_mismatch'].append([pair,budget,name,f.stem,pe])
   so,ss,sf=map(holm_reject,[orig,small,full]);contrasts[name]=(so,ss,sf,effects)
   for key,changed in [('changed_small',so^ss),('changed_full',so^sf)]:
    for i in sorted(changed):report[key].append(dict(pair=pair,budget=budget,contrast=name,function=fs[i].stem,n=ns[i],p_auto=orig[i],p_exact=full[i],effect=effects[i],new_significant=i not in so))
  for method,idx in [('auto',0),('small',1),('full',2)]:
   det,non,harm=[contrasts[k] for k in ['det','noninf','harm']]
   w={i for i in det[idx] if det[3][i]>0};l={i for i in det[idx] if det[3][i]<0};pf={i for i in non[idx] if non[3][i]<0};h={i for i in harm[idx] if harm[3][i]<0}
   report['g1'].append(dict(pair=pair,budget=budget,method=method,better=len(w),worse=len(l),median_r=float(np.median(det[3])),portfolio_losses=len(pf),g1b=[len(h&w),len(h)],pass_budget=len(w)>len(l) and np.median(det[3])>=.3 and len(pf)<=7))
if ARGS.esperado:
 expected_report=json.loads(Path(ARGS.esperado).read_text())
 assert report == expected_report, 'Discrepancia con el cálculo registrado'
 print('coincide con', ARGS.esperado)
assert report['n_total']==6816 and report['n_small']==447
assert len(report['changed_small'])==13 and len(report['changed_full'])==56
assert all(x['new_significant'] for x in report['changed_full'])
for pair in ['GWOGA','DEGA','PSOACO']:
 for budget in [5000,50000]:
  subset=[x for x in report['g1'] if x['pair']==pair and x['budget']==budget]
  assert len({x['pass_budget'] for x in subset})==1
  assert len({x['median_r'] for x in subset})==1
with (OUT/'cambios_exactos_completos.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=report['changed_full'][0]);w.writeheader();w.writerows(report['changed_full'])
g1rows=[]
for x in report['g1']:
 row={k:v for k,v in x.items() if k!='g1b'}
 row.update(g1b_numerador=x['g1b'][0],g1b_denominador=x['g1b'][1],g1b_porcentaje=100*x['g1b'][0]/x['g1b'][1]);g1rows.append(row)
with (OUT/'g1_sensibilidad_completa.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=g1rows[0]);w.writeheader();w.writerows(g1rows)
(OUT/'SENSIBILIDAD_COMPLETA.json').write_text(json.dumps(report,indent=2))
print(json.dumps({**{k:v for k,v in report.items() if k not in ['changed_small','changed_full','g1']},'changes_small':len(report['changed_small']),'changes_full':len(report['changed_full']),'g1':report['g1']},indent=2))
