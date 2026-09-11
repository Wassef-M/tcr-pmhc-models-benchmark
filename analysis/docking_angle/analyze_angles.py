#!/usr/bin/env python3
import csv, statistics as st, collections, sys
TSV = sys.argv[1] if len(sys.argv)>1 else "results/docking_angles_classI.tsv"
OUTERR = "results/angle_errors_classI.tsv"
def canon(c): return "msa+tmpl" if "template" in c else "msa"

rows  = list(csv.DictReader(open(TSV), delimiter='\t'))
nat   = {r['pdb']:(float(r['docking_angle']),float(r['incident_angle']))
         for r in rows if r['model']=='true' and r['status']=='OK'}
preds = [r for r in rows if r['model']!='true']

with open(OUTERR,'w',newline='') as fh:
    w=csv.writer(fh,delimiter='\t')
    w.writerow(['pdb','model','condition','rank','status',
                'dock_pred','dock_native','dock_err','inc_pred','inc_native','inc_err'])
    for r in preds:
        nd,ni = nat.get(r['pdb'],('',''))
        if r['status']=='OK' and r['pdb'] in nat:
            dp,ip=float(r['docking_angle']),float(r['incident_angle'])
            w.writerow([r['pdb'],r['model'],canon(r['condition']),r['rank'],'OK',
                        f'{dp:.2f}',f'{nd:.2f}',f'{abs(dp-nd):.2f}',
                        f'{ip:.2f}',f'{ni:.2f}',f'{abs(ip-ni):.2f}'])
        else:
            w.writerow([r['pdb'],r['model'],canon(r['condition']),r['rank'],r['status'].split(':')[0],
                        '','','','','',''])
print(f"wrote {OUTERR}   (native reference targets: {len(nat)})")

def agg(view):
    g=collections.defaultdict(lambda:{'n':0,'ok':0,'d':[],'i':[]})
    for r in view:
        k=(r['model'],canon(r['condition'])); g[k]['n']+=1
        if r['status']=='OK' and r['pdb'] in nat:
            g[k]['ok']+=1
            g[k]['d'].append(abs(float(r['docking_angle'])-nat[r['pdb']][0]))
            g[k]['i'].append(abs(float(r['incident_angle'])-nat[r['pdb']][1]))
    return g

def show(title,g,frac):
    print(f"\n### {title}")
    h=f"{'model':<13}{'cond':<9}"+(f"{'n':>4}{'comp%':>7}" if frac else "")+\
      f"{'N':>5}{'dMAE':>7}{'dMed':>7}{'d<10':>6}{'d<15':>6}{'iMAE':>7}{'iMed':>7}{'i<10':>6}"
    print(h); print('-'*len(h))
    for k in sorted(g):
        v=g[k]; line=f"{k[0]:<13}{k[1]:<9}"
        if frac: line+=f"{v['n']:>4}{(100*v['ok']/v['n'] if v['n'] else 0):>7.0f}"
        N=len(v['d'])
        if N:
            line+=f"{N:>5}{st.mean(v['d']):>7.1f}{st.median(v['d']):>7.1f}"\
                  f"{100*sum(x<10 for x in v['d'])/N:>6.0f}{100*sum(x<15 for x in v['d'])/N:>6.0f}"\
                  f"{st.mean(v['i']):>7.1f}{st.median(v['i']):>7.1f}{100*sum(x<10 for x in v['i'])/N:>6.0f}"
        else: line+=f"{0:>5}"+"      -"*6
        print(line)

show("ranked_0 (top prediction) vs native", agg([r for r in preds if r['rank']=='ranked_0']), True)

best=collections.defaultdict(list)
for r in preds:
    if r['status']=='OK' and r['pdb'] in nat:
        best[(r['pdb'],r['model'],canon(r['condition']))].append(
            (abs(float(r['docking_angle'])-nat[r['pdb']][0]), r))
show("best-of-5 (closest rank per target) vs native",
     agg([min(v,key=lambda t:t[0])[1] for v in best.values()]), False)
