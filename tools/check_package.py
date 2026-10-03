#!/usr/bin/env python3
"""Check public skill package structure, local links and obvious privacy leaks."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[];skills=[]
for skill in sorted((ROOT/'skills').iterdir()):
 if not skill.is_dir():continue
 main=skill/'SKILL.md'
 if not main.exists():errors.append(str(skill.relative_to(ROOT))+': missing SKILL.md');continue
 text=main.read_text();parts=text.split('---',2)
 if len(parts)!=3:errors.append(skill.name+': invalid frontmatter');continue
 fields={k:v.strip() for k,v in re.findall(r'^([a-z-]+):\s*(.+)$',parts[1],re.M)}
 if fields.get('name')!=skill.name or not fields.get('description'):errors.append(skill.name+': name/description invalid')
 if len(text.splitlines())>500:errors.append(skill.name+': entrypoint too long')
 for p in skill.rglob('*'):
  if p.is_symlink():errors.append(str(p.relative_to(ROOT))+': symlink not self-contained')
  if not p.is_file() or '__pycache__' in p.parts:continue
  if p.suffix not in {'.md','.py','.sty','.tex','.txt','.json','.yaml'} and p.name!='LICENSE':continue
  body=p.read_text()
  for pattern in [r'/workspace/',r'/Users/',r'ghp_[A-Za-z0-9]{20,}',r'sk-proj-[A-Za-z0-9_-]{20,}',r'github_pat_[A-Za-z0-9_]+',r'-----BEGIN .*PRIVATE KEY-----']:
   if re.search(pattern,body):errors.append(str(p.relative_to(ROOT))+': prohibited local/private data')
  if p.suffix=='.md':
   for link in re.findall(r'\]\(([^)]+)\)',body):
    if '://' in link or link.startswith('#'):continue
    target=(p.parent/link.split('#')[0]).resolve()
    if not target.is_relative_to(skill.resolve()) or not target.exists():errors.append(str(p.relative_to(ROOT))+': missing/external local link '+link)
 skills.append(skill.name)
print(json.dumps({'ok':not errors,'skills':skills,'errors':errors},indent=2));sys.exit(bool(errors))
