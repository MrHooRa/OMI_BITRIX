// Export isolated fixtures: python tests/test_calendar.py --export output/calendar-fixtures
// Set CALENDAR_FIXTURES to that folder, then run with optional Playwright installed.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

(async () => {
  if (!process.env.CALENDAR_FIXTURES) throw new Error('Export fixtures first and set CALENDAR_FIXTURES (see README).');
  const cookie = JSON.parse(fs.readFileSync(path.join(process.env.CALENDAR_FIXTURES, 'cookies.json'), 'utf8'));
  const browser = await chromium.launch({headless: true, channel: process.env.BROWSER_CHANNEL || undefined});
  try {
    async function fixtures(context) {
      if (!process.env.CALENDAR_FIXTURES) return;
      await context.route('http://127.0.0.1:5066/**', async route => {
        const request = route.request(), url = new URL(request.url());
        let file, contentType;
        if (url.pathname === '/calendar') {
          const cookies = await context.cookies();
          const lang = cookies.some(c => c.name === cookie.name && c.value === cookie.ar) ? 'ar' : 'en';
          file = path.join(process.env.CALENDAR_FIXTURES, `${lang}.html`); contentType = 'text/html; charset=utf-8';
        } else if (url.pathname === '/api/calendar') {
          file = path.join(process.env.CALENDAR_FIXTURES, 'tasks.json'); contentType = 'application/json';
        } else if (/^\/static\/[\w-]+\.(js|css)$/.test(url.pathname)) {
          file = path.join(__dirname, '..', 'static', path.basename(url.pathname));
          contentType = file.endsWith('.js') ? 'text/javascript' : 'text/css';
        } else { await route.fulfill({status: 404, body: ''}); return; }
        await route.fulfill({status: 200, contentType, body: fs.readFileSync(file)});
      });
    }
    const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
    await fixtures(context);
    await context.addCookies([{name: cookie.name, value: cookie.en, url: 'http://127.0.0.1:5066'}]);
    const page = await context.newPage();
    const errors = [], mutations = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => { if (request.method() !== 'GET') mutations.push(request.url()); });
    await page.clock.setFixedTime(new Date('2026-10-10T10:00:00Z'));
    await page.goto('http://127.0.0.1:5066/calendar');
    await page.waitForFunction(() => document.querySelector('#calCount').textContent.startsWith('3 '));
    await page.click('#calToday');
    await page.locator('[data-task-id="102"]').dragTo(page.locator('[data-date="2026-10-15"]'));
    assert.equal(await page.locator('[data-date="2026-10-15"] [data-task-id="102"]').count(), 1);
    await page.reload();
    await page.waitForFunction(() => document.querySelector('#calCount').textContent.startsWith('3 '));
    await page.click('#calToday');
    assert.equal(await page.locator('[data-date="2026-10-15"] [data-task-id="102"]').count(), 1);
    await page.locator('[data-task-id="101"]').click();
    await page.fill('#calPlanDate', '2026-10-20');
    await page.locator('#calPlanForm button[type="submit"], #calPlanForm button:not([type])').click();
    assert.equal(await page.locator('[data-date="2026-10-20"] [data-task-id="101"]').count(), 1);
    assert.match(await page.locator('[data-task-id="101"]').innerText(), /11 Oct 2026/);
    await page.click('#calUndo');
    assert.equal(await page.locator('[data-date="2026-10-11"] [data-task-id="101"]').count(), 1);
    await page.locator('[data-task-id="102"]').click();
    await page.selectOption('#calColleague', '2');
    await page.fill('#calRemindDate', '2026-10-10');
    await page.fill('#calNote', 'Ask for the validation file <sample>');
    await page.locator('#calReminderForm button').click();
    assert.match(await page.locator('#calReminders').innerText(), /Ahmed/);
    await page.click('#calClose');
    assert.equal(await page.locator('[data-task-id="102"] .cal-colleagues').innerText(), 'Colleague: Ahmed');
    assert.match(await page.locator('#calDue').innerText(), /Ask for the validation file <sample>/);
    await page.locator('#calDue').getByRole('button', {name: 'Mark done', exact: true}).click();
    assert.match(await page.locator('#calDue').innerText(), /No follow-ups due/);
    assert.equal(await page.locator('[data-task-id="102"] .cal-colleagues').innerText(), 'Colleague: Ahmed');
    await page.locator('[data-task-id="102"]').click();
    await page.locator('#calReminders').getByRole('button', {name: 'Reopen', exact: true}).click();
    await page.click('#calClose');
    await page.selectOption('#calStatus', 'completed');
    assert.equal(await page.locator('.cal-card').count(), 1);
    await page.selectOption('#calStatus', 'all');
    await page.fill('#calSearch', 'missing task');
    assert.equal(await page.locator('.cal-card').count(), 0);
    await page.fill('#calSearch', '');
    await page.selectOption('#calProject', '8');
    assert.equal(await page.locator('.cal-card').count(), 1);
    await page.selectOption('#calProject', '');
    const output = process.env.CALENDAR_ARTIFACTS;
    if (output) {
      fs.mkdirSync(output, {recursive: true});
      await page.screenshot({path: path.join(output, 'calendar-desktop.png'), fullPage: true, animations: 'disabled'});
    }
    await page.evaluate(() => document.documentElement.dataset.theme = 'dark');
    if (output) await page.screenshot({path: path.join(output, 'calendar-dark.png'), fullPage: true, animations: 'disabled'});
    // A separate employee cannot see this employee's saved dates or reminders.
    const arabic = await browser.newContext({viewport: {width: 390, height: 844}});
    await fixtures(arabic);
    await arabic.addCookies([{name: cookie.name, value: cookie.ar, url: 'http://127.0.0.1:5066'}]);
    const mobile = await arabic.newPage();
    mobile.on('pageerror', error => errors.push(error.message));
    await mobile.clock.setFixedTime(new Date('2026-10-10T10:00:00Z'));
    await mobile.goto('http://127.0.0.1:5066/calendar');
    await mobile.waitForFunction(() => document.querySelector('#calCount').textContent.startsWith('3 '));
    await mobile.click('#calToday');
    assert.equal(await mobile.locator('html').getAttribute('dir'), 'rtl');
    assert.equal(await mobile.locator('#calUndated [data-task-id="102"]').count(), 1);
    assert.equal(await mobile.locator('#calDue .cal-reminder').count(), 0);
    assert.ok(await mobile.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await mobile.locator('[data-task-id="102"]').click();
    await mobile.fill('#calPlanDate', '2026-10-18');
    await mobile.locator('#calPlanForm button:not([type])').click();
    assert.equal(await mobile.locator('[data-date="2026-10-18"] [data-task-id="102"]').count(), 1);
    await mobile.locator('[data-task-id="102"]').click();
    await mobile.fill('#calName', 'خالد');
    await mobile.fill('#calRemindDate', '2026-10-18');
    await mobile.locator('#calReminderForm button').click();
    await mobile.click('#calClose');
    assert.equal(await mobile.locator('[data-task-id="102"] .cal-colleagues').innerText(), 'الزميل: خالد');
    await mobile.evaluate(() => window.scrollTo(0, 0));
    if (output) await mobile.screenshot({path: path.join(output, 'calendar-arabic-mobile.png'), fullPage: true, animations: 'disabled'});
    // Long Arabic task and colleague names must stay within both desktop side panels.
    await mobile.setViewportSize({width: 1544, height: 1188});
    const crowdedTasks = await mobile.evaluate(async () => (await fetch('/api/calendar')).json());
    crowdedTasks.tasks.find(task => task.id === '102').title = 'مراجعة رواتب الموظفين لشهر ديسمبر [OMI-SIM-B2-20261003] والتحقق من نتائج المطابقة';
    await mobile.route('**/api/calendar', route => route.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify(crowdedTasks)}));
    await mobile.click('#calRefresh');
    await mobile.waitForFunction(() => !document.querySelector('#calRefresh').disabled);
    await mobile.locator('[data-task-id="102"]').click();
    await mobile.fill('#calName', 'خالدعبدالله'.repeat(7));
    await mobile.fill('#calRemindDate', '2026-10-10');
    await mobile.locator('#calReminderForm button').click();
    await mobile.click('#calClose');
    await mobile.evaluate(() => { document.documentElement.dataset.theme = 'dark'; window.scrollTo(0, 0); });
    const panelsFit = await mobile.evaluate(() => {
      const main = document.querySelector('.main').getBoundingClientRect();
      return [...document.querySelectorAll('.cal-side-panel')].every(panel => {
        const box = panel.getBoundingClientRect();
        return box.left >= main.left && box.right <= main.right && panel.scrollWidth <= panel.clientWidth;
      }) && document.documentElement.scrollWidth <= window.innerWidth;
    });
    assert.ok(panelsFit, 'Arabic side panels and long reminder titles must not overflow');
    if (output) await mobile.screenshot({path: path.join(output, 'calendar-arabic-desktop.png'), fullPage: true, animations: 'disabled'});
    // A failed refresh keeps the currently displayed tasks and shows an actionable error.
    await page.route('**/api/calendar', route => route.fulfill({status: 502, contentType: 'application/json', body: '{}'}));
    await page.click('#calRefresh');
    await page.waitForFunction(() => document.querySelector('#calMessage').classList.contains('is-error'));
    assert.equal(await page.locator('.cal-card').count(), 3);
    // Corrupt storage is never silently overwritten by a subsequent save.
    await page.evaluate(() => {
      const key = `omi-calendar-v1:${document.querySelector('#taskCalendar').dataset.scope}`;
      localStorage.setItem(key, '{broken');
    });
    await page.locator('[data-task-id="102"]').click();
    await page.fill('#calPlanDate', '2026-10-22');
    await page.locator('#calPlanForm button:not([type])').click();
    assert.match(await page.locator('#calDialogMessage').innerText(), /could not be read/);
    assert.equal(await page.evaluate(() => localStorage.getItem(`omi-calendar-v1:${document.querySelector('#taskCalendar').dataset.scope}`)), '{broken');
    assert.deepEqual(errors, []);
    assert.deepEqual(mutations, []);
    console.log('PASS: drag/drop, date picker, persistence, deadline preservation, undo, reminders, filters, profile isolation, Arabic/mobile, dark mode, failed refresh, corrupt storage; no write requests.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
