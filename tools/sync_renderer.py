#!/usr/bin/env python3
"""Stage identical runtime resources into independently installable skills."""
from pathlib import Path
import argparse,hashlib,json,shutil,sys
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
source=r/'skills/bilingual-pdf';dest=r/'skills/course-guide-quick-reference'
paths=['requirements.txt','scripts/bilingual_pdf.py','assets/paralleltext.sty','assets/bound-profile.tex','assets/reading-profile.tex','references/configuration.md','references/latex.md','references/languages.md','references/input.md']
errors=[]
for starter in (source/'assets/starter/paralleltext.sty',dest/'assets/learning-starter/paralleltext.sty'):
 if args.check:
  if not starter.exists() or starter.read_bytes()!=(source/'assets/paralleltext.sty').read_bytes():errors.append(str(starter.relative_to(r)))
 else:shutil.copyfile(source/'assets/paralleltext.sty',starter)
projects=[source/'assets/starter',dest/'assets/learning-starter']+sorted((r/'skills/bilingual-pdf/examples').glob('*'))+[r/'skills/course-guide-quick-reference/examples']
for project in projects:
 if not project.is_dir():continue
 for target,owner in [('paralleltext.sty',source/'assets/paralleltext.sty')]:
  copy=project/target
  if args.check:
   if not copy.exists() or copy.read_bytes()!=owner.read_bytes():errors.append(str(copy.relative_to(r)))
  else:shutil.copyfile(owner,copy)
for name in paths:
 s=source/name;d=dest/name
 if args.check:
  if not d.exists() or s.read_bytes()!=d.read_bytes():errors.append(name)
 else:d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,d)
print(json.dumps({'ok':not errors,'stale':errors,'sha256':{n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in paths}}))
sys.exit(bool(errors))
