(() => {
  const $ = (q, root=document) => root.querySelector(q);
  const $$ = (q, root=document) => [...root.querySelectorAll(q)];
  const I = window.WC_I18N || {};
  const fmt = (key, vars={}) => String(I[key] || key).replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? `{${k}}`);

  // Theme is intentionally browser-local: it changes presentation only and never touches SQLite.
  const THEME_KEY = 'work-cockpit-theme';
  function setTheme(theme) {
    const next = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem(THEME_KEY, next); } catch (_) {}
    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
      btn.setAttribute('aria-pressed', next === 'dark' ? 'true' : 'false');
    });
  }
  document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
    btn.addEventListener('click', () => setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
  });
  setTheme(document.documentElement.dataset.theme || 'light');

  const testBtn = $('#testBitrix');
  if (testBtn) {
    testBtn.addEventListener('click', async () => {
      const url = $('#webhook_url').value.trim();
      const status = $('#connectionStatus');
      if (!url) return;
      status.className = 'status-line';
      status.textContent = I.connecting || 'Connecting to Bitrix24…';
      testBtn.disabled = true;
      try {
        const r = await fetch('/api/test-bitrix', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({webhook_url:url})});
        const data = await r.json();
        if (!data.ok) throw new Error(data.error || I.connection_failed || 'Connection failed');
        status.className = 'status-line ok';
        status.textContent = fmt('fetching_projects', {name:data.user.name || I.bitrix_user || 'Bitrix user', id:data.user.id});
        const pr = await fetch('/api/projects', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({webhook_url:url})});
        const pd = await pr.json();
        if (!pd.ok) throw new Error(pd.error || I.could_not_fetch || 'Could not fetch projects');
        renderProjects(pd.projects || []);
        status.textContent = fmt('connected_as', {name:data.user.name || I.bitrix_user || 'Bitrix user', count:pd.projects.length});
      } catch (e) {
        status.className = 'status-line bad';
        status.textContent = e.message;
      } finally { testBtn.disabled = false; }
    });
  }

  function escapeHtml(v='') { return v.replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
  function renderProjects(projects) {
    const grid = $('#projectGrid'); if (!grid) return;
    grid.innerHTML = projects.length ? projects.map(p => `
      <label class="project-option" data-name="${escapeHtml((p.name||'').toLowerCase())}">
        <input type="checkbox" name="project_id" value="${escapeHtml(String(p.id))}">
        <input type="hidden" name="project_name" value="${escapeHtml(p.name||'')}">
        <span><strong>${escapeHtml(p.name||I.untitled||'Untitled')}</strong><small dir="ltr">ID ${escapeHtml(String(p.id))}${p.members ? ` · ${p.members} ${escapeHtml(I.members||'members')}` : ''}</small></span>
      </label>`).join('') : `<div class="empty-box">${escapeHtml(I.no_projects_returned || 'No projects were returned for this webhook user.')}</div>`;
  }

  const search = $('#projectSearch');
  if (search) search.addEventListener('input', () => {
    const q = search.value.trim().toLowerCase();
    $$('.project-option', $('#projectGrid')).forEach(el => { el.style.display = (el.dataset.name || el.textContent.toLowerCase()).includes(q) ? '' : 'none'; });
  });
  $('#selectAll')?.addEventListener('click', () => $$('#projectGrid input[type=checkbox]').forEach(x => x.checked = true));
  $('#clearAll')?.addEventListener('click', () => $$('#projectGrid input[type=checkbox]').forEach(x => x.checked = false));

  const dialog = $('#commentDialog');
  $$('.comment-trigger').forEach(btn => btn.addEventListener('click', () => {
    if (!dialog) return;
    $('#commentForm').action = `/task/${btn.dataset.task}/message`;
    $('#commentTitle').textContent = btn.dataset.title || I.progress_update || 'Progress update';
    $('#commentMessage').value = '';
    dialog.showModal();
  }));
  $$('[data-close-dialog]').forEach(btn => btn.addEventListener('click', () => dialog?.close()));
  $$('[data-message]').forEach(btn => btn.addEventListener('click', () => { const t = $('#commentMessage'); if (t) { t.value = btn.dataset.message; t.focus(); } }));
  $$('[data-fill]').forEach(btn => btn.addEventListener('click', () => { const form = btn.closest('form'); const t = $('textarea[name=message]', form); if (t) { t.value = btn.dataset.fill; t.focus(); } }));

  const delayDialog = $('#delayDialog');
  const delayTriggers = $$('.delay-trigger');
  const delayPromptTimes = new Map();
  function openDelayDialog(btn) {
    if (!delayDialog || !btn) return;
    const form = $('#delayForm');
    form.action = `/task/${btn.dataset.task}/justify-delay`;
    $('#delayTitle').textContent = btn.dataset.title ? fmt('justify_delay_prefix', {title:btn.dataset.title}) : (I.why_miss_deadline || 'Why will this task miss its deadline?');
    $('#delayDeadline').textContent = btn.dataset.deadline ? fmt('bitrix_deadline', {deadline:btn.dataset.deadline}) : (I.deadline_unavailable || 'Bitrix deadline not available');
    $('#delayJustification').value = '';
    delayPromptTimes.set(String(btn.dataset.task || ''), Date.now());
    delayDialog.showModal();
    setTimeout(() => $('#delayJustification')?.focus(), 0);
  }
  delayTriggers.forEach(btn => btn.addEventListener('click', () => openDelayDialog(btn)));
  $$('[data-close-delay]').forEach(btn => btn.addEventListener('click', () => delayDialog?.close()));
  $$('[data-justify]').forEach(btn => btn.addEventListener('click', () => {
    const t = $('#delayJustification');
    if (t) { t.value = btn.dataset.justify || ''; t.focus(); t.setSelectionRange(t.value.length, t.value.length); }
  }));
  // An overdue task without a posted justification should actively ask for one.
  const requiredDelay = delayTriggers.find(btn => btn.dataset.autoOpen === '1');
  if (requiredDelay && delayDialog) setTimeout(() => openDelayDialog(requiredDelay), 250);

  // Also catch a deadline that passes while the dashboard/task page stays open.
  // If the user dismisses the prompt, wait 15 minutes before asking again.
  function checkCrossedDeadlines() {
    if (!delayDialog || delayDialog.open) return;
    const now = Date.now();
    const candidate = delayTriggers.find(btn => {
      if (btn.dataset.justified === '1' || !btn.dataset.deadline) return false;
      const deadlineMs = Date.parse(btn.dataset.deadline);
      if (!Number.isFinite(deadlineMs) || deadlineMs > now) return false;
      const last = delayPromptTimes.get(String(btn.dataset.task || '')) || 0;
      return now - last >= 15 * 60 * 1000;
    });
    if (candidate) openDelayDialog(candidate);
  }
  setInterval(checkCrossedDeadlines, 60 * 1000);

  // Personal 8-hour planner. The server provides the default plan; user adjustments
  // are intentionally browser-only so SQLite remains configuration-only.
  const planner = $('#todayPlanner');
  const plannerList = $('#plannerList');
  if (planner && plannerList) {
    const items = () => $$('.planner-item', plannerList);
    const planDate = planner.dataset.date;
    const key = `work-cockpit-plan:${planDate}`;
    const defaultOrder = items().map(el => el.dataset.taskId);
    const defaultMinutes = Object.fromEntries(items().map(el => [el.dataset.taskId, Number(el.dataset.defaultMinutes || 0)]));

    const parseStart = () => {
      const [h, m] = (planner.dataset.start || '08:00').split(':').map(Number);
      return (Number.isFinite(h) ? h : 8) * 60 + (Number.isFinite(m) ? m : 0);
    };
    const hhmm = mins => `${String(Math.floor((mins % 1440) / 60)).padStart(2,'0')}:${String(mins % 60).padStart(2,'0')}`;
    const duration = mins => `${Math.floor(mins / 60)}${I.hour_short || 'h'} ${String(mins % 60).padStart(2,'0')}${I.minute_short || 'm'}`;

    function updatePlan(save=true) {
      let cursor = parseStart();
      let total = 0;
      items().forEach(el => {
        const mins = Math.max(0, Number(el.dataset.minutes || 0));
        $('.planner-start', el).textContent = hhmm(cursor);
        $('.planner-end', el).textContent = hhmm(cursor + mins);
        $('.planner-duration', el).textContent = duration(mins);
        cursor += mins;
        total += mins;
      });
      const totalNode = $('#plannerTotal');
      if (totalNode) {
        totalNode.textContent = duration(total);
        totalNode.classList.toggle('capacity-warning', total !== 480);
      }
      if (save && items().length) {
        try {
          localStorage.setItem(key, JSON.stringify({
            order: items().map(el => el.dataset.taskId),
            minutes: Object.fromEntries(items().map(el => [el.dataset.taskId, Number(el.dataset.minutes || 0)]))
          }));
        } catch (_) {}
      }
    }

    function restorePlan() {
      if (!items().length) return;
      try {
        const saved = JSON.parse(localStorage.getItem(key) || 'null');
        const current = new Set(defaultOrder);
        const savedIds = new Set(saved?.order || []);
        const exactSameTasks = current.size === savedIds.size && [...current].every(id => savedIds.has(id));
        if (!saved || !exactSameTasks) return updatePlan(false);
        saved.order.forEach(id => {
          const el = items().find(x => x.dataset.taskId === String(id));
          if (el) plannerList.appendChild(el);
        });
        items().forEach(el => {
          const value = Number(saved.minutes?.[el.dataset.taskId]);
          if (Number.isFinite(value) && value >= 0) el.dataset.minutes = String(value);
        });
      } catch (_) {}
      updatePlan(false);
    }

    plannerList.addEventListener('click', e => {
      const move = e.target.closest('.plan-move');
      if (move) {
        const item = move.closest('.planner-item');
        if (move.dataset.direction === 'up' && item.previousElementSibling?.classList.contains('planner-item')) {
          plannerList.insertBefore(item, item.previousElementSibling);
        } else if (move.dataset.direction === 'down' && item.nextElementSibling?.classList.contains('planner-item')) {
          plannerList.insertBefore(item.nextElementSibling, item);
        }
        updatePlan();
        return;
      }

      const timeBtn = e.target.closest('.plan-time');
      if (timeBtn) {
        const all = items();
        if (all.length < 2) return;
        const item = timeBtn.closest('.planner-item');
        const delta = Number(timeBtn.dataset.delta || 0);
        const current = Number(item.dataset.minutes || 0);
        if (delta > 0) {
          const donor = all.filter(x => x !== item && Number(x.dataset.minutes || 0) >= 30)
            .sort((a,b) => Number(b.dataset.minutes || 0) - Number(a.dataset.minutes || 0))[0];
          if (!donor) return;
          item.dataset.minutes = String(current + 15);
          donor.dataset.minutes = String(Number(donor.dataset.minutes || 0) - 15);
        } else if (delta < 0 && current >= 30) {
          const recipient = all.find(x => x !== item);
          item.dataset.minutes = String(current - 15);
          recipient.dataset.minutes = String(Number(recipient.dataset.minutes || 0) + 15);
        }
        updatePlan();
      }
    });

    $('#plannerReset')?.addEventListener('click', () => {
      defaultOrder.forEach(id => {
        const el = items().find(x => x.dataset.taskId === id);
        if (el) {
          el.dataset.minutes = String(defaultMinutes[id] || 0);
          plannerList.appendChild(el);
        }
      });
      try { localStorage.removeItem(key); } catch (_) {}
      updatePlan(false);
    });

    restorePlan();
  }


  // OMI Bitrix focus notes. Kept intentionally local/offline and concise.
  const focusQuotes = window.WC_LANG === 'ar' ? [
    'أنهِ الخطوة المفيدة التالية.',
    'لا تنتظر صفاء اليوم؛ ابدأ بأوضح مهمة أمامك.',
    'التوثيق الجيد جزء من الإنجاز، وليس عملاً بعده.',
    'إذا كانت المهمة كبيرة، حوّلها إلى نتيجة صغيرة يمكن تسليمها اليوم.',
    'ركّز على المخرج الذي سيستخدمه شخص آخر.',
    'المهمة الواضحة أسرع من عشر نوايا مفتوحة.',
    'اكتب السبب، احسم القرار، ثم أكمل التنفيذ.',
    'أغلق حلقة واحدة قبل أن تفتح ثلاث حلقات جديدة.',
    'أفضل تحديث للمشرف: ما تم، ما تعطل، وما الخطوة التالية.',
    'أعد استخدام ما نجح: SQL، Workflow، أو طريقة تحقق.',
    'الإنجاز الهادئ يتفوق على الانشغال الظاهر.',
    'اجعل آخر 15 دقيقة للتوثيق والتسليم، لا للمفاجآت.',
    'تأكد دوما أن المهام الصعبة تبدو أسهل مما هي عليه، وأن المهام السهلة تبدو أصعب مما هي عليه.'
  ] : [
    'Finish the next useful thing.',
    'Do the clearest task before searching for the perfect plan.',
    'Documentation is part of delivery, not the work after delivery.',
    'If the task feels large, define one result you can ship today.',
    'Focus on the output someone else will actually use.',
    'One clear task beats ten open intentions.',
    'Write the reason, make the decision, then keep moving.',
    'Close one loop before opening three more.',
    'A useful update says: done, blocked, next.',
    'Reuse what already worked: SQL, workflow, or validation logic.',
    'Quiet completion beats visible busyness.',
    'Reserve the last 15 minutes for documentation and handover.',
    'Make hard tasks look easier than they are, and easy tasks look harder than they are.'
  ];
  const quoteNode = $('#focusQuoteText');
  const quoteButton = $('#nextFocusQuote');
  let previousQuote = -1;
  function showFocusQuote() {
    if (!quoteNode || !focusQuotes.length) return;
    let index = Math.floor(Math.random() * focusQuotes.length);
    if (focusQuotes.length > 1 && index === previousQuote) index = (index + 1) % focusQuotes.length;
    previousQuote = index;
    quoteNode.classList.remove('quote-enter');
    void quoteNode.offsetWidth;
    quoteNode.textContent = focusQuotes[index];
    quoteNode.classList.add('quote-enter');
  }
  if (quoteNode) {
    showFocusQuote();
    quoteButton?.addEventListener('click', showFocusQuote);
    setInterval(showFocusQuote, 45000);
  }

  // Lazy Bitrix discussion history. Dashboard cards stay fast because comments
  // are fetched only when a user expands a task's discussion panel.
  function formatCommentDate(value) {
    if (!value) return '';
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) {
      try {
        return new Intl.DateTimeFormat(window.WC_LANG === 'ar' ? 'ar-SA' : 'en-GB', {
          dateStyle: 'medium', timeStyle: 'short'
        }).format(parsed);
      } catch (_) {}
    }
    return String(value);
  }
  function commentInitial(name='') {
    const value = String(name).trim();
    return value ? value.charAt(0).toUpperCase() : 'B';
  }
  function renderComments(panel, data) {
    const feed = $('[data-comment-feed]', panel);
    const count = $('[data-comment-count]', panel);
    const more = $('[data-comments-more]', panel);
    if (!feed) return;
    const comments = data.comments || [];
    count.textContent = fmt('comments_count', {count: data.available ?? comments.length});
    if (!comments.length) {
      feed.innerHTML = `<div class="comment-feed-state">${escapeHtml(I.no_comments || 'No comments on this task yet.')}</div>`;
    } else {
      feed.innerHTML = comments.map(item => `
        <article class="comment-item">
          <div class="comment-avatar">${escapeHtml(commentInitial(item.author))}</div>
          <div class="comment-content">
            <div class="comment-head"><strong>${escapeHtml(String(item.author || 'Bitrix24'))}</strong><time dir="ltr">${escapeHtml(formatCommentDate(item.date))}</time></div>
            <div class="comment-text">${escapeHtml(String(item.text || ''))}</div>
          </div>
        </article>`).join('');
    }
    if (more) more.hidden = !data.has_more;
    panel.dataset.loaded = '1';
    panel.dataset.available = String(data.available || comments.length);
  }
  async function loadComments(panel, limit=null, force=false) {
    if (!panel || (panel.dataset.loading === '1')) return;
    if (!force && panel.dataset.loaded === '1' && !limit) return;
    const feed = $('[data-comment-feed]', panel);
    const taskId = panel.dataset.taskId;
    const requested = limit || Number(panel.dataset.limit || 12);
    panel.dataset.loading = '1';
    if (feed) feed.innerHTML = `<div class="comment-feed-state loading">${escapeHtml(I.loading_comments || 'Loading comments…')}</div>`;
    try {
      const response = await fetch(`/api/task/${encodeURIComponent(taskId)}/comments?limit=${requested}`, {headers:{'Accept':'application/json'}});
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || I.comments_error || 'Could not load comments.');
      renderComments(panel, data);
    } catch (error) {
      if (feed) feed.innerHTML = `<div class="comment-feed-state error">${escapeHtml(error.message || I.comments_error || 'Could not load comments.')}</div>`;
    } finally {
      panel.dataset.loading = '0';
    }
  }
  $$('[data-comments-panel]').forEach(panel => {
    panel.addEventListener('toggle', () => { if (panel.open) loadComments(panel); });
    $('[data-comments-refresh]', panel)?.addEventListener('click', event => {
      event.preventDefault();
      loadComments(panel, Number(panel.dataset.limit || 12), true);
    });
    $('[data-comments-more]', panel)?.addEventListener('click', event => {
      event.preventDefault();
      loadComments(panel, 50, true);
    });
  });


  // Shared-vault folder browser. This browses the filesystem of the machine
  // running Flask; it never uploads a folder or copies its contents.
  const folderDialog = $('#folderBrowser');
  let folderTarget = null;
  let folderPath = '';
  let folderParent = null;

  function renderFolderRoots(roots=[]) {
    const list = $('#folderList');
    const current = $('#folderCurrent');
    if (!list || !current) return;
    folderPath = '';
    folderParent = null;
    current.textContent = I.folder_roots || 'Locations';
    list.innerHTML = roots.length ? roots.map(path => `
      <button type="button" class="folder-item" data-folder-path="${escapeHtml(path)}">
        <span class="folder-glyph">▣</span><span dir="ltr">${escapeHtml(path)}</span>
      </button>`).join('') : `<div class="empty-box">${escapeHtml(I.no_subfolders || 'No folders found.')}</div>`;
  }

  async function loadFolder(path='') {
    const list = $('#folderList');
    if (!list) return;
    list.innerHTML = `<div class="empty-box">${escapeHtml(I.loading_folders || 'Loading folders…')}</div>`;
    try {
      const url = path ? `/api/folders?path=${encodeURIComponent(path)}` : '/api/folders';
      const response = await fetch(url, {headers:{'Accept':'application/json'}});
      const data = await response.json();
      if (!data.ok) throw new Error(data.error || 'Unable to read folder');
      if (!path) return renderFolderRoots(data.roots || []);
      folderPath = data.path || path;
      folderParent = data.parent || null;
      $('#folderCurrent').textContent = folderPath;
      list.innerHTML = (data.folders || []).length ? data.folders.map(item => `
        <button type="button" class="folder-item" data-folder-path="${escapeHtml(item.path)}">
          <span class="folder-glyph">▰</span><span>${escapeHtml(item.name)}</span>
        </button>`).join('') : `<div class="empty-box">${escapeHtml(I.no_subfolders || I.folder_browser_empty || 'No readable subfolders here.')}</div>`;
    } catch (error) {
      list.innerHTML = `<div class="empty-box folder-error">${escapeHtml(error.message || String(error))}</div>`;
    }
  }

  $$('.folder-browse-trigger').forEach(btn => btn.addEventListener('click', () => {
    if (!folderDialog) return;
    folderTarget = document.getElementById(btn.dataset.target || 'vault_root');
    const initial = folderTarget?.value?.trim() || '';
    folderDialog.showModal();
    loadFolder(initial);
  }));
  $('#folderList')?.addEventListener('click', event => {
    const item = event.target.closest('[data-folder-path]');
    if (item) loadFolder(item.dataset.folderPath || '');
  });
  $('#folderUp')?.addEventListener('click', () => folderParent ? loadFolder(folderParent) : loadFolder(''));
  $('#folderRoots')?.addEventListener('click', () => loadFolder(''));
  $('#folderUse')?.addEventListener('click', () => {
    if (!folderTarget || !folderPath) return;
    folderTarget.value = folderPath;
    folderTarget.dispatchEvent(new Event('input', {bubbles:true}));
    folderDialog?.close();
  });
  $$('[data-folder-close]').forEach(btn => btn.addEventListener('click', () => folderDialog?.close()));

  // Keep the setup path preview truthful while the user changes employee/vault.
  const employeeInput = $('#employee_name');
  const vaultInput = $('#vault_root');
  const pathPreview = $('#employeePathPreview');
  function refreshEmployeePathPreview() {
    if (!pathPreview) return;
    const root = (vaultInput?.value || '').trim().replace(/[\\/]+$/, '');
    const employee = (employeeInput?.value || '').trim() || (I.employee_name || 'Employee');
    const sep = root.includes('\\') ? '\\' : '/';
    pathPreview.textContent = `${root || '…'}${sep}Bitrix Work${sep}${employee}${sep}Project${sep}Task`;
  }
  employeeInput?.addEventListener('input', refreshEmployeePathPreview);
  vaultInput?.addEventListener('input', refreshEmployeePathPreview);
  refreshEmployeePathPreview();

  // Add a small safety prompt to actions that materially change another employee's task.
  $$('form[data-confirm]').forEach(form => form.addEventListener('submit', event => {
    const message = form.dataset.confirm || '';
    if (message && !window.confirm(message)) event.preventDefault();
  }));

  // Fade transient notifications without any external JS dependency.
  setTimeout(() => $$('.toast-stack .toast').forEach(t => { t.style.opacity='0'; t.style.transform='translateY(-4px)'; setTimeout(()=>t.remove(), 250); }), 4500);
})();
