import sys, warnings
from Bio import BiopythonWarning
from Bio.PDB import PDBParser
warnings.simplefilter('ignore', BiopythonWarning)

AA3 = {'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
       'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
       'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V'}
parser = PDBParser(QUIET=True)
for path in sys.argv[1:]:
    print(f"\n=== {path} ===")
    try:
        model = next(parser.get_structure('x', path).get_models())
    except Exception as e:
        print("  parse error:", e); continue
    for ch in model:
        aa = [r for r in ch if r.id[0] == ' ' and r.resname in AA3]
        het = sum(1 for r in ch if r.id[0] != ' ')
        seq = ''.join(AA3[r.resname] for r in aa)
        first = aa[0].id[1] if aa else None
        last  = aa[-1].id[1] if aa else None
        print(f"  chain {ch.id!r:>4}: {len(aa):>4} aa  resnum {first}..{last}  HET={het}")
        print(f"        {seq[:65]}{'...' if len(seq)>65 else ''}")
