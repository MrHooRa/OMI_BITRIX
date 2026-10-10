(() => {
  'use strict';
  const I = window.DIWAN_I18N || {};
  const t = key => I['d_' + key] || key;
  const $ = selector => document.querySelector(selector);
  const node = (tag, text, className) => {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  };
  const show = (target, text, error = false) => {
    const element = typeof target === 'string' ? $(target) : target;
    if (!element) return;
    element.textContent = text;
    element.classList.toggle('d-error', error);
  };
  const dialog = $('#diwanTokenDialog');
  function openToken() {
    $('#diwanToken').value = '';
    show('#diwanTokenError', '');
    if (!dialog.open) dialog.showModal();
  }
  async function api(url, options = {}) {
    const response = await fetch(url, {headers: {'Content-Type': 'application/json'}, ...options});
    let data;
    try { data = await response.json(); }
    catch (_) { throw new Error(t('error_invalid_response')); }
    if (!response.ok || data.ok === false) {
      if (data.code === 'token_invalid' || data.code === 'token_required') openToken();
      throw new Error(data.error || t('error_source_unavailable'));
    }
    return data;
  }
  const post = (url, payload = {}) => api(url, {method: 'POST', body: JSON.stringify(payload)});
  async function action(button, target, fn) {
    button.disabled = true;
    show(target, t('working'));
    try { await fn(); }
    catch (error) { show(target, error.message, true); }
    finally { button.disabled = false; }
  }
  document.querySelectorAll('[data-token-open]').forEach(button => button.addEventListener('click', openToken));
  document.querySelectorAll('[data-close-dialog]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
  dialog?.addEventListener('close', () => {
    $('#diwanToken').value = '';
    $('#diwanToken').type = 'password';
    $('#diwanTokenShow').setAttribute('aria-pressed', 'false');
  });
  $('#diwanTokenShow')?.addEventListener('click', event => {
    const field = $('#diwanToken');
    field.type = field.type === 'password' ? 'text' : 'password';
    event.currentTarget.setAttribute('aria-pressed', String(field.type === 'text'));
  });
  $('#diwanTokenForm')?.addEventListener('submit', event => {
    event.preventDefault();
    action(event.submitter, '#diwanTokenError', async () => {
      await post('/api/diwany/token', {token: $('#diwanToken').value});
      $('#diwanToken').value = '';
      location.reload();
    });
  });

  function table(headers, rows) {
    const wrap = node('div', undefined, 'd-table-wrap');
    const result = node('table', undefined, 'd-table');
    const head = node('thead'), hr = node('tr'), body = node('tbody');
    headers.forEach(label => { const th = node('th', label); th.scope = 'col'; hr.append(th); });
    head.append(hr);
    rows.forEach(values => {
      const row = node('tr');
      values.forEach(value => {
        const cell = node('td');
        cell.append(value instanceof Node ? value : document.createTextNode(String(value ?? '—')));
        row.append(cell);
      });
      body.append(row);
    });
    result.append(head, body); wrap.append(result);
    return wrap;
  }
  function renderEstimate(value) {
    const section = node('section', undefined, 'd-note');
    section.append(node('h3', t('estimate')));
    section.append(node('p', value.available
      ? value.median + ' ' + t('hours') + ' (' + value.low + '–' + value.high + ')'
      : t('insufficient')));
    section.append(node('p', t('samples') + ': ' + value.samples), node('small', t('elapsed_help')));
    return section;
  }
  async function poll(job, target) {
    for (;;) {
      const data = await api('/api/diwany/jobs/' + job);
      show(target, t('pages') + ': ' + data.job.pages + ' · ' + t('count') + ': ' + data.job.count);
      if (data.job.status !== 'running') {
        if (data.job.error) {
          if (data.job.error === 'token_invalid') openToken();
          throw new Error(t('error_' + data.job.error));
        }
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  let page = 1, currentJob = '', detailId = '';
  async function list() {
    const q = $('#diwanSearch').value;
    const data = await api('/api/diwany/tasks?page=' + page + '&q=' + encodeURIComponent(q));
    const target = $('#diwanRows'); target.replaceChildren();
    if (!data.records.length) target.append(node('p', t('empty'), 'd-pad'));
    else target.append(table([...data.columns.map(column => column.label), ''],
      data.records.map(row => {
        const button = node('button', t('details'), 'btn secondary');
        button.addEventListener('click', () => action(button, '#diwanProgress', () => details(row.id)));
        return [...row.display_values, button];
      })));
    show('#diwanCount', t('count') + ': ' + data.total);
    show('#diwanPageNumber', String(page));
    $('#diwanPrev').disabled = page <= 1;
    $('#diwanNext').disabled = page * 50 >= data.total;
    if (!currentJob) {
      show('#diwanProgress', (data.coverage.complete ? t('complete') : t('partial')) +
        ' · ' + (data.coverage.updated_at || '—') +
        (data.coverage.error ? ' · ' + t('error_' + data.coverage.error) : ''),
        Boolean(data.coverage.error));
    }
  }
  async function details(id) {
    const data = await api('/api/diwany/tasks/' + encodeURIComponent(id));
    detailId = id;
    $('#diwanDetailTitle').textContent = data.task.title + ' · ' + id;
    const target = $('#diwanDetailBody'); target.replaceChildren();
    const facts = node('dl', undefined, 'd-facts');
    [[t('request_id'), data.task.request_id], [t('status'), data.task.status_label],
      ...data.task.fields.map(field => [field.label, typeof field.value === 'object' ? JSON.stringify(field.value, null, 2) : field.value])]
      .forEach(([label, value]) => facts.append(node('dt', label), node('dd', String(value ?? ''))));
    target.append(facts, node('h3', t('workflow')));
    data.task.actions.forEach(value => target.append(node('pre', JSON.stringify(value, null, 2), 'd-raw')));
    show('#delegationStatus', '');
    $('#diwanDetail').showModal();
  }
  if ($('#diwanPage')) {
    list().catch(error => show('#diwanProgress', error.message, true));
    if ($('#diwanPage').dataset.connected !== '1') openToken();
    $('#diwanFilters').addEventListener('submit', event => {
      event.preventDefault();
      action(event.submitter, '#diwanProgress', async () => {
        const data = await post('/api/diwany/sync', Object.fromEntries(new FormData(event.target)));
        currentJob = data.job_id; $('#diwanCancel').hidden = false;
        try { await poll(currentJob, '#diwanProgress'); }
        finally { currentJob = ''; $('#diwanCancel').hidden = true; page = 1; await list(); }
      });
    });
    $('#diwanCancel').addEventListener('click', () => {
      if (currentJob) api('/api/diwany/jobs/' + currentJob, {method:'DELETE'}).catch(error => show('#diwanProgress', error.message, true));
    });
    let searchTimer;
    $('#diwanSearch').addEventListener('input', () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => { page = 1; list().catch(error => show('#diwanProgress', error.message, true)); }, 250);
    });
    $('#diwanPrev').addEventListener('click', () => { page--; list().catch(error => show('#diwanProgress', error.message, true)); });
    $('#diwanNext').addEventListener('click', () => { page++; list().catch(error => show('#diwanProgress', error.message, true)); });
    $('#delegateForm').addEventListener('submit', event => {
      event.preventDefault();
      if (!confirm(t('confirm_delegate'))) return;
      const recipient = new FormData(event.target).get('recipient');
      action(event.submitter, '#delegationStatus', async () => {
        await post('/api/diwany/tasks/' + encodeURIComponent(detailId) + '/delegate', {recipient, confirmed:true});
        show('#delegationStatus', t('saved')); await list();
      });
    });
    $('#reconcileDelegation').addEventListener('click', event => action(event.currentTarget, '#delegationStatus', async () => {
      await post('/api/diwany/tasks/' + encodeURIComponent(detailId) + '/reconcile');
      show('#delegationStatus', t('saved')); await list();
    }));
  }

  const localTime = value => value ? new Date(value).toLocaleString(window.WC_LANG || 'en') : '—';
  let analysisRequest = 0;
  window.addEventListener('analysis-reset', () => { analysisRequest++; });
  async function runAnalysis(payload) {
    const requestId = ++analysisRequest;
    window.dispatchEvent(new CustomEvent('workspace-panel', {detail: 'analysisPanel'}));
    window.dispatchEvent(new CustomEvent('analysis-start', {detail: payload}));
    $('#previewRankResults')?.replaceChildren(node('p', t('working'), 'rec-empty'));
    const target = $('#analysisResults'); target.replaceChildren(node('p', t('working')));
    let data;
    try { data = await post('/api/intelligence/analyze', payload); }
    catch (error) {
      if (requestId !== analysisRequest) return;
      target.replaceChildren(node('p', error.message, 'd-error'));
      $('#previewRankResults').replaceChildren(node('p', error.message, 'd-error'));
      window.dispatchEvent(new CustomEvent('analysis-related', {detail: {count: '—', text: payload.text || $('#analysisQuery').value}}));
      window.dispatchEvent(new CustomEvent('recommendation-results', {detail: {error: true}}));
      throw error;
    }
    if (requestId !== analysisRequest) return;
    const result = data.result; target.replaceChildren();
    const coverage = data.coverage[payload.source];
    if (!coverage.complete || coverage.error) target.append(node('p', t('history_incomplete'), 'd-error'));
    const groups = result.related_groups || result.related;
    if (!groups.length) {
      const empty = node('div', undefined, 'ui-empty');
      empty.append(node('h2', window.UI_I18N.no_related), node('p', window.UI_I18N.no_related_help)); target.append(empty);
    } else {
      const grid = node('div', undefined, 'ui-related-grid');
      groups.forEach(item => {
        const card = node('article', undefined, 'ui-related-task'), header = node('header');
        const relevance=node('span',item.score+'%','ui-score');relevance.title=t('relevance');relevance.setAttribute('aria-label',t('relevance')+' '+item.score+'%');
        header.append(node('h3', item.task.title), relevance);
        const duplicates = item.duplicate_tasks || [{id:item.task.id, assignee:item.task.assignee_name || item.task.assignee_id}];
        card.append(header, node('p',item.task.source+' · '+t(item.task.completed?'completed_evidence':'open_evidence'),'help'), node('p', t('recipients') + ': ' + [...new Set(duplicates.map(row => row.assignee).filter(Boolean))].join(' / ')));
        card.append(node('p', t('shared_terms') + ': ' + item.shared_terms.join(' · ')));
        const evidence = node('details'); evidence.append(node('summary', t('details') + ' · ' + duplicates.length));
        duplicates.forEach(row => {
          const link = node('a', '#' + row.id + ' · ' + (row.assignee || item.task.assignee_name || '—'), 'rec-example');
          link.href = '#evidence-' + encodeURIComponent(row.id);
          link.addEventListener('click', event => { event.preventDefault(); window.dispatchEvent(new CustomEvent('task-evidence', {detail: {id:row.id, source:item.task.source || payload.source}})); });
          evidence.append(link);
        });
        card.append(evidence); grid.append(card);
      }); target.append(grid);
    }
    if (result.related_groups?.some(item => item.duplicate_tasks.length > 1)) target.append(node('p', t('grouped_duplicates'), 'help'));
    const context = $('#analysisContext'), detail = node('details', undefined, 'ui-disclosure');
    detail.append(node('summary', window.UI_I18N.context), node('p', t('category') + ': ' + (result.category || t('insufficient'))), renderEstimate(result.estimate));
    context.replaceChildren(detail);
    window.dispatchEvent(new CustomEvent('analysis-understanding', {detail: result}));
    window.dispatchEvent(new CustomEvent('analysis-related', {detail: {count: groups.length, text: result.query_text}}));
    window.dispatchEvent(new CustomEvent('task-analysis', {detail: {source: payload.source, text: result.query_text, category: payload.category || result.category || '', project_id: result.project_id || payload.project_id, exclude_id: result.exclude_id}}));
    show('#analysisStatus', '');
  }
  function similarButton(row) {
    const button = node('button', t('find_similar'), 'btn secondary');
    button.type = 'button';
    button.addEventListener('click', () => action(button, '#analysisStatus', async () => {
      $('#analyzeForm [name="source"]').value = row.source;
      $('#analyzeForm [name="text"]').value = row.title;
      await runAnalysis({source: row.source, task_id: row.id});
      window.dispatchEvent(new CustomEvent('result-panel', {detail:'analysisResults'}));
      $('#analysisResultWorkspace').scrollIntoView({behavior: 'smooth', block: 'start'});
    }));
    return button;
  }
  let historyPage=1;
  let intelligenceLoading = false, historyReloadPending = false;
  let intelligenceVersion = "";
  async function loadIntelligence(evaluate = false) {
    if (intelligenceLoading) return;
    intelligenceLoading = true;
    try {
      const source=$('#workspaceSource').value;
      const params=new URLSearchParams({page:String(historyPage),q:$('#historySearch').value,source});
      if($('#similarityExamples').open)params.set('pairs','1');
      if(evaluate)params.set('evaluate','1');
      const data = await api('/api/intelligence?' + params);
      if(source!==$('#workspaceSource').value)return;
      $('#historyPrev').disabled=historyPage===1;$('#historyNext').disabled=historyPage*50>=data.filtered_total;
      $('#historyPage').textContent=historyPage+' / '+Math.max(1,Math.ceil(data.filtered_total/50));
      const diagnostics=$('#qualityDiagnostics');diagnostics.replaceChildren();
      const qualitySources=Object.keys(data.quality);const qualityKeys=Object.keys(data.quality[qualitySources[0]] || {});
      diagnostics.append(table([t('quality_title'),...qualitySources],qualityKeys.map(key=>[t('quality_'+key),...qualitySources.map(source=>String(data.quality[source][key]??'—'))])));
      const coverage = $('#historyCoverage'); coverage.replaceChildren();
      Object.entries(data.coverage).forEach(([source, value]) => {
        const schedule = value.schedule;
        const running = schedule.job?.status === 'running';
        const status = !schedule.enabled ? t('not_connected') : running ? t('working') : value.complete ? t('complete') : t('partial');
        const message = source + ' · ' + status + ' · ' + value.count + ' ' + t('records') +
          ' · ' + t('last_refresh') + ': ' + localTime(value.updated_at) +
          (schedule.enabled ? ' · ' + t('next_refresh') + ': ' + localTime(schedule.next_run_at) : '');
        coverage.append(node('p', message, 'd-note'));
        if (value.error || schedule.error || value.index_error) coverage.append(node('p', t('error_' + (value.error || schedule.error || value.index_error)), 'd-error'));
        else if (value.complete && value.count && !value.index_ready) coverage.append(node('p', t('preparing_history'), 'help'));
      });
      const version = JSON.stringify([source,Boolean($('#similarityExamples').open),historyPage,$('#historySearch').value,Object.values(data.coverage).map(value => [value.updated_at, value.count, value.index_ready])]);
      if (version !== intelligenceVersion) {
      intelligenceVersion = version;
      const pairs = $('#similarityPairs'); pairs.replaceChildren();
      if (!data.pairs.length) pairs.append(node('p', t('no_pairs')));
      else pairs.append(table([t('source'), t('tasks_analysis'), t('related'), t('relevance'), t('find_similar')],
        data.pairs.map(pair => [pair.task.source, '#' + pair.task.id + ' ' + pair.task.title,
          '#' + pair.match.task.id + ' ' + pair.match.task.title, pair.match.score + '%', similarButton(pair.task)])));
      $('#intelligenceRows').replaceChildren(node('h2', t('historical_tasks')), node('p', data.records.length + ' / ' + data.filtered_total + ' · ' + t('display_limit'), 'help'),
        table([t('source'), t('task_id'), t('tasks_analysis'), t('recipients'), t('priority'),t('sla_deadline'),t('find_similar')],
          data.records.map(row => [row.source, row.id, row.title, row.assignee_name || row.assignee_id, String(row.effective_priority),row.sla_deadline?localTime(row.sla_deadline)+(row.sla_late?' · '+t('sla_overdue'):''):'—',similarButton(row)])));
      }
      if (data.evaluation) {
        const target = $('#historyEvaluation'); target.replaceChildren(node('h3', t('evaluation')));
        target.append(node('p', t('evaluation_help')), node('pre', JSON.stringify(data.evaluation, null, 2), 'd-raw'));
      }
    } finally { intelligenceLoading = false; if(historyReloadPending){historyReloadPending=false;loadIntelligence().catch(error=>show('#historyProgress',error.message,true));} }
  }
  if ($('#intelligencePage')) {
    $('#historyPrev').addEventListener('click',()=>{historyPage=Math.max(1,historyPage-1);loadIntelligence().catch(error=>show('#historyProgress',error.message,true));});
    $('#historyNext').addEventListener('click',()=>{historyPage++;loadIntelligence().catch(error=>show('#historyProgress',error.message,true));});
    let historySearchTimer;$('#historySearch').addEventListener('input',()=>{clearTimeout(historySearchTimer);historySearchTimer=setTimeout(()=>{historyPage=1;loadIntelligence().catch(error=>show('#historyProgress',error.message,true));},250);});
    const reloadHistory=()=>{if(intelligenceLoading){historyReloadPending=true;return;}loadIntelligence().catch(error=>show('#historyProgress',error.message,true));};
    window.addEventListener('workspace-source',()=>{historyPage=1;intelligenceVersion='';$('#intelligenceRows').replaceChildren();$('#similarityPairs').replaceChildren();if(!$('#historyPanel').hidden)reloadHistory();});
    window.addEventListener('workspace-panel-selected',event=>{if(event.detail==='historyPanel')reloadHistory();});
    $('#similarityExamples').addEventListener('toggle',()=>{if($('#similarityExamples').open)reloadHistory();});
    setInterval(() => {
      if (!document.hidden && !$('#historyPanel').hidden) loadIntelligence().catch(error => show('#historyProgress', error.message, true));
    }, 60000);
    $('#bitrixHistory').addEventListener('click', event => action(event.currentTarget, '#historyProgress', async () => {
      const data = await post('/api/history/sync', {source: $('#analyzeForm [name="source"]').value});
      try { await poll(data.job_id, '#historyProgress'); }
      finally { await loadIntelligence(); }
    }));
    $('#evaluateHistory').addEventListener('click', event => action(event.currentTarget, '#historyProgress', () => loadIntelligence(true)));
    $('#analyzeForm').addEventListener('submit', event => {
      event.preventDefault();
      action(event.submitter, '#analysisStatus', () => runAnalysis(Object.fromEntries(new FormData(event.target))));
    });
  }

  function field(label, value = '', type = 'text') {
    const wrap = node('label', label), input = node('input');
    input.type = type; input.value = value; wrap.append(input);
    return [wrap, input];
  }
  function selectField(label, options, value) {
    const wrap = node('label', label), input = node('select');
    options.forEach(([key, text]) => { const option = node('option', text); option.value = key; input.append(option); });
    input.value = value; wrap.append(input); return [wrap, input];
  }
  function employeeRow(value = {}) {
    const row = node('div', undefined, 'd-employee d-grid');
    const controls = {};
    [['value','identifier'],['name_en','name_en'],['name_ar','name_ar'],['away_from','away_from'],['away_to','away_to']]
      .forEach(([key, label]) => {
        const [wrap, input] = field(t(label), value[key], key.startsWith('away') ? 'date' : 'text');
        controls[key] = input; row.append(wrap);
      });
    const [wrap, select] = selectField(t('source'), [['diwan', t('diwan')], ['bitrix', 'Bitrix24']], value.source || 'diwan');
    controls.source = select; row.append(wrap);
    const remove = node('button', t('remove'), 'btn secondary');
    remove.type = 'button'; remove.addEventListener('click', () => row.remove()); row.append(remove);
    row.read = () => Object.fromEntries(Object.entries(controls).map(([key, input]) => [key, input.value]));
    $('#employeeRows').append(row);
  }
  function ruleRow(target, key = '', value = 0, priority = false) {
    const row = node('div', undefined, 'd-rule');
    const [keyWrap, keyInput] = field(t(priority ? 'tag' : 'category'), key);
    if (priority) keyInput.setAttribute('list', 'diwanTagOptions');
    const [valueWrap, valueInput] = field(t(priority ? 'priority' : 'sla_target'), value, 'number');
    valueInput.min = '0'; valueInput.max = priority ? '3' : '2000'; valueInput.step = priority ? '1' : '0.5';
    const remove = node('button', t('remove'), 'btn secondary'); remove.type = 'button';
    remove.addEventListener('click', () => row.remove());
    row.append(keyWrap, valueWrap, remove);
    row.read = () => [keyInput.value.trim(), Number(valueInput.value)];
    $(target).append(row);
  }
  if ($('#connectionsPage')) {
    async function loadColumns() {
      const result = await api('/api/diwany/columns');
      const selected = new Map(result.selected.map(column => [column.key, column.label]));
      const choices = new Map(result.available.map(column => [column.key, column]));
      result.selected.forEach(column => { if (!choices.has(column.key)) choices.set(column.key, column); });
      const rows = $('#diwanColumnRows'); rows.replaceChildren();
      const ordered = [...result.selected.map(column => choices.get(column.key)), ...[...choices.values()].filter(column => !selected.has(column.key))];
      ordered.forEach(column => {
        const row = node('div', undefined, 'd-column-choice');
        const label = node('label'), checkbox = node('input');
        checkbox.type = 'checkbox'; checkbox.value = column.key; checkbox.checked = selected.has(column.key);
        label.append(checkbox, document.createTextNode(column.label || column.key));
        const name = node('input'); name.value = selected.get(column.key) || ''; name.maxLength = 80;
        name.placeholder = t('column_label'); name.setAttribute('aria-label', t('column_label') + ': ' + column.key);
        row.dataset.columnKey = column.key;
        row.append(label, name); rows.append(row);
      });
      show('#diwanColumnsStatus', result.has_json_fields ? '' : t('columns_fetch_hint'));
    }
    loadColumns().catch(error => show('#diwanColumnsStatus', error.message, true));
    $('#diwanColumnsRefresh').addEventListener('click', event => action(event.currentTarget, '#diwanColumnsStatus', loadColumns));
    $('#diwanColumnsForm').addEventListener('submit', event => {
      event.preventDefault();
      const columns = [...$('#diwanColumnRows').children].filter(row => row.querySelector('[type=checkbox]').checked)
        .map(row => ({key: row.dataset.columnKey, label: row.querySelector('input:not([type=checkbox])').value.trim()}));
      action(event.submitter, '#diwanColumnsStatus', async () => { await post('/api/diwany/columns', {columns}); show('#diwanColumnsStatus', t('saved')); });
    });
    $('#diwanColumnSearch').addEventListener('input', event => {
      const query = event.target.value.trim().toLocaleLowerCase();
      [...$('#diwanColumnRows').children].forEach(row => { row.hidden = !row.textContent.toLocaleLowerCase().includes(query); });
    });
    const data = JSON.parse($('#connectionData').textContent);
    const tagOptions = node('datalist'); tagOptions.id = 'diwanTagOptions'; document.body.append(tagOptions);
    api('/api/intelligence/tags').then(result => result.tags.forEach(tag => {
      const option = node('option'); option.value = tag; tagOptions.append(option);
    })).catch(() => {});
    data.employees.forEach(employeeRow);
    Object.entries(data.settings.tag_priorities || {}).forEach(([key, value]) => ruleRow('#priorityRules', key, value, true));
    Object.entries(data.settings.sla_hours || {}).forEach(([key, value]) => ruleRow('#slaRules', key, value));
    $('#addEmployee').addEventListener('click', () => employeeRow());
    $('#saveEmployees').addEventListener('click', event => action(event.currentTarget, '#employeeStatus', async () => {
      await post('/api/diwany/employees', {employees:[...$('#employeeRows').children].map(row => row.read())});
      window.dispatchEvent(new Event('employees-saved'));
      show('#employeeStatus', t('saved'));
    }));
    $('#addPriority').addEventListener('click', () => ruleRow('#priorityRules', '', 0, true));
    $('#addSla').addEventListener('click', () => ruleRow('#slaRules'));
    $('#endpointForm').addEventListener('submit', event => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(event.target));
      data.roles_confirmed = event.target.elements.roles_confirmed.checked;
      data.delegation_confirmed = event.target.elements.delegation_confirmed.checked;
      action(event.submitter, '#endpointStatus', async () => {
        await post('/api/diwany/config', data); location.reload();
      });
    });
    $('#removeDiwanToken')?.addEventListener('click', event => {
      if (!confirm(t('confirm_remove'))) return;
      action(event.currentTarget, '#endpointStatus', async () => {
        await api('/api/diwany/token', {method:'DELETE'}); location.reload();
      });
    });
    $('#analysisSettingsForm').addEventListener('submit', event => {
      event.preventDefault();
      const data = new FormData(event.target);
      const readRules = target => Object.fromEntries([...$(target).children].map(row => row.read()).filter(([key]) => key));
      action(event.submitter, '#rulesStatus', async () => {
        await post('/api/intelligence/settings', {
          start_hour:Number(data.get('start_hour')), end_hour:Number(data.get('end_hour')),
          working_days:data.getAll('working_days').map(Number),
          holidays:String(data.get('holidays')).split(/\s+/).filter(Boolean),
          tag_priorities:readRules('#priorityRules'), sla_hours:readRules('#slaRules')
        });
        show('#rulesStatus', t('saved'));
      });
    });
  }
})();
