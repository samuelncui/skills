#!/usr/bin/env python3
"""Small native graph-component regression matrix. No private source data."""
import argparse,os,re
from pathlib import Path
import pymupdf as fitz
from matrix_support import ROOT,add_matrix_arguments,initialize_output,execute_matrix,run_command

def cases():
 return [
 ('english','',None),
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
 ('paired',r'\def\GraphFixturePaired{}',None),
 ('sparse-style',r'\AtBeginDocument{\renewcommand\ParallelSemanticMarkerStyle{\normalfont\bfseries}}',None),
 ('invalid-legend',r'\AtBeginDocument{\StudyGraphLegendItem{unknown}{Invalid}}','Unknown graph legend function'),
 ('zero-choice',r'\AtBeginDocument{\StudyGraphChoice{0}{Invalid}{finish}}','Graph ordinal must be a positive integer'),
 ('unknown-target',r'\AtBeginDocument{\StudyGraphReference{not-declared}}','Unknown graph key'),
 ('invalid-call',r'\AtBeginDocument{\StudyGraphCall{choose-task}{Always}{A value}{compute-value}{2}}','Graph call target must be a procedure'),
 ]
def run_case(case,work):
 name,prefix,error=case;p=work/name;p.mkdir(exist_ok=True)
 source=prefix+'\n'+r'\input{'+str(ROOT/'tests/fixtures/study-graph-components.tex')+'}\n'
 (p/'main.tex').write_text(source)
 env={**os.environ,'TEXINPUTS':str(ROOT/'skills/study-notes/assets')+'//:'+str(ROOT/'skills/bilingual-pdf/assets')+'//:'+os.environ.get('TEXINPUTS','')+':'}
 for turn in [1,2]:
  proc=run_command(['xelatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=p,env=env,timeout=40)
  log=proc.stdout+proc.stderr;(p/f'compile-{turn}.log').write_text(log)
  if proc.returncode:return {'case':name,'passed':bool(error and error in log),'expected_error':error,'errors':[] if error and error in log else ['Unexpected compile failure']}
 if error:return {'case':name,'passed':False,'errors':['Expected rejection did not occur']}
 errors=[];d=fitz.open(p/'main.pdf');text='\n'.join(x.get_text() for x in d);text=' '.join(re.sub(r'(?<=\w)-\n(?=\w)', '', text).split());aux=(p/'main.aux').read_text()
 if re.search(r'Overfull \\[hv]box|Missing character:|undefined references',log):errors.append('Layout, glyph or reference diagnostic')
 headings = [(1,'Choose the task'),(2,'Obtain the missing value'),(3,'Compute the value'),(4,'Check the result'),(5,'Report the result')] if name in ('reader-profile','intro-rules','intro-rules-paired') else [(1,'Question'),(2,'Warning'),(3,'Action'),(4,'Check'),(5,'Result')]
 for n,label in headings:
  if not re.search(str(n)+r'\s*·\s*'+label,text):errors.append('Missing numbered heading '+str(n))
 values=['Choose from the stated conditions.','Perform the stated solution steps.','Resolve missing information before proceeding.','A.','B.','C.','Then resume','Carry back','Exit when']
 values += ['1:','2:','first match','Unclear or otherwise','An earlier choice is undecidable.','Report only an invariant result.'] if name in ('reader-profile','intro-rules','intro-rules-paired') else ['Action 1','Action 2','first true condition']
 if name.startswith('intro-rules'):
  values.remove('first match')
  values += ['Intro priority rule:', 'A required value is unknown.', 'Both values are given.', 'An earlier choice is undecidable.', 'Stop if no new fact can be obtained.']
  if 'first-match' in aux:errors.append('Automatic rule paragraph remains in intro mode')
  if 'Read A, B, C in order.' in text:errors.append('Explicit or automatic first-match output remains')
 else:
  if r'\newlabel{graph:choose-task:first-match}' not in aux:errors.append('Default node rule paragraph missing')
 for value in values:
  if value not in text:errors.append('Missing semantic text '+value)
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
