// Export with python tests/test_local_history.py --export output/columns-fixtures.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

(async () => {
  const root = process.env.COLUMNS_FIXTURES;
  if (!root) throw new Error('Set COLUMNS_FIXTURES to the exported fixture folder.');
  const read = file => fs.readFileSync(path.join(root, file), 'utf8');
  const browser = await chromium.launch({headless: true, channel: process.env.BROWSER_CHANNEL || undefined});
  try {
    for (const lang of ['en', 'ar']) {
      const context = await browser.newContext({viewport: {width: lang === 'ar' ? 390 : 1440, height: 900}});
      const choices = JSON.parse(read(`columns-${lang}.json`));
      let selected = choices.selected;
      const requests = [], errors = [];
      await context.route('http://127.0.0.1:5067/**', async route => {
        const request = route.request(), url = new URL(request.url());
        requests.push({url: url.pathname, method: request.method()});
        if (['/connections', '/diwany'].includes(url.pathname)) {
          await route.fulfill({contentType: 'text/html', body: read(`${url.pathname.slice(1)}-${lang}.html`)});
        } else if (/^\/static\/[\w-]+\.(css|js)$/.test(url.pathname)) {
          const file = path.join(__dirname, '..', 'static', path.basename(url.pathname));
          await route.fulfill({contentType: file.endsWith('.css') ? 'text/css' : 'text/javascript', body: fs.readFileSync(file)});
        } else {
          let result = {ok: true};
          if (url.pathname === '/api/diwany/columns') {
            if (request.method() === 'POST') {
              assert.ok(request.headers()['x-csrf-token']);
              selected = request.postDataJSON().columns;
            } else result = {...choices, selected};
          } else if (url.pathname === '/api/diwany/tasks') {
            result = JSON.parse(read(`tasks-${lang}.json`));
            const original = new Map(result.columns.map((column, i) => [column.key, result.records[0].display_values[i]]));
            result.columns = selected.map(column => ({...column, label: column.label || choices.available.find(item => item.key === column.key).label}));
            result.records[0].display_values = selected.map(column => column.key === 'json:department.name' ? 'المالية' : original.get(column.key));
          } else if (url.pathname === '/api/intelligence/tags') result.tags = [];
          else if (url.pathname === '/api/intelligence/domains') {result.domains = []; result.builtins = [];}
          else if (url.pathname === '/api/employees') {result.people = []; result.sources = {}; result.total = 0;}
          else { await route.fulfill({status: 404, contentType: 'application/json', body: JSON.stringify({ok: false, error: 'Fixture unavailable'})}); return; }
          await route.fulfill({contentType: 'application/json', body: JSON.stringify(result)});
        }
      });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      await page.goto('http://127.0.0.1:5067/connections#diwanColumnsSettings');
      const row = page.locator('[data-column-key="json:department.name"]');
      await row.locator('[type=checkbox]').check();
      await row.locator('input:not([type=checkbox])').fill('Department / القسم');
      await page.locator('#diwanColumnsForm button:not([type])').click();
      await page.waitForFunction(() => document.querySelector('#diwanColumnsStatus').textContent && !document.querySelector('#diwanColumnsForm button').disabled);
      assert.ok(selected.some(column => column.key === 'json:department.name' && column.label === 'Department / القسم'));
      await page.reload();
      await row.locator('[type=checkbox]').waitFor();
      assert.equal(await row.locator('[type=checkbox]').isChecked(), true);
      assert.equal(await row.locator('input:not([type=checkbox])').inputValue(), 'Department / القسم');
      assert.equal(await page.locator('#diwanTokenDialog').evaluate(dialog => dialog.open), false);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2));
      const artifacts = process.env.COLUMNS_ARTIFACTS;
      if (artifacts) {
        fs.mkdirSync(artifacts, {recursive: true});
        await page.screenshot({path: path.join(artifacts, `columns-${lang}.png`), fullPage: true});
      }
      await page.goto('http://127.0.0.1:5067/diwany');
      await page.locator('#diwanRows th').first().waitFor();
      assert.match(await page.locator('#diwanRows').innerText(), /Department \/ القسم/);
      assert.match(await page.locator('#diwanRows').innerText(), /المالية/);
      assert.equal(await page.locator('#diwanTokenDialog').evaluate(dialog => dialog.open), false);
      await page.evaluate(() => document.documentElement.dataset.theme = 'dark');
      if (artifacts) await page.screenshot({path: path.join(artifacts, `diwany-${lang}-dark.png`), fullPage: true});
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2));
      assert.deepEqual(errors, []);
      assert.deepEqual(requests.filter(request => request.method !== 'GET').map(request => request.url), ['/api/diwany/columns']);
      await context.close();
    }
    process.stdout.write('Column selection, persistence, table values, token reuse, English/Arabic and mobile browser checks passed.\n');
  } finally { await browser.close(); }
})().catch(error => { process.stderr.write(error.stack + '\n'); process.exitCode = 1; });
