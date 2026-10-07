"""Opt-in real-browser layout regression; default fast discovery skips this profile."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_bilingual_html import RENDERER, minimal, pair


DRIVER = r"""
const fs = require('fs');
const cfg = JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));
const {chromium} = require(cfg.module);
(async () => {
  const browser = await chromium.launch({executablePath:cfg.executable, headless:true,
    chromiumSandbox:!cfg.allowNoSandbox, ignoreDefaultArgs:['--hide-scrollbars'], timeout:20000});
  const results = [];
  try {
    for (const item of cfg.inputs) for (const width of [1366,390]) {
      const context = await browser.newContext({viewport:{width,height:844}});
      await context.route('**/*', route => /^(file|data|about):/.test(route.request().url()) ? route.continue() : route.abort());
      const page = await context.newPage();
      await page.goto('file://' + item.path);
      await page.evaluate(() => document.fonts.ready);
      const result = await page.evaluate(() => {
        const wrapper = document.querySelector('.table-scroll');
        const lineCount = id => [...document.querySelectorAll('[data-pair-id="'+id+'"] .text')].map(span => {
          const range = document.createRange(); range.selectNodeContents(span);
          return new Set([...range.getClientRects()].map(r=>Math.round(r.top))).size;
        });
        const pair = document.querySelector('[data-pair-id="h-time"]');
        const source = pair.querySelector('.source').getBoundingClientRect();
        const target = pair.querySelector('.target').getBoundingClientRect();
        return {width:innerWidth, documentWidth:document.documentElement.scrollWidth,
          timeLines:lineCount('r1-time'), headingLines:lineCount('h-time'),
          source:{x:source.x,y:source.y,bottom:source.bottom}, target:{x:target.x,y:target.y},
          scrollWidth:wrapper.scrollWidth,clientWidth:wrapper.clientWidth,
          tabindex:wrapper.getAttribute('tabindex'),role:wrapper.getAttribute('role'),
          labelled:!!wrapper.getAttribute('aria-labelledby') && wrapper.getAttribute('aria-labelledby').split(/\s+/).every(id=>!!document.getElementById(id))};
      });
      await page.locator('.table-scroll').focus();
      result.focused = await page.evaluate(()=>document.activeElement===document.querySelector('.table-scroll'));
      await page.keyboard.press('ArrowRight'); await page.waitForTimeout(80);
      result.scrollAfterKey = await page.locator('.table-scroll').evaluate(e=>e.scrollLeft);
      results.push({...result,name:item.name,order:item.order});
      await context.close();
    }
  } finally { await browser.close(); }
  process.stdout.write(JSON.stringify(results));
})().catch(e=>{console.error(e.stack);process.exit(1);});
"""


@unittest.skipUnless(os.environ.get('BILINGUAL_HTML_BROWSER_TESTS') == '1',
                     'optional real-browser profile; set BILINGUAL_HTML_BROWSER_TESTS=1')
class BilingualHTMLBrowserTests(unittest.TestCase):
    def test_table_words_times_pairs_and_keyboard_scroll(self):
        module = os.environ.get('PLAYWRIGHT_NODE_MODULE')
        executable = os.environ.get('CHROMIUM_EXECUTABLE')
        self.assertTrue(module and executable, 'Set an installed Playwright Node module and Chromium executable')
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            inputs = []
            for name, source, target, target_dir, order in [
                ('en-fr','en','fr','ltr','source-first'),
                ('reversed','en','fr','ltr','target-first'),
                ('fr-ar','fr','ar','rtl','source-first'),
                ('ja-zh','ja','zh-Hans','ltr','source-first'),
            ]:
                data = minimal()
                data['languages'] = {'source':{'tag':source,'dir':'ltr'},'target':{'tag':target,'dir':target_dir}}
                data['config'] = {'desktop_order':order}
                data['blocks'] = [{'type':'table','headers':[
                    pair('h-stage','Point in the afternoon','Moment de l’après-midi'),
                    pair('h-time','Time','Heure'),pair('h-action','What happens','Déroulement')],
                    'rows':[[pair('r1-stage','Doors open','Ouverture des portes'),pair('r1-time','14:00','14:00'),
                             pair('r1-action','Booked and open places become available',
                                  'Les places réservées et les places libres deviennent disponibles')],
                            [pair('r2-stage','Reserved places released','Libération des places réservées'),
                             pair('r2-time','14:25','14:25'),pair('r2-action','Any remaining reserved places become open',
                                  'Toutes les places encore réservées deviennent libres')]]}]
                if target_dir == 'rtl':
                    data['blocks'][0]['headers'][0]['target'] = 'المرحلة'
                    data['blocks'][0]['rows'][0][2]['target'] = 'تصبح الأماكن المحجوزة والأماكن المتاحة متاحة للزوار'
                if name == 'ja-zh':
                    data['blocks'][0]['headers'][0].update(source='午後の予定',target='下午安排')
                source_path = base / (name+'.json')
                source_path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
                output = RENDERER.render_document(source_path,base/name)
                inputs.append({'name':name,'path':str(output/'index.html'),'order':order})
            config = {'inputs':inputs,'module':module,'executable':executable,
                      'allowNoSandbox':os.environ.get('BILINGUAL_HTML_ALLOW_NO_SANDBOX')=='1'}
            config_path=base/'browser-config.json';config_path.write_text(json.dumps(config),encoding='utf-8')
            run=subprocess.run([os.environ.get('NODE_BINARY','node'),'-e',DRIVER,str(config_path)],
                               capture_output=True,text=True,timeout=75)
            self.assertEqual(run.returncode,0,run.stderr)
            results=json.loads(run.stdout)
            self.assertEqual(len(results),8)
            for result in results:
                with self.subTest(case=result['name'],width=result['width']):
                    self.assertEqual(result['headingLines'],[1,1],result)
                    self.assertEqual(result['timeLines'],[1,1],result)
                    self.assertLessEqual(result['documentWidth'],result['width'],result)
                    self.assertEqual(result['role'],'region',result)
                    self.assertEqual(result['tabindex'],'0',result)
                    self.assertTrue(result['labelled'] and result['focused'],result)
                    if result['width']==390:
                        self.assertGreaterEqual(result['target']['y'],result['source']['bottom'],result)
                    elif result['order']=='target-first':
                        self.assertLess(result['target']['x'],result['source']['x'],result)
                    else:
                        self.assertLess(result['source']['x'],result['target']['x'],result)
                    if result['scrollWidth']>result['clientWidth']:
                        self.assertGreater(result['scrollAfterKey'],0,result)


if __name__=='__main__':
    unittest.main()
