#!/usr/bin/env python3
"""Small native graph-component regression matrix. No private source data."""
import argparse,os,re,shutil
from pathlib import Path
import pymupdf as fitz
from matrix_support import ROOT,add_matrix_arguments,initialize_output,execute_matrix,run_command

def cases():
 return [
 ('english','',None),
 ('hierarchy',r'\def\GraphFixtureHierarchy{}\def\GraphFixtureReader{}',None),
 ('hierarchy-paired',r'\def\GraphFixtureHierarchy{}\def\GraphFixtureReader{}\def\GraphFixturePaired{}\def\GraphFixtureChinese{}',None),
 ('hierarchy-only',r'\def\GraphFixtureHierarchy{}',None),
 ('hierarchy-sparse',r'\def\GraphFixtureHierarchy{}\def\GraphFixtureReader{}\def\GraphFixtureRulePlacement{\ParallelSetup{semantic-badge-padding=.18em,semantic-badge-rule=.5pt,semantic-badge-gap=.5em,semantic-field-indent=1.5em,semantic-bullet-indent=1.2em}}',None),
 ('late-hierarchy',r'\def\GraphFixtureBody{\StudyGraphHierarchyProfile}','Can be used only in preamble'),
 ('invalid-badge-rule',r'\def\GraphFixtureRulePlacement{\ParallelSetup{semantic-badge-rule=0pt}}','Semantic badge rule must be positive'),
 ('invalid-field-indent',r'\def\GraphFixtureRulePlacement{\ParallelSetup{semantic-field-indent=-1pt}}','Semantic field indent must not be negative'),
 ('native-auto',r'\def\GraphFixtureAuto{}\def\GraphFixtureReader{}\def\GraphFixtureRulePlacement{\ParallelSetup{header-left=\ParallelFirstEntry,header-right=\ParallelLastEntry}}',None),
 ('reader-profile',r'\def\GraphFixtureReader{}',None),
 ('intro-rules',r'\def\GraphFixtureIntro{}\def\GraphFixtureReader{}\def\GraphFixtureRulePlacement{\StudyGraphRulePlacement{intro}}',None),
 ('intro-rules-paired',r'\def\GraphFixtureIntro{}\def\GraphFixtureReader{}\def\GraphFixturePaired{}\def\GraphFixtureRulePlacement{\StudyGraphRulePlacement{intro}}',None),
 ('node-rules',r'\def\GraphFixtureRulePlacement{\StudyGraphRulePlacement{intro}\StudyGraphRulePlacement{node}}',None),
 ('invalid-placement',r'\def\GraphFixtureRulePlacement{\StudyGraphRulePlacement{other}}','Unknown graph rule placement'),
 ('late-placement',r'\def\GraphFixtureBody{\StudyGraphRulePlacement{intro}}','Can be used only in preamble'),
 ('local-terminal',r'\def\GraphFixtureTerminal{}\def\GraphFixtureRulePlacement{\StudyGraphTerminalMode{local}}',None),
 ('local-terminal-paired',r'\def\GraphFixtureTerminal{}\def\GraphFixturePaired{}\def\GraphFixtureRulePlacement{\StudyGraphTerminalMode{local}}',None),
 ('link-terminal',r'\def\GraphFixtureTerminal{}\def\GraphFixtureRulePlacement{\StudyGraphTerminalMode{local}\StudyGraphTerminalMode{link}}',None),
 ('invalid-terminal-mode',r'\def\GraphFixtureRulePlacement{\StudyGraphTerminalMode{other}}','Unknown graph terminal mode'),
 ('late-terminal-mode',r'\def\GraphFixtureBody{\StudyGraphTerminalMode{local}}','Can be used only in preamble'),
 ('operation-scope',r'\def\GraphFixtureOperation{\StudyGraphOperationChoice{1}{Apply the stated local scope.}{compute-value}{}}',None),
 ('operation-step',r'\def\GraphFixtureOperation{\StudyGraphOperationChoice{1}{Apply the stated local scope.}{compute-value}{2}}',None),
 ('operation-invalid-step',r'\def\GraphFixtureOperation{\StudyGraphOperationChoice{1}{Invalid}{compute-value}{0}}','Graph ordinal must be a positive integer'),
 ('operation-unknown-owner',r'\def\GraphFixtureOperation{\StudyGraphOperationChoice{1}{Invalid}{missing}{}}','Unknown graph key'),
 ('paired',r'\def\GraphFixturePaired{}',None),
 ('sparse-style',r'\AtBeginDocument{\renewcommand\ParallelSemanticMarkerStyle{\normalfont\bfseries}}',None),
 ('invalid-legend',r'\AtBeginDocument{\StudyGraphLegendItem{unknown}{Invalid}}','Unknown graph legend function'),
 ('zero-choice',r'\AtBeginDocument{\StudyGraphChoice{0}{Invalid}{finish}}','Graph ordinal must be a positive integer'),
 ('unknown-target',r'\AtBeginDocument{\StudyGraphReference{not-declared}}','Unknown graph key'),
 ('invalid-call',r'\AtBeginDocument{\StudyGraphCall{choose-task}{Always}{A value}{compute-value}{2}}','Graph call target must be a procedure'),
 ]
def run_case(case,work):
 name,prefix,error=case;p=work/name;p.mkdir(exist_ok=True)
 hierarchy=name.startswith('hierarchy')
 reader=name in ('native-auto','reader-profile','intro-rules','intro-rules-paired') or (hierarchy and name!='hierarchy-only')
 source=prefix+'\n'+(ROOT/'tests/fixtures/study-graph-components.tex').read_text()
 if name=='native-auto':
  source=re.sub(r'\\StudyDeclareGraphNode\{([^}]+)\}\{[1-5]\}',r'\\StudyDeclareGraphNodeAuto{\1}',source)
 (p/'main.tex').write_text(source)
 env={**os.environ,'TEXINPUTS':str(ROOT/'skills/study-notes/assets')+'//:'+str(ROOT/'skills/bilingual-pdf/assets')+'//:'+os.environ.get('TEXINPUTS','')+':'}
 if hierarchy or name=='native-auto':
  # The installed skills deliberately have unrelated, separately discovered paths.
  study=p/'installed-learning';render=p/'dependencies'/'rendering'
  shutil.copytree(ROOT/'skills/study-notes/assets',study,dirs_exist_ok=True)
  shutil.copytree(ROOT/'skills/bilingual-pdf/assets',render,dirs_exist_ok=True)
  env['TEXINPUTS']=str(study)+'//:'+str(render)+'//:'

 for turn in [1,2]:
  proc=run_command(['xelatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=p,env=env,timeout=40)
  log=proc.stdout+proc.stderr;(p/f'compile-{turn}.log').write_text(log)
  if proc.returncode:return {'case':name,'passed':bool(error and error in log),'expected_error':error,'errors':[] if error and error in log else ['Unexpected compile failure']}
 if error:return {'case':name,'passed':False,'errors':['Expected rejection did not occur']}
 errors=[];d=fitz.open(p/'main.pdf');text='\n'.join(x.get_text() for x in d);text=' '.join(re.sub(r'(?<=\w)-\n(?=\w)', '', text).split());aux=(p/'main.aux').read_text()
 if re.search(r'Overfull \\[hv]box|Missing character:|undefined references',log):errors.append('Layout, glyph or reference diagnostic')
 headings = [(1,'Choose the task'),(2,'Obtain the missing value'),(3,'Compute the value'),(4,'Check the result'),(5,'Report the result')] if reader or hierarchy else [(1,'Question'),(2,'Warning'),(3,'Action'),(4,'Check'),(5,'Result')]
 for n,label in headings:
  if not re.search(('N' if reader else '')+str(n)+(r'\s+' if hierarchy else r'\s*·\s*')+label,text):errors.append('Missing numbered heading '+str(n))
 values=['Choose from the stated conditions.','Perform the stated solution steps.','Resolve missing information before proceeding.','A.','B.','C.','Then resume','Carry back','Exit when']
 values += ['N1:','N2:','first match','Unclear or otherwise','An earlier choice is undecidable.','Report only an invariant result.'] if reader else ['Action 1','Action 2','first true condition']

 if hierarchy:
  values=[x for x in values if x not in ('N1:','N2:','Action 1','Action 2')]
  values+=['Step 1:', 'Step 2:', 'Warning:', 'Limits:']
  if name=='hierarchy-paired' and not re.search(r'步\s*骤\s*1',text):errors.append('Localized step label missing')
  if not all(re.search(r'[•・]\s*'+label+':',text) for label in ('Warning','Limits')):errors.append('Caution field bullet missing')
  if re.search(r'\b[1-5]\s*·\s*(Question|Solution|Action|Warning|Check|Result)',text):errors.append('Separate category heading remains')
  # A neutral named step must keep its body font size and a true inset.
  page=d[0]
  body=page.search_for('Record the two values.')
  steps=page.search_for('Step 1:')
  nodes=page.search_for('Compute the value')
  if not body or not steps or not nodes:errors.append('Hierarchy geometry probe missing')
  elif min(x.x0 for x in steps)<=min(x.x0 for x in page.search_for('Remember:') or page.search_for('Completion check:')):errors.append('Step field is not indented')
  spans=[s for p0 in d for b in p0.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans']]
  probe=page.search_for('Record the two values.')
  probe_spans=[s for s in spans if any(fitz.Rect(s['bbox']).intersects(rect) for rect in probe)]
  if not probe_spans or not all(abs(s['size']-9)<.1 for s in probe_spans):errors.append('Original 9pt body size changed')
  # Outlined number badges are drawn in both headings and inline references.
  outlines=[drawing for p0 in d for drawing in p0.get_drawings()
            if drawing.get('color') and drawing['rect'].width<35 and drawing['rect'].height<22]
  if len(outlines)<10:errors.append('Node and reference badge outlines missing')
  for target in ['graph:compute-value:step:2','graph:get-value:completion-check']:
   match=re.search(r'\\newlabel\{'+re.escape(target)+r'\}\{\{.*?\}\{.*?\}\{.*?\}\{([^}]+)\}',aux)
   if not match or match[1] not in d.resolve_names():errors.append('Actual PDF destination missing '+target)
  if not any(link.get('kind') in (fitz.LINK_GOTO,fitz.LINK_NAMED) and link.get('page',-1)>=0 for p0 in d for link in p0.get_links()):errors.append('Clickable graph links missing')
 if name.startswith('intro-rules'):
  values.remove('first match')
  values += ['Intro priority rule:', 'A required value is unknown.', 'Both values are given.', 'An earlier choice is undecidable.', 'Stop if no new fact can be obtained.']
  if 'first-match' in aux:errors.append('Automatic rule paragraph remains in intro mode')
  if 'Read A, B, C in order.' in text:errors.append('Explicit or automatic first-match output remains')
 else:
  if r'\newlabel{graph:choose-task:first-match}' not in aux:errors.append('Default node rule paragraph missing')
 for value in values:
  if value not in text:errors.append('Missing semantic text '+value)
 if name in ('operation-scope','operation-step'):
  segment=text.split('A. Apply the stated local scope.',1)[-1].split('Use: Execution scope',1)[0]
  if 'A. Apply the stated local scope.' not in text:errors.append('Local operation condition missing')
  if name=='operation-scope' and segment.strip():errors.append('Unspecified operation gained a destination')
  if name=='operation-step' and 'Action 2 (p. 1)' not in segment:errors.append('Explicit operation step link changed')
 if 'terminal' in name:
  values=['When called:', 'stated resume node', 'Action 2 (p. 1)']
  if any(value not in text for value in values):errors.append('Call-return instruction or real resume reference changed')
  if name.startswith('local-terminal'):
   if re.search(r'(Finish|Done)\s*\(p\.',text):errors.append('Local terminal still has a page reference')
   if 'Result: Finish' not in text:errors.append('Local terminal completion missing')
   if name.endswith('paired') and 'Result: Done' not in text:errors.append('Localized terminal completion missing')
  elif 'Finish (p. 1)' not in text:errors.append('Default linked terminal changed')
 for label in ['graph:compute-value:step:2','graph:get-value:completion-check','graph:finish']:
  if r'\newlabel{'+label+'}' not in aux:errors.append('Missing stable anchor '+label)
 if reader:
  if any(key in text for key in ('choose-task','get-value','compute-value','check-value','report-value')):errors.append('Internal graph key leaked into reader text')
 if name=='paired' and not all(x in text for x in ['Choose the task','Select the task','Compute the value','Calculate the value']):errors.append('Selected-language registry title not used')
 if name=='english' and 'Select the task' in text:errors.append('Right title leaked into left output')
 colors={s['color'] for p0 in d for b in p0.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']}
 if not {0x0b4f8a,0x006b5b,0x8a5a00}<=colors:errors.append('Functional palette missing')
 for i,page in enumerate(d):page.get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(p/f'page-{i+1}.png')
 return {'case':name,'passed':not errors,'errors':errors,'pages':len(d)}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);add_matrix_arguments(p);a=p.parse_args()
 work=initialize_output(a.output,a.resume)
 return execute_matrix(cases(),lambda c:run_case(c,work),work,a,'study-graph-components')
if __name__=='__main__':raise SystemExit(main())
