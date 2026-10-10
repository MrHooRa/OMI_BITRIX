(() => {
  'use strict';
  const root = document.getElementById('taskCalendar');
  if (!root) return;
  const $ = id => document.getElementById(id);
  const t = key => window.WC_I18N[key] || key;
  const locale = window.WC_LANG === 'ar' ? 'ar-SA-u-ca-gregory' : 'en-GB';
  const key = `omi-calendar-v1:${root.dataset.scope}`;
  const empty = () => ({dates: {}, reminders: []});
  const validDate = value => /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(Date.parse(`${value}T12:00:00Z`)) &&
    new Date(`${value}T12:00:00Z`).toISOString().slice(0, 10) === value;
  const dayString = date => date.toISOString().slice(0, 10);
  const today = () => {
    const parts = new Intl.DateTimeFormat('en', {timeZone: 'Asia/Riyadh', year: 'numeric', month: '2-digit', day: '2-digit'}).formatToParts(new Date());
    const part = type => parts.find(p => p.type === type).value;
    return `${part('year')}-${part('month')}-${part('day')}`;
  };
  const monthDate = value => new Date(`${value.slice(0, 7)}-01T12:00:00Z`);
  const formatDate = value => value ? new Intl.DateTimeFormat(locale, {dateStyle: 'medium', timeZone: 'UTC'}).format(new Date(`${value.slice(0, 10)}T12:00:00Z`)) : t('cal_undated');
  let state = empty(), tasks = [], members = [], selected = null, previous = null;
  let month = monthDate(root.dataset.today), loaded = false, dragging = null;
  function message(text, error = false) {
    $('calMessage').textContent = text;
    $('calMessage').classList.toggle('is-error', error);
    $('calDialogMessage').textContent = text;
    $('calDialogMessage').classList.toggle('is-error', error);
  }
  function readState() {
    const raw = localStorage.getItem(key);
    if (!raw) return empty();
    const data = JSON.parse(raw);
    if (!data || !data.dates || typeof data.dates !== 'object' || Array.isArray(data.dates) || !Array.isArray(data.reminders) ||
        !Object.entries(data.dates).every(([id, date]) => /^\d+$/.test(id) && (date === '' || validDate(date))) ||
        !data.reminders.every(r => r && typeof r.id === 'string' && /^\d+$/.test(r.taskId) &&
          typeof r.name === 'string' && typeof r.note === 'string' && typeof r.done === 'boolean' && validDate(r.date))) {
      throw new Error(t('cal_storage_invalid'));
    }
    return data;
  }
  try { state = readState(); } catch (_) { message(t('cal_storage_invalid'), true); }
  function save(change, notice = 'cal_saved') {
    let current;
    try { current = readState(); } catch (_) { message(t('cal_storage_invalid'), true); return false; }
    const next = JSON.parse(JSON.stringify(current));
    change(next);
    try { localStorage.setItem(key, JSON.stringify(next)); }
    catch (_) { message(t('cal_storage_error'), true); return false; }
    previous = current; state = next;
    $('calUndo').disabled = false;
    message(t(notice)); render();
    if (selected) renderReminders();
    return true;
  }
  function element(tag, text, cls) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  }
  function action(text, callback) {
    const button = element('button', text, 'btn secondary small');
    button.type = 'button'; button.addEventListener('click', callback);
    return button;
  }
  const planned = task => Object.hasOwn(state.dates, task.id) ? state.dates[task.id] : task.deadline.slice(0, 10);
  function filteredTasks() {
    const query = $('calSearch').value.trim().toLocaleLowerCase();
    return tasks.filter(task => (!query || `${task.title} ${task.id} ${task.project}`.toLocaleLowerCase().includes(query)) &&
      (!$('calProject').value || task.projectId === $('calProject').value) &&
      ($('calStatus').value === 'all' || (task.status === '5') === ($('calStatus').value === 'completed')));
  }
  function card(task) {
    const node = element('button', undefined, `cal-card${task.status === '5' ? ' is-completed' : task.priority === '2' ? ' is-high' : ''}`);
    node.type = 'button'; node.draggable = true; node.dataset.taskId = task.id;
    node.append(element('small', `${task.project} · #${task.id}`), element('strong', task.title));
    const colleagues = [...new Set(state.reminders.filter(r => r.taskId === task.id)
      .map(r => r.name.trim()).filter(Boolean))];
    if (colleagues.length) {
      const label = element('small', `${t('cal_colleague')}: ${colleagues.join(window.WC_LANG === 'ar' ? '، ' : ', ')}`, 'cal-colleagues');
      label.dir = 'auto';
      node.append(label);
    }
    node.append(element('small', `${t('cal_deadline')}: ${formatDate(task.deadline)}`));
    if (task.status === '5') node.append(element('small', t('cal_completed_note')));
    else if (task.priority === '2') node.append(element('small', t('cal_high')));
    node.addEventListener('click', () => openTask(task));
    node.addEventListener('dragstart', event => {
      dragging = task.id;
      event.dataTransfer.setData('text/plain', task.id);
      event.dataTransfer.effectAllowed = 'move';
    });
    node.addEventListener('dragend', () => {
      dragging = null;
      root.querySelectorAll('.cal-drop').forEach(n => n.classList.remove('cal-drop'));
    });
    return node;
  }
  function dropTarget(node, date) {
    node.addEventListener('dragover', event => {
      if (!dragging) return;
      event.preventDefault(); event.dataTransfer.dropEffect = 'move'; node.classList.add('cal-drop');
    });
    node.addEventListener('dragleave', event => {
      if (!node.contains(event.relatedTarget)) node.classList.remove('cal-drop');
    });
    node.addEventListener('drop', event => {
      event.preventDefault(); node.classList.remove('cal-drop');
      const id = dragging; dragging = null;
      if (!id || !tasks.some(task => task.id === id)) return;
      save(next => { next.dates[id] = date; });
    });
  }
  function render() {
    const visible = filteredTasks(), grid = $('calGrid');
    grid.replaceChildren(); $('calUndated').replaceChildren();
    $('calCount').textContent = `${visible.length} ${t('cal_count')}`;
    $('calMonth').textContent = new Intl.DateTimeFormat(locale, {month: 'long', year: 'numeric', timeZone: 'UTC'}).format(month);
    const start = new Date(month);
    start.setUTCDate(1 - month.getUTCDay());
    for (let i = 0; i < 7; i++) {
      const day = new Date(start); day.setUTCDate(start.getUTCDate() + i);
      grid.append(element('div', new Intl.DateTimeFormat(locale, {weekday: 'short', timeZone: 'UTC'}).format(day), 'cal-weekday'));
    }
    const grouped = new Map();
    visible.forEach(task => {
      const date = planned(task);
      if (!grouped.has(date)) grouped.set(date, []);
      grouped.get(date).push(task);
    });
    const currentDay = today();
    for (let i = 0; i < 42; i++) {
      const day = new Date(start); day.setUTCDate(start.getUTCDate() + i);
      const date = dayString(day), cell = element('div', undefined, 'cal-day');
      cell.dataset.date = date;
      cell.classList.toggle('is-today', date === currentDay);
      cell.classList.toggle('is-outside', day.getUTCMonth() !== month.getUTCMonth());
      const label = element('time');
      label.append(element('span', new Intl.NumberFormat(locale).format(day.getUTCDate()), 'cal-day-number'),
        element('span', new Intl.DateTimeFormat(locale, {weekday: 'long', month: 'short', day: 'numeric', timeZone: 'UTC'}).format(day), 'cal-day-long'));
      label.dateTime = date; label.title = formatDate(date); cell.append(label);
      cell.classList.toggle('has-tasks', (grouped.get(date) || []).length > 0);
      (grouped.get(date) || []).forEach(task => cell.append(card(task)));
      dropTarget(cell, date); grid.append(cell);
    }
    const undated = grouped.get('') || [];
    $('calUndatedCount').textContent = new Intl.NumberFormat(locale).format(undated.length);
    undated.forEach(task => $('calUndated').append(card(task)));
    if (!undated.length) $('calUndated').append(element('p', t('cal_none_undated'), 'cal-empty'));
    renderDue();
  }
  function reminderRow(reminder, showTask = false) {
    const node = element('div', undefined, `cal-reminder${reminder.done ? ' is-done' : ''}`);
    const heading = element('div', undefined, 'cal-reminder-heading');
    const avatar = element('span', [...reminder.name.trim()][0] || '•', 'cal-reminder-avatar');
    avatar.setAttribute('aria-hidden', 'true');
    const person = element('div', undefined, 'cal-reminder-person');
    const name = element('strong', reminder.name); name.dir = 'auto';
    const date = element('time', formatDate(reminder.date)); date.dateTime = reminder.date;
    person.append(name, date); heading.append(avatar, person); node.append(heading);
    if (showTask) {
      const task = tasks.find(item => item.id === reminder.taskId);
      if (task) {
        const taskButton = action(task.title, () => openTask(task));
        taskButton.classList.add('cal-reminder-task');
        node.append(taskButton);
      }
    }
    if (reminder.note) node.append(element('p', reminder.note, 'cal-reminder-note'));
    const buttons = element('div', undefined, 'cal-actions');
    buttons.append(action(t(reminder.done ? 'cal_reopen' : 'cal_done'), () => save(next => {
      const item = next.reminders.find(r => r.id === reminder.id);
      if (item) item.done = !item.done;
    }, 'cal_reminder_saved')));
    if (!showTask) buttons.append(action(t('cal_remove'), () => save(next => {
      next.reminders = next.reminders.filter(r => r.id !== reminder.id);
    }, 'cal_reminder_saved')));
    node.append(buttons); return node;
  }
  function renderDue() {
    const container = $('calDue'); container.replaceChildren();
    const ids = new Set(tasks.map(task => task.id));
    const due = state.reminders.filter(r => !r.done && r.date <= today() && ids.has(r.taskId))
      .sort((a, b) => a.date.localeCompare(b.date));
    $('calDueCount').textContent = new Intl.NumberFormat(locale).format(due.length);
    due.forEach(r => container.append(reminderRow(r, true)));
    if (!due.length) container.append(element('p', t('cal_none_due'), 'cal-empty'));
  }
  function renderReminders() {
    const container = $('calReminders'); container.replaceChildren();
    state.reminders.filter(r => r.taskId === selected.id).sort((a, b) => a.date.localeCompare(b.date))
      .forEach(r => container.append(reminderRow(r)));
    if (!container.childElementCount) container.append(element('p', t('cal_no_followups'), 'muted'));
  }
  function openTask(task) {
    selected = task; $('calTaskTitle').textContent = task.title;
    $('calDialogMessage').textContent = '';
    $('calTaskMeta').textContent = `${task.project} · ${t('cal_deadline')}: ${formatDate(task.deadline)}`;
    $('calPlanDate').value = planned(task);
    $('calOpen').href = task.url;
    // Completed tasks are still plannable, but the existing detail view is active-task scoped.
    $('calOpen').hidden = task.status === '5';
    $('calReminderForm').reset(); $('calRemindDate').value = today();
    renderReminders(); $('calDialog').showModal();
  }
  async function loadTasks() {
    $('calRefresh').disabled = true; message(t('cal_loading'));
    try {
      const response = await fetch(root.dataset.source, {headers: {Accept: 'application/json'}});
      if (!response.ok || response.redirected) throw new Error();
      const data = await response.json();
      if (!Array.isArray(data.tasks) || !Array.isArray(data.members)) throw new Error();
      tasks = data.tasks; members = data.members; loaded = true;
      const selectedProject = $('calProject').value;
      $('calProject').replaceChildren(new Option(t('cal_projects'), ''));
      const projects = new Map(tasks.map(task => [task.projectId, task.project]));
      projects.forEach((name, id) => $('calProject').add(new Option(name, id)));
      if (projects.has(selectedProject)) $('calProject').value = selectedProject;
      $('calColleague').replaceChildren(new Option(t('cal_choose'), ''));
      members.forEach(member => $('calColleague').add(new Option(member.name, member.id)));
      message('');
      try { state = readState(); } catch (_) { message(t('cal_storage_invalid'), true); }
      render();
    } catch (_) { message(t('cal_load_error'), true); }
    finally { $('calRefresh').disabled = false; }
  }
  $('calPlanForm').addEventListener('submit', event => {
    event.preventDefault();
    const date = $('calPlanDate').value;
    if (date && !validDate(date)) return;
    if (save(next => { next.dates[selected.id] = date; })) $('calDialog').close();
  });
  $('calReset').addEventListener('click', () => {
    if (save(next => { delete next.dates[selected.id]; })) $('calPlanDate').value = planned(selected);
  });
  $('calReminderForm').addEventListener('submit', event => {
    event.preventDefault();
    const member = members.find(m => m.id === $('calColleague').value);
    const name = $('calName').value.trim() || (member && member.name), date = $('calRemindDate').value;
    if (!name || !validDate(date)) { message(t('cal_need_colleague'), true); return; }
    if (save(next => next.reminders.push({id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      taskId: selected.id, name, date, note: $('calNote').value.trim(), done: false}), 'cal_reminder_saved')) {
      $('calReminderForm').reset(); $('calRemindDate').value = today();
    }
  });
  $('calClose').addEventListener('click', () => $('calDialog').close());
  $('calDialog').addEventListener('close', () => { selected = null; });
  $('calUndo').addEventListener('click', () => {
    if (!previous) return;
    const backup = previous;
    if (save(next => { next.dates = backup.dates; next.reminders = backup.reminders; })) {
      previous = null; $('calUndo').disabled = true;
    }
  });
  $('calPrev').addEventListener('click', () => { month.setUTCMonth(month.getUTCMonth() - 1); render(); });
  $('calNext').addEventListener('click', () => { month.setUTCMonth(month.getUTCMonth() + 1); render(); });
  $('calToday').addEventListener('click', () => { month = monthDate(today()); render(); });
  ['calSearch', 'calProject', 'calStatus'].forEach(id => $(id).addEventListener('input', render));
  $('calRefresh').addEventListener('click', loadTasks);
  dropTarget($('calUndated'), '');
  window.addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    try {
      state = readState(); previous = null; $('calUndo').disabled = true;
      render(); if (selected) { $('calPlanDate').value = planned(selected); renderReminders(); }
    } catch (_) { message(t('cal_storage_invalid'), true); }
  });
  let lastDay = today();
  setInterval(() => {
    if (loaded && today() !== lastDay) { lastDay = today(); render(); }
  }, 60000);
  render(); loadTasks();
})();
