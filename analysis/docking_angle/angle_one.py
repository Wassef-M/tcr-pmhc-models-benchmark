#!/usr/bin/env python3
import sys, os, subprocess, argparse, tempfile, shutil, warnings, re
from Bio import BiopythonWarning, PDB
warnings.simplefilter('ignore', BiopythonWarning)

AA3 = {'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
       'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
       'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V'}
ALPHA_LIKE = {'A','D'}   # alpha or delta  -> tool chain D
BETA_LIKE  = {'B','G'}   # beta  or gamma  -> tool chain E

def seq_of(ch):  return ''.join(AA3.get(r.resname,'X') for r in ch if r.id[0]==' ')
def n_res(ch):   return sum(1 for r in ch if r.id[0]==' ')

def anarci_type(seq):
    if len(seq) < 50:
        return None
    try:
        r = subprocess.run(['ANARCI','-i',seq,'--scheme','a','-r','tr'],
                           capture_output=True, text=True, timeout=180)
    except Exception:
        return None
    for line in r.stdout.splitlines():
        if line.startswith('#|'):
            p = line.split('|')
            if len(p) > 2 and p[2].strip() in ('A','B','G','D'):
                return p[2].strip()
    return None

def classify_classI(model):
    alpha = beta = None
    others = []
    for ch in model:
        t = anarci_type(seq_of(ch))
        if   t in ALPHA_LIKE: alpha = ch.id
        elif t in BETA_LIKE:  beta  = ch.id
        else:                 others.append(ch.id)
    if alpha is None or beta is None:
        raise RuntimeError(f"TCR a/b not both found (alpha={alpha}, beta={beta})")
    others = sorted(others, key=lambda c: n_res(model[c]))
    if len(others) < 2:
        raise RuntimeError(f"need >=2 non-TCR chains, got {others}")
    if len(others) > 2:
        raise RuntimeError(f"got {len(others)} non-TCR chains (class II?); needs class-II handling")
    return {'mhc': others[-1], 'pep': others[0], 'alpha': alpha, 'beta': beta}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i','--input', required=True)
    ap.add_argument('--repo', default=os.getcwd())
    ap.add_argument('--mhc_type', default='0')
    ap.add_argument('-o','--output', default=None)
    ap.add_argument('--keep', action='store_true')
    a = ap.parse_args()
    pid = os.path.basename(a.input).split('_')[0]
    work = tempfile.mkdtemp(prefix='ang_')
    try:
        struct = PDB.PDBParser(QUIET=True).get_structure('x', a.input)
        model  = next(struct.get_models())
        roles  = classify_classI(model)
        target = {roles['mhc']:'A', roles['pep']:'C', roles['alpha']:'D', roles['beta']:'E'}
        for ch in list(model):
            if ch.id not in target: model.detach_child(ch.id)
        t2f = {}
        for ch in list(model):
            f='tmp_'+target[ch.id]; t2f[f]=target[ch.id]; ch.id=f
        for ch in list(model): ch.id=t2f[ch.id]
        norm = os.path.join(work,'norm.pdb')
        io=PDB.PDBIO(); io.set_structure(struct); io.save(norm)
        renum = os.path.join(work,'renum.pdb')
        subprocess.run(['python', os.path.join(a.repo,'scripts','renumber_tcr.py'),
                        '-i',norm,'-o',renum,'--mhc_a','A','--peptide','C',
                        '--tcr_a','D','--tcr_b','E'],
                       capture_output=True, text=True, cwd=work)
        if not os.path.exists(renum):
            raise RuntimeError("renumber_tcr.py produced no output")
        tp = subprocess.run([os.path.join(a.repo,'tcr_docking_angle'), renum, a.mhc_type],
                            capture_output=True, text=True, cwd=work)
        out = tp.stdout + tp.stderr
        m = re.search(r'ANGLES:\s+(\S+)\s+(\S+)\s+(\S+)', out)
        warn = 1 if 'suspicious' in out else 0
        if not m:
            raise RuntimeError(f"no ANGLES (rc={tp.returncode}): {out[-150:].strip()}")
        print(f"RESULT\t{pid}\t{roles['mhc']}\t{roles['pep']}\t{roles['alpha']}"
              f"\t{roles['beta']}\t{m.group(1)}\t{m.group(2)}\t{m.group(3)}\t{warn}\tOK")
        if a.output: shutil.copy(renum, a.output)
    except Exception as e:
        print(f"RESULT\t{pid}\t-\t-\t-\t-\t-\t-\t-\t-\tFAIL:{str(e)[:160]}")
    finally:
        if not a.keep: shutil.rmtree(work, ignore_errors=True)

if __name__ == '__main__':
    main()
