(() => {
  'use strict';
  const u = key => window.UI_I18N?.[key] || key;
  const t = key => window.DIWAN_I18N?.['d_r_' + key] || key;
  const sourceName = source => source === 'bitrix' ? 'Bitrix24' : (window.DIWAN_I18N?.d_diwan || 'Diwan');
  const localDate = value => { if(!value)return '—'; const d=new Date(value); return Number.isNaN(d.getTime()) ? value : d.toLocaleString(document.documentElement.lang || 'en'); };
  const $ = selector => document.querySelector(selector);
  const node = (tag, text, cls) => {
    const result = document.createElement(tag);
    if (text !== undefined) result.textContent = text;
    if (cls) result.className = cls;
    return result;
  };
  let currentSource = new URLSearchParams(location.search).get('source') || $('#workspaceSource')?.value || 'bitrix';
  if (!['bitrix','diwan'].includes(currentSource)) currentSource='bitrix';
  async function api(path, data, source=currentSource) {
    const response = await fetch('/api/recommendations' + path + (path.includes('?')?'&':'?') + 'source=' + encodeURIComponent(source), data === undefined ? {} : {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
    });
    const body = await response.json();
    if (!response.ok || body.ok === false) throw new Error(body.error || t('stale'));
    return body;
  }
  const onPage = Boolean($('#recommendationPage'));
  let rankRequest = 0, previewEpoch = 0;
  let snapshot, snapshotLinkLoaded = false, policyLoaded = false, busy = false;
  function status(text, error = false) {
    const target = $('#recommendationStatus');
    if (target) { target.textContent = text; target.classList.toggle('d-error', error); }
  }
  async function action(button, operation) {
    button.disabled = true; busy = true; status(t('working'));
    try { await operation(); if ($('#recommendationStatus')?.textContent === t('working')) status(''); }
    catch (error) { if(onPage){try{await load();}catch{/* Preserve the original action error. */}} status(error.message, true); }
    finally { busy = false; button.disabled = false; }
  }
  function button(label, operation) {
    const result = node('button', label, 'btn secondary'); result.type = 'button';
    result.addEventListener('click', () => action(result, operation)); return result;
  }
  function field(label, value, type = 'text') {
    const wrap = node('label', label), input = node('input'); input.type = type;
    if (type === 'checkbox') input.checked = Boolean(value); else input.value = value ?? '';
    wrap.append(input); return {wrap, input};
  }
  const employeeRows = [];
  function employeeEditor(employee) {
    const block = node('fieldset'); block.append(node('legend', employee.name || t('add_employee')));
    const fields = {};
    [['id', 'id'], ['name', 'name'], ['enabled', 'enabled', 'checkbox'], ['active', 'employee_active', 'checkbox'],
      ['projects', 'projects'], ['categories', 'categories'], 
      ['away_from', 'away_from', 'date'], ['away_to', 'away_to', 'date']].forEach(([key, label, type]) => {
      const value = Array.isArray(employee[key]) ? employee[key].join(', ') : employee[key];
      const entry = field(t(label), value, type);
      if(key==='id' && employee.id)entry.input.readOnly=true;
      if(key==='projects'){
        const select=node('select');select.multiple=true;select.size=Math.min(5,Math.max(2,snapshot.projects.length));
        snapshot.projects.forEach(p=>{const option=new Option(p.name,p.id);option.selected=(employee.projects || []).includes(p.id);select.append(option);});
        entry.input.replaceWith(select);entry.input=select;
      }
      fields[key] = entry.input; block.append(entry.wrap);
    });
    block.classList.add('d-grid'); $('#recommendationEmployees').append(block); employeeRows.push(fields);
  }
  const split = value => value.split(/[,،]/).map(x => x.trim()).filter(Boolean);
  function loadPolicy(data) {
    $('#recommendationPolicy').hidden=currentSource==='diwan';
    $('#diwanPolicyHelp').hidden=currentSource!=='diwan';
    if (policyLoaded) return;
    policyLoaded = true;
    const policy = data.policy;
    document.querySelectorAll('[data-field-map]').forEach(input=>input.value=policy.data_fields?.[input.dataset.fieldMap] || '');
    if(currentSource==='bitrix')api('/fields').then(data=>{const list=$('#sourceFieldOptions');list.replaceChildren();data.fields.forEach(field=>list.append(new Option(field.name,field.id)));}).catch(()=>{});
    $('#recommendationCategoryField').value = policy.category_field || '';
    $('#recommendationTopN').value = policy.top_n;
    $('#weightSimilarity').value = policy.weights.similarity;
    $('#weightExperience').value = policy.weights.experience;
    $('#weightCapacity').value = policy.weights.capacity;
    $('#recommendationEmployees').replaceChildren(); employeeRows.length = 0;
    data.employees.forEach(employeeEditor);
  }
  const format = (key, values) => t(key).replace(/\{(\w+)\}/g, (_, name) => String(values[name] ?? ''));
  function suggestionText(item) {
    const suggestion = item?.suggestion;
    if (suggestion?.status === 'ready') {
      return format('auto_candidate', {name:suggestion.employee.name}) + ' · ' +
        format('auto_reason', {completed:suggestion.reason.similar_completed,active:suggestion.reason.active_tasks});
    }
    return t('auto_' + (suggestion?.status || 'pending'));
  }
  function appendSuggestion(card, item) {
    if(item.state !== 'needs_assignment')return;
    const summary=node('div',undefined,'rec-auto-suggestion');
    const suggestion=item.suggestion;
    if(suggestion?.status==='ready'){
      summary.append(node('strong',format('auto_candidate',{name:suggestion.employee.name})));
      summary.append(node('p',format('auto_reason',{completed:suggestion.reason.similar_completed,active:suggestion.reason.active_tasks}),'rec-auto-reason'));
    }else summary.append(node('p',suggestionText(item),'rec-auto-reason'));
    if(suggestion?.status==='ready' && suggestion.reason.evidence?.length){
      const evidence=suggestion.reason.evidence[0];
      const proof=node('a',t('primary_evidence')+' · #'+evidence.id+' · '+evidence.title,'rec-example');
      proof.href='#evidence-'+encodeURIComponent(evidence.id);
      proof.addEventListener('click',event=>{event.preventDefault();showEvidence(evidence.id,evidence.source || currentSource);});
      summary.append(proof);
      if(suggestion.reason.evidence_patterns<2)summary.append(node('p',t('limited'),'rec-caption'));
    }
    card.append(summary);
  }
  async function load() {
    const loadingSource=currentSource;
    const data = await api(onPage ? '' : '?summary=1');
    if (loadingSource!==currentSource)return;
    let unread = data.unread || 0, firstAlert = data.alert;
    let pending = firstAlert?.suggestion?.status === 'pending';
    if(!onPage){
      const diwan=await api('?summary=1',undefined,'diwan');unread+=diwan.unread || 0;firstAlert ||= diwan.alert;pending ||= diwan.alert?.suggestion?.status === 'pending';
      if(!data.unread && diwan.unread){['#recommendationAlert','#recommendationBadge'].forEach(id=>{const link=$(id)?.closest('a');if(link)link.href='/tasks?view=assignments&source=diwan';});}
    }
    const badge = $('#recommendationBadge'); if (badge) badge.textContent = unread ? String(unread) : '';
    const alert = $('#recommendationAlert');
    if (alert) {
      alert.hidden = onPage || !unread;
      alert.textContent = t('alert') + ': ' + unread + (firstAlert ? ' · #'+firstAlert.id+' · '+firstAlert.title+' — '+suggestionText(firstAlert) : '');
      if(firstAlert)alert.href='/tasks?view=assignments&source='+firstAlert.source+'&task='+encodeURIComponent(firstAlert.id);
    }
    if (!onPage) { pollSuggestions(pending);return; }
    const previousSnapshot = snapshot;
    snapshot = data;
    $('#analyzeForm button').disabled = !data.configured;
    if (!data.configured) { $('#recommendationCoverage').textContent='';$('#taskDecisionActions').hidden=true;status(t(currentSource==='diwan'?'diwan_setup':'not_connected'), true); $('#recommendationInbox').replaceChildren();$('#recommendationTask').replaceChildren();$('#recommendationForm button[type=submit]').disabled=true;$('#queueCount').textContent='0';$('#assignmentTabCount').textContent='';return; }
    $('#queueCount').textContent = data.notifications.length;
    $('#recommendationCoverage').textContent = t('checked') + ': ' + (data.checked_at ? new Date(data.checked_at).toLocaleString(window.WC_LANG) : '—') +
      ' · ' + t('evidence') + ': ' + data.completed_evidence + ' · ' + t('cadence');
    if (data.error || !data.history_ready) status(t(data.error === 'directory_unavailable' ? 'status_directory_unavailable' : 'stale'), true);
    else if (!busy) status('');
    $('#assignmentTabCount').textContent = data.notifications.length || '';
    const selected = $('#recommendationTask').value;
    const oldTask = previousSnapshot?.tasks?.find(row=>row.id===selected);
    $('#recommendationTask').replaceChildren(new Option(t('select_task'), ''));
    data.tasks.forEach(task => $('#recommendationTask').append(new Option('#' + task.id + ' · ' + task.title + ' · ' + t(task.state), task.id)));
    $('#recommendationTask').value = selected;
    const newTask = data.tasks.find(row=>row.id===selected);
    if(selected && (data.error || !newTask || (oldTask && (oldTask.assignee_id!==newTask.assignee_id || oldTask.creator_id!==newTask.creator_id || oldTask.state!==newTask.state || oldTask.operation?.status!==newTask.operation?.status))))$('#recommendationResults').replaceChildren(node('p',t('refresh_before_assign'),'d-error'));
    const analysisProject = $('#analysisProject');
    if (analysisProject && !analysisProject.options.length) data.projects.forEach(item => analysisProject.append(new Option(item.name, item.id)));
    const project = $('#recommendationProject').value;
    $('#recommendationProject').replaceChildren();
    data.projects.forEach(item => $('#recommendationProject').append(new Option(item.name, item.id)));
    if (project) $('#recommendationProject').value = project;
    window.dispatchEvent(new Event('workspace-snapshot'));
    renderQueue();
    if (!snapshotLinkLoaded && !location.search && !location.hash && data.notifications.length && !document.querySelector('#analyzeForm [name=text]').value) {
      window.dispatchEvent(new CustomEvent('workspace-panel', {detail:'assignmentPanel'}));
    }
    if (!$('#policyPanel').hidden) loadPolicy(data);
    selectionChanged(false);
    if (!snapshotLinkLoaded) {
      snapshotLinkLoaded = true;
      const requested = new URLSearchParams(location.search).get('task');
      if (requested && data.tasks.some(task => task.id === requested)) {
        $('#recommendationTask').value = requested; selectionChanged(); await runRank({task_id: requested});
      }
    }
  }
  function renderQueue() {
    if (!snapshot?.configured) return;
    const inbox = $('#recommendationInbox'); inbox.replaceChildren();
    const search = $('#queueSearch').value.trim().toLocaleLowerCase();
    const rows = ( $('#queueScope').value === 'all' ? snapshot.tasks : snapshot.notifications ).filter(row =>
      (row.id + ' ' + row.title).toLocaleLowerCase().includes(search));
    rows.sort((a,b) => $('#queueSort').value === 'deadline'
      ? (a.deadline || '9999').localeCompare(b.deadline || '9999')
      : Number(b.priority || 0) - Number(a.priority || 0) || (a.deadline || '9999').localeCompare(b.deadline || '9999'));
    if (!rows.length) inbox.append(node('p',t('no_alerts')));
    rows.forEach(item => {
      const card = node('article',undefined,'rec-queue-item');
      card.dataset.task = item.id; card.setAttribute('aria-current', String(item.id === $('#recommendationTask').value));
      card.append(node('span','#' + item.id + ' · ' + t(item.state),'rec-queue-meta'), node('h3',item.title));
      appendSuggestion(card,item);
      card.append(button(t('review_task'),async()=>{
        $('#recommendationTask').value=item.id; selectionChanged();
        await runRank({task_id:item.id}); $('#recommendationResults').scrollIntoView({block:'start',behavior:'smooth'});
      }));
      if (item.state === 'needs_assignment') card.append(button(t('read'),async()=>{await api('/tasks/'+item.id+'/read',{});await load();}));
      inbox.append(card);
    });
  }
  async function showEvidence(id, evidenceSource=currentSource) {
    const target=$('#evidenceContent'); target.replaceChildren(node('p',t('working')));
    $('#evidenceDialog').showModal();
    try {
      const row=(await api('/evidence/'+encodeURIComponent(id), undefined, evidenceSource)).task;
      target.replaceChildren(node('h2',sourceName(evidenceSource)+' · #'+row.id+' · '+row.title),node('p',row.description),
        node('p',t('task_status')+': '+row.status),node('p',t('assignee')+': '+(row.assignee_name || row.assignee_id)),
        node('p',t('deadline')+': '+(row.deadline || '—')),node('p',t('completed_at')+': '+(row.completed_at || '—')));
      if(row.attributes)Object.entries(row.attributes).forEach(([key,value])=>target.append(node('p',t('field_'+key)+': '+(value==null?'—':JSON.stringify(value)))));
    } catch(error) {target.replaceChildren(node('p',error.message,'d-error'));}
  }
  function selectionChanged(clear = true) {
    const task = snapshot?.tasks.find(row => row.id === $('#recommendationTask').value);
    $('#previewFields').hidden = true;
    $('#recommendationForm button[type=submit]').disabled = !task;
    $('#taskDecisionActions').hidden = !task;
    $('#selectedTaskState').hidden = !task;
    if (task) {
      const personName=id=>snapshot.employees.find(e=>e.id===id)?.name || id || '—';
      const facts = node('dl', undefined, 'ui-task-facts');
      [[t('owner'), personName(task.creator_id)], [t('assignee'), personName(task.assignee_id)], [t('deadline'), task.deadline || '—'], [t('priority'), task.priority || 0]].forEach(([label, value]) => facts.append(node('dt',label),node('dd',String(value))));
      $('#taskBrief').replaceChildren(node('h3','#'+task.id+' · '+task.title),node('p',task.description || t('missing_description')),facts);
      $('#selectedTaskState').textContent = t(task.state);
      (task.operation?.warnings || []).forEach(warning=>$('#taskBrief').append(node('p',warning,'d-error')));
      const unresolved = ['pending','uncertain'].includes(task.operation?.status);
      $('#verifyAssignment').hidden = !unresolved;
      $('#releaseUncertain').hidden = task.operation?.status !== 'uncertain';
      $('#claimOwnWork').disabled = unresolved;$('#markNeedsAssignment').disabled = unresolved;
      $('#claimOwnWork').hidden = task.assignee_id !== snapshot.user_id || task.state === 'self_assigned';
    }
    document.querySelectorAll('[data-task]').forEach(card => card.setAttribute('aria-current',String(card.dataset.task === task?.id)));
    if (!task) $('#taskBrief').replaceChildren();
    if (clear) $('#recommendationResults').replaceChildren(node('p', t('start_help'), 'rec-empty'));
  }
  function confirmAction(title, message) {
    const dialog = $('#recommendationConfirm');
    $('#recommendationConfirmTitle').textContent = title;
    $('#recommendationConfirmText').textContent = message;
    return new Promise(resolve => {
      dialog.returnValue = 'cancel';
      dialog.addEventListener('close', () => resolve(dialog.returnValue === 'confirm'), {once: true});
      dialog.showModal();
    });
  }
  const labelName = tag => tag[window.WC_LANG === 'ar' ? 'ar' : 'en'] || tag.id;
  function chips(tags, counts=false) {
    const list=node('ul',undefined,'insight-tags');
    tags.forEach(tag=>list.append(node('li',labelName(tag)+(counts?' · '+tag.count:''))));
    return list;
  }
  function groupedTopics(tags) {
    const wrap=node('div',undefined,'insight-topic-groups');
    ['BUSINESS_DOMAIN','SYSTEM_OR_TOOL','TASK_TYPE','DELIVERABLE_TYPE','CONCEPT'].forEach(kind=>{
      const selected=tags.filter(tag=>tag.type===kind); if(!selected.length)return;
      const group=node('div');group.append(node('h3',t(kind)),chips(selected,selected[0].count!==undefined));wrap.append(group);
    });return wrap;
  }
  let peopleRequest=0, profileRequest=0, returnPanel='peoplePanel';
  function pageControls(page,total,onPage) {
    const wrap=node('div',undefined,'d-toolbar insight-paging');
    const previous=button(window.DIWAN_I18N.d_history_prev,()=>onPage(page-1));previous.disabled=page<=1;
    const next=button(window.DIWAN_I18N.d_history_next,()=>onPage(page+1));next.disabled=page*20>=total;
    wrap.append(previous,node('span',t('page')+' '+page+' / '+Math.max(1,Math.ceil(total/20))),next);return wrap;
  }
  async function loadPeople(page=1) {
    const requestId=++peopleRequest, source=currentSource;
    const form=$('#peopleSearch'), params=new URLSearchParams(new FormData(form));params.set('page',page);
    const target=$('#peopleResults');target.setAttribute('aria-busy','true');
    $('#peopleStatus').textContent=t('working');target.replaceChildren();$('#peoplePaging').replaceChildren();
    try {
      const data=await api('/people?'+params);
      if(requestId!==peopleRequest || source!==currentSource)return;
      $('#peopleStatus').textContent=!data.configured?t(source==='diwan'?'diwan_setup':'not_connected'):
        (data.history_ready && !data.stale?'':t('stale')+' · ')+t('scope_count')+': '+data.total;
      const selected=form.elements.topic.value;
      form.elements.topic.replaceChildren(new Option(t('all_topics'),''));
      (data.topics || []).forEach(tag=>form.elements.topic.append(new Option(labelName(tag),tag.id)));
      form.elements.topic.value=selected;
      if(data.configured && !data.people.length)target.append(node('p',t('people_empty'),'rec-empty'));
      data.people.forEach(person=>{
        const card=node('article',undefined,'insight-person');
        card.append(node('h3',person.name),node('p',t('completed_count')+': '+person.completed_count+' · '+t('open_count')+': '+person.active_count,'rec-caption'));
        if(person.topics.length)card.append(chips(person.topics.slice(0,6),true));else card.append(node('p',t('profile_no_work'),'rec-caption'));
        card.append(button(t('profile'),()=>openProfile(person.id)));target.append(card);
      });
      if(data.total)$('#peoplePaging').append(pageControls(page,data.total,loadPeople));
    } catch(error){if(requestId===peopleRequest && source===currentSource)$('#peopleStatus').textContent=error.message;}
    finally{if(requestId===peopleRequest)target.setAttribute('aria-busy','false');}
  }
  async function loadProfile(id,page=1) {
    const requestId=++profileRequest, source=currentSource, target=$('#employeeProfile');
    target.replaceChildren(node('p',t('working')));target.setAttribute('aria-busy','true');
    try {
      const data=await api('/people?employee='+encodeURIComponent(id)+'&page='+page);
      if(requestId!==profileRequest || source!==currentSource)return;
      const person=data.people[0];target.replaceChildren();
      if(!person){target.append(node('p',t('people_empty')));return;}
      const header=node('header',undefined,'insight-profile-head');
      header.append(node('span',person.name.slice(0,1),'rec-initial'),node('h2',person.name));
      target.append(header);
      if(!data.history_ready || data.stale)target.append(node('p',t('stale'),'d-error'));
      const layout=node('div',undefined,'ui-profile-layout'), main=node('div',undefined,'ui-profile-main');
      const aside=node('aside',undefined,'panel d-pad ui-profile-aside'), counts=node('div',undefined,'ui-profile-counts');
      [[person.completed_count,t('completed_count')],[person.active_count,t('open_count')]].forEach(([value,label])=>{
        const block=node('div');block.append(node('strong',String(value)),node('p',label));counts.append(block);
      });
      aside.append(counts,node('p',t('profile_note'),'rec-caption'),node('p',t('checked')+': '+(data.checked_at?new Date(data.checked_at).toLocaleString(window.WC_LANG):'—'),'rec-caption'));
      const topics=node('section',undefined,'panel d-pad');topics.append(node('h2',u('observed')));
      if(person.topics.length){
        topics.append(chips(person.topics.slice(0,6),true));
        const all=node('details',undefined,'rec-details');all.append(node('summary',u('every_topic')),groupedTopics(person.topics));topics.append(all);
      }else topics.append(node('p',t('profile_no_work')));
      const work=node('section',undefined,'panel d-pad');work.append(node('h2',t('profile_work')));
      const list=node('div',undefined,'ui-work-list'), count=node('p','','ui-history-count');
      const more=button(u('show_more'),async()=>{shown+=6;renderTasks();});let shown=6;
      const renderTasks=()=>{
        list.replaceChildren();person.tasks.slice(0,shown).forEach(row=>{
          const article=node('article',undefined,'rec-queue-item');
          const link=node('a','#'+row.id+' · '+row.title,'rec-example');link.href='#evidence-'+encodeURIComponent(row.id);
          link.addEventListener('click',event=>{event.preventDefault();showEvidence(row.id, row.source || currentSource);});
          article.append(link,node('p',t('completed_at')+': '+(row.completed_at?new Date(row.completed_at).toLocaleDateString(window.WC_LANG):'—'),'rec-caption'));list.append(article);
        });
        count.textContent=u('history_count').replace('{shown}',Math.min(shown,person.tasks.length)).replace('{total}',person.task_total);
        more.hidden=shown>=person.tasks.length;
      };
      if(!person.tasks.length)work.append(node('p',t('profile_no_work')));
      work.append(list,count,more);renderTasks();
      if(person.task_total>20)work.append(pageControls(page,person.task_total,p=>loadProfile(id,p)));
      main.append(topics,work);layout.append(main,aside);target.append(layout);
    } catch(error){if(requestId===profileRequest && source===currentSource)target.replaceChildren(node('p',error.message,'d-error'));}
    finally{if(requestId===profileRequest)target.setAttribute('aria-busy','false');}
  }
  async function openProfile(id) {
    returnPanel=document.querySelector('.workspace-panel:not([hidden])')?.id || 'peoplePanel';
    window.dispatchEvent(new CustomEvent('workspace-panel',{detail:{panel:'employeePanel',employee:id}}));
    $('#employeeBack').focus();
  }
  function renderUnderstanding(result, target) {
    const section=node('details',undefined,'insight-understanding ui-intent');
    section.append(node('summary',t('inferred_topics')),node('p',t('intent_help'),'rec-caption'));
    const profile=result.query_profile;
    if(profile){
      const groups=node('dl',undefined,'ui-intent-groups');
      [['domains','intent_subject'],['tools','intent_tools'],['actions','intent_action'],['deliverables','intent_output']].forEach(([key,label])=>{
        const group=node('div');group.append(node('dt',t(label)));
        const value=node('dd');value.append(profile[key].length?chips(profile[key]):node('span',t('not_detected'),'rec-caption'));group.append(value);groups.append(group);
      });section.append(groups);
      if(profile.status!=='specific')section.append(node('p',t('query_'+profile.status),'ui-query-guidance'));
      else if(!profile.domain_known)section.append(node('p',t('query_unknown_domain'),'rec-caption'));
      if(profile.excluded_labels?.length)section.append(node('p',t('excluded_subjects')+': '+profile.excluded_labels.map(labelName).join('، '),'rec-caption'));
      const learned=profile.labels.filter(tag=>tag.basis==='completed_corpus_association');
      learned.forEach(tag=>section.append(node('p',t('learned_subject')+': '+labelName(tag)+' · '+tag.term+' · '+t('pattern_count')+': '+tag.support,'rec-caption')));
    }else section.append(result.task_labels?.length?chips(result.task_labels):node('p',t('no_labels')));
    const model=node('details',undefined,'rec-details ui-model-note');model.append(node('summary',t('method_title')),node('p',t(result.model?.semantic_status==='ready'?'semantic_method_help':'semantic_unavailable'),'rec-caption'));
    if(result.model?.semantic_status==='ready'&&result.model?.verification_status!=='ready')model.append(node('p',t('verification_unavailable'),'rec-caption'));
    if(result.model?.discovery)section.append(node('p',t('discovered_topics')+': '+(result.model.discovery.topics??0)+' · '+t('topic_provisional'),'rec-caption'));
    if(result.model?.learned_terms>0)model.append(node('p',t('learned_terms')+': '+result.model.learned_terms,'rec-caption'));
    if(result.model?.fitted_documents!==undefined)model.append(node('p',t('model_version')+': '+result.version+' · '+result.model.id+' · '+t('model_documents')+': '+result.model.fitted_documents+' · '+t('model_vocabulary')+': '+result.model.vocabulary_size,'rec-caption'));
    section.append(model);target.replaceChildren(section);
  }
  function candidateRow(candidate, provisional = false, task = null) {
    const card = node('article', undefined, 'rec-candidate');
    const heading = node('div', undefined, 'rec-candidate-head');
    const title = node('div'); title.append(node('h3', candidate.name), node('span', t(candidate.evidence_level), 'rec-caption'));
    heading.append(node('span', candidate.name.slice(0, 1), 'rec-initial'), title);
    if (!provisional && candidate.score != null) heading.append(node('span',t('ranking_label')+': '+Math.round(candidate.score)+' / 100','ui-score'));
    card.append(heading);
    if(candidate.linked_sources?.length>1)card.append(node('p',t('linked_evidence')+': '+candidate.linked_sources.map(sourceName).join(' / '),'rec-caption'));
    const metrics = node('div', undefined, 'rec-metrics');
    metrics.append(node('p', (provisional ? t('open_matches') : t('samples')) + ': ' + (provisional ? candidate.similar_open : candidate.similar_completed)),
      node('p', t('active') + ': ' + candidate.active_tasks)); card.append(metrics);
    if(!provisional && candidate.coverage?.requested.length){
      const domains=candidate.coverage.matched.filter(tag=>tag.type==='BUSINESS_DOMAIN');
      if(domains.length)card.append(node('p',t('subject_evidence')+': '+domains.map(labelName).join('، '),'ui-candidate-reason'));
      card.append(node('p',t('covered'),'insight-small-heading'));
      card.append(candidate.coverage.matched.length?chips(candidate.coverage.matched):node('p',t('no_topic_coverage'),'rec-caption'));
      if(candidate.coverage.missing.length){const missing=node('details',undefined,'rec-details');missing.append(node('summary',t('missing_topics')+' · '+candidate.coverage.missing.length),chips(candidate.coverage.missing));card.append(missing);}
    }
    if(!provisional && candidate.examples.length){
      const first=candidate.examples[0], proof=node('p',t('primary_evidence')+': '+sourceName(first.source || currentSource)+' · #'+first.id+' · '+first.title,'ui-candidate-reason');
      card.append(proof);
    }
    const evidence=node('details',undefined,'rec-details');evidence.append(node('summary',t('why_person')));
    if(!provisional && candidate.evidence_patterns!==undefined)evidence.append(node('p',t('pattern_count')+': '+candidate.evidence_patterns+' · '+t('patterns_help'),'rec-caption'));
    candidate.examples.forEach(example => {
      const link = node('a', (example.source || currentSource) + ' · #' + example.id + ' · ' + example.title, 'rec-example');
      link.href = '#evidence-' + encodeURIComponent(example.id);
      link.addEventListener('click',event=>{event.preventDefault();showEvidence(example.id, example.source || currentSource);});
      link.append(node('small', example.shared_terms?.length ? t('matched_terms') + ': ' + example.shared_terms.join('، ') : t('concept_match')));
      evidence.append(link);
    });card.append(evidence);
    if (!provisional && candidate.score != null) {
      const details = node('details', undefined, 'rec-details'); details.append(node('summary', t('score_details')));
      const breakdown=node('dl',undefined,'ui-score-breakdown');
      Object.entries(candidate.components).forEach(([key,value])=>breakdown.append(node('dt',t(key)),node('dd',String(value))));
      details.append(breakdown,
        node('p',t('retrieval')+': '+candidate.retrieval_similarity+'% · '+t('coverage')+': '+(candidate.coverage?.ratio==null?t('unknown_coverage'):Math.round(candidate.coverage.ratio*100)+'%')),
        node('p',t('coverage_formula'),'rec-caption'));
      card.append(details);
    }
    if(candidate.duration?.available){const elapsed=node('details',undefined,'rec-details');elapsed.append(node('summary',t('elapsed')),node('p',candidate.duration.median+' '+t('hours')+' ('+candidate.duration.low+'–'+candidate.duration.high+') · n='+candidate.duration.samples));card.append(elapsed);}
    const actions=node('div',undefined,'insight-actions');
    actions.append(button(t('profile'),()=>openProfile(candidate.id)));
    if(task && !candidate.reasons){const choose=button(t('choose_candidate'),async()=>assignCandidate(task,candidate.id,candidate.name));choose.className='btn primary';choose.disabled=Boolean(task.assignmentBlocked);choose.title=task.assignmentBlocked?t('refresh_before_assign'):'';actions.append(choose);}
    card.append(actions);return card;
  }
  async function assignCandidate(task, id, name, reason='') {
    const source = currentSource;
    if (!await confirmAction(t('assign'),t('confirm_assign')+'\n#'+task.id+' → '+name)) return;
    if (source !== currentSource || task.assignmentBlocked) throw new Error(t('refresh_before_assign'));
    const result = await api('/tasks/'+task.id+'/assign',{employee_id:id,expected_assignee:task.assignee_id,confirmed:true,reason},source);
    await load();
    const target = $('#recommendationResults');target.replaceChildren(node('p',t('saved')));
    (result.warnings || []).forEach(warning=>target.append(node('p',warning,'d-error')));
  }
  function renderOpenAffinity(result, target) {
    target.replaceChildren(node('h2',t('open_affinity')),node('p',t('open_affinity_help'),'rec-caption'));
    if(!result.open_affinity?.length){target.append(node('p',t('open_affinity_empty'),'rec-empty'));return;}
    const list=node('ol',undefined,'ui-affinity-list');
    result.open_affinity.forEach(person=>{
      const row=node('li'), heading=node('header',undefined,'ui-affinity-heading');
      heading.append(node('h3',person.name),node('span',t('text_match')+': '+person.text_similarity+'%','rec-caption'));row.append(heading);
      row.append(node('p',t('open_matches')+': '+person.similar_open+' · '+t('samples')+': '+person.similar_completed+' · '+t('active')+': '+person.active_tasks,'rec-caption'));
      const periods=person.mentioned_periods.map(period=>{
        const [year,month]=period.split('-');
        const name=new Intl.DateTimeFormat(window.WC_LANG||'en',{month:'long',timeZone:'UTC'}).format(new Date(Date.UTC(2020,Number(month)-1,1)));
        return name+(year==='unspecified'?'':' '+year);
      });
      row.append(node('p',t('mentioned_periods')+': '+(periods.join('، ')||t('not_detected')),'ui-candidate-reason'));
      const evidence=node('details',undefined,'rec-details');evidence.append(node('summary',t('affinity_evidence')),node('p',t('periods_help'),'rec-caption'));
      person.examples.forEach(example=>{
        const ids=example.duplicate_tasks.map(item=>'#'+item.id).join(' / ');
        const item=node('div',undefined,'ui-affinity-evidence');item.append(node('p',ids+' · '+example.title));
        item.append(node('p',t('open_not_completed')+' · '+t('source_status')+': '+(example.status||'—')+' · '+t('source_created')+': '+(example.created_at?new Date(example.created_at).toLocaleString(window.WC_LANG):'—'),'rec-caption'));
        example.duplicate_tasks.forEach(task=>{const link=node('a',t('source_details')+' #'+task.id,'rec-example');link.href='#evidence-'+encodeURIComponent(task.id);link.addEventListener('click',event=>{event.preventDefault();window.dispatchEvent(new CustomEvent('task-evidence',{detail:{id:task.id,source:example.source || currentSource}}));});item.append(link);});evidence.append(item);
      });row.append(evidence,button(t('profile'),()=>openProfile(person.id)));list.append(row);
    });target.append(list);
  }
  async function runRank(payload, target = $('#recommendationResults')) {
    const requestId = String(++rankRequest); target.dataset.request = requestId;
    target.setAttribute('aria-busy', 'true');
    target.replaceChildren(node('p', t('working'), 'rec-empty'));
    const rankingSource=currentSource;
    let result;
    try { result = (await api('/rank', payload)).result; }
    catch (error) { if(target.dataset.request !== requestId || currentSource!==rankingSource)return; target.replaceChildren(node('p', error.message, 'd-error')); if(target.id==='previewRankResults'){$('#openAffinityResults').replaceChildren(node('p',error.message,'d-error'));$('#openAffinityCount').textContent='—';} throw error; }
    finally { if(target.dataset.request === requestId)target.setAttribute('aria-busy', 'false'); }
    if (target.dataset.request !== requestId || currentSource!==rankingSource) return;
    target.replaceChildren();
    if(target.id==='previewRankResults')renderUnderstanding(result,$('#analysisUnderstanding'));

    if(target.id==='previewRankResults'){
      renderOpenAffinity(result,$('#openAffinityResults'));
      $('#openAffinityCount').textContent=String(result.open_affinity?.length||0);
    }
    target.append(node('h2',t('result_title')));
    if(result.evidence_sources?.length)target.append(node('p',t('linked_evidence')+': '+result.evidence_sources.map(s=>sourceName(s.source)+' · '+localDate(s.updated_at)+(s.complete?'':' · '+t('stale'))).join(' / '),'rec-caption'));
    if (result.status_reasons?.length)result.status_reasons.forEach(reason=>target.append(node('p',t('status_'+reason),'d-error')));
    else if (result.stale || !result.history_ready) target.append(node('p', t('stale'), 'd-error'));
    if (!result.candidates.length) target.append(node('p', t('no_completed_match'), 'rec-evidence-notice'));
    const selectedTask = payload.task_id ? snapshot.tasks.find(row => row.id === result.task_id) : null;
    const task = selectedTask ? {...selectedTask, assignmentBlocked: result.stale || ['pending','uncertain'].includes(selectedTask.operation?.status)} : null;
    if (task?.assignmentBlocked) target.append(node('p',t('refresh_before_assign'),'d-error'),button(t('refresh'),async()=>{await api('/refresh',{});await load();await runRank(payload,target);}));
    if(task)target.append(node('p','#'+task.id+' · '+task.title,'rec-caption'));
    const candidateGrid=node('div',undefined,'insight-grid');
    result.candidates.forEach(candidate => candidateGrid.append(candidateRow(candidate,false,task)));target.append(candidateGrid);
    if(result.team?.members.length){
      const team=node('details',undefined,'rec-details insight-team');team.append(node('summary',t('complementary')),node('p',t('complementary_help'),'rec-caption'));
      result.team.members.forEach(member=>{const row=node('div',undefined,'insight-team-member');row.append(button(member.name,()=>openProfile(member.id)),chips(result.task_labels.filter(tag=>member.contributes.includes(tag.id))));team.append(row);});
      if(result.team.missing.length)team.append(node('p',t('missing_topics')),chips(result.team.missing));target.append(team);
    }
    if (!result.open_affinity && result.provisional.length) {
      target.append(node('h3', t('provisional_title')), node('p', t('provisional_help'), 'rec-caption'));
      result.provisional.forEach(candidate => target.append(candidateRow(candidate, true,task)));
    } else if (!result.candidates.length && !result.related_excluded.length && !result.open_affinity?.length) {
      target.append(node('p', result.eligible_count ? t('no_evidence') : t('no_candidates'), 'rec-empty'));
    }
    if (result.related_excluded.length) {
      target.append(node('h3', t('blocked_evidence')), node('p', t('blocked_help'), 'rec-caption'));
      result.related_excluded.forEach(candidate => {
        const card = candidateRow(candidate, !candidate.similar_completed);
        card.append(node('p', candidate.reasons.map(t).join(' · '), 'd-error'));
        card.append(button(t('review_eligibility'), async () => {
          window.dispatchEvent(new CustomEvent('workspace-panel', {detail: 'policyPanel'}));
          $('#rankingPolicy').open = true;
          const row = employeeRows.find(fields => fields.id.value === candidate.id);
          if (row) { row.enabled.focus(); row.enabled.scrollIntoView({block: 'center'}); }
        })); target.append(card);
      });
    }
    if (result.available.length) {
      const other = node('details', undefined, 'rec-details'); other.append(node('summary', t('manual_only') + ' (' + result.available.length + ')'));
      result.available.forEach(person => other.append(node('p', person.name + ' · ' + t('active') + ': ' + person.active_tasks)));
      target.append(other);
    }
    if (task && !task.assignmentBlocked && result.eligible_ids.length) {
      const controls = node('details', undefined, 'rec-assignment'); controls.append(node('summary', t('override')));
      const select = node('select'); select.setAttribute('aria-label', t('override')); select.append(new Option(t('choose_employee'), ''));
      result.eligible_ids.forEach(id => select.append(new Option(snapshot.employees.find(e => e.id === id)?.name || id, id)));
      const reason = field(t('reason'), '');
      controls.append(node('p', t('manual_help'), 'rec-caption'), select, reason.wrap, button(t('assign'), async () => {
        if (!select.value) throw new Error(t('choose_employee'));
        await assignCandidate(task, select.value, select.selectedOptions[0].textContent, reason.input.value);
      })); target.append(controls);
    }
    if (target.id !== 'previewRankResults') {
      const understanding=node('div');renderUnderstanding(result,understanding);target.append(understanding);
      if(result.open_affinity?.length){const open=node('details',undefined,'rec-details');open.append(node('summary',t('open_affinity')));const content=node('div');renderOpenAffinity(result,content);open.append(content);target.append(open);}
    }
    if (target.id==='previewRankResults') window.dispatchEvent(new CustomEvent('recommendation-results',{detail:{count:result.candidates.length}}));
    if (result.excluded.length) {
      const details = node('details', undefined, 'rec-details'); details.append(node('summary', t('excluded')));
      result.excluded.forEach(item => details.append(node('p', item.name + ': ' + item.reasons.map(t).join(' · ')))); target.append(details);
    }
  }
  async function changeSource(value, preserveAnalysis=false) {
    currentSource=value; peopleRequest++;profileRequest++; snapshot=null;policyLoaded=false;snapshotLinkLoaded=false;rankRequest++;
    $('#workspaceSource').value=value;document.querySelector('#analyzeForm [name=source]').value=value;
    ['#recommendationResults','#previewRankResults','#taskBrief','#recommendationInbox','#analysisProject'].forEach(id=>$(id).replaceChildren());
    if(!preserveAnalysis){$('#analysisResults').replaceChildren();window.dispatchEvent(new CustomEvent('analysis-reset'));}
    $('#recommendationCoverage').textContent='';$('#taskDecisionActions').hidden=true;
    document.querySelectorAll('a[data-workspace-view]').forEach(a=>a.href='/tasks?view='+a.dataset.workspaceView+'&source='+value);
    const url=new URL(location.href);url.searchParams.set('source',value);url.searchParams.delete('task');url.searchParams.delete('employee');history.replaceState({},'',url);
    $('#recommendationPolicy').hidden=value==='diwan';$('#diwanPolicyHelp').hidden=value!=='diwan';
    $('#analysisProject').closest('label').hidden=value!=='bitrix';
    window.dispatchEvent(new CustomEvent('workspace-source',{detail:value}));
    await load();
    if(!$('#peoplePanel').hidden)await loadPeople();
    if(!$('#employeePanel').hidden)window.dispatchEvent(new CustomEvent('workspace-panel',{detail:'peoplePanel'}));
  }
  if (onPage) {
    document.querySelectorAll('a[data-workspace-view]').forEach(a=>a.href='/tasks?view='+a.dataset.workspaceView+'&source='+currentSource);
    $('#workspaceSource').value=currentSource;
    document.querySelector('#analyzeForm [name=source]').value=currentSource;
    $('#workspaceSource').addEventListener('change',()=>changeSource($('#workspaceSource').value).catch(error=>status(error.message,true)));
    const panelViews={analysisPanel:'analysis',assignmentPanel:'assignments',historyPanel:'history',decisionsPanel:'decisions',policyPanel:'policy',peoplePanel:'people',employeePanel:'employee'};
    const choosePanel = (id,update=true,employee=null) => {
      if(!panelViews[id]) id='analysisPanel';
      document.querySelectorAll('.workspace-panel').forEach(panel=>{panel.hidden=panel.id!==id;});
      document.querySelectorAll('.workspace-tab').forEach(tab=>tab.setAttribute('aria-pressed',String(tab.dataset.panel===(id==='employeePanel'?'peoplePanel':id))));
      const tool=document.querySelector('.ui-workspace-tools');tool.open=false;
      $('#workspaceToolLabel').textContent=['historyPanel','decisionsPanel','policyPanel'].includes(id)?' · '+document.querySelector('[data-panel='+id+']').textContent:'';
      if(update){const url=new URL(location.href);url.searchParams.set('view',panelViews[id]);if(id==='employeePanel' && employee)url.searchParams.set('employee',employee);else if(id!=='employeePanel')url.searchParams.delete('employee');url.hash='';history.pushState({},'',url);}
      window.dispatchEvent(new CustomEvent('workspace-panel-selected',{detail:id}));
      if(id==='policyPanel' && snapshot?.configured)loadPolicy(snapshot);
      if(id==='decisionsPanel') loadDecisions();
      if(id==='peoplePanel')loadPeople();
      if(id==='employeePanel')loadProfile(new URLSearchParams(location.search).get('employee') || '');
    };
    const restorePanel=()=>{
      const params=new URLSearchParams(location.search);
      const view=location.hash==='#rankingPolicy'?'policy':params.get('view') || (params.has('task')?'assignments':'analysis');
      choosePanel(Object.keys(panelViews).find(k=>panelViews[k]===view),false);
    };
    async function loadDecisions(){
      const target=$('#decisionRows'); target.replaceChildren(node('p',t('working')));
      try{const data=await api('/decisions');target.replaceChildren();
        if(!data.events.length)target.append(node('p',t('no_decisions')));
        data.events.forEach(e=>{const row=node('article',undefined,'rec-queue-item');row.append(node('h3','#'+e.task_id+' · '+t(e.event)),node('p',new Date(e.at).toLocaleString(window.WC_LANG)),node('p',(snapshot?.employees.find(p=>p.id===e.selected_employee)?.name || e.selected_employee || '')+' '+(e.reason || '')));if(e.recommendation?.candidates?.length)row.append(node('p',t('samples')+': '+e.recommendation.candidates.map(c=>(snapshot?.employees.find(p=>p.id===c.id)?.name||c.id)+' ('+(c.similar_completed||0)+')').join(' · '),'rec-caption'));target.append(row);});
      }catch(error){target.replaceChildren(node('p',error.message,'d-error'));}
    }
    $('#peopleSearch').addEventListener('submit',event=>{event.preventDefault();loadPeople();});
    $('#peopleSearch [name=topic]').addEventListener('change',()=>loadPeople());
    $('#employeeBack').addEventListener('click',()=>{profileRequest++;choosePanel(returnPanel);});
    $('#loadDecisions').addEventListener('click',loadDecisions);
    ['#queueSearch','#queueScope','#queueSort'].forEach(id=>$(id).addEventListener('input',renderQueue));
    window.addEventListener('workspace-panel',event=>{const value=event.detail;choosePanel(typeof value==='string'?value:value.panel,true,value.employee);});
    window.addEventListener('popstate',async()=>{
      const requestedUrl=location.href, params=new URLSearchParams(location.search), source=params.get('source') || currentSource;
      if(['bitrix','diwan'].includes(source) && source!==currentSource){
        try {await changeSource(source);history.replaceState({},'',requestedUrl);}catch(error){status(error.message,true);}
      }
      restorePanel();
    });
    document.querySelectorAll('.workspace-tab').forEach(tab=>tab.addEventListener('click',()=>choosePanel(tab.dataset.panel)));
    restorePanel();
    const sourceSelect = document.querySelector('#analyzeForm [name=source]');
    const updateSource = () => {
      $('#analysisProject').closest('label').hidden = sourceSelect.value !== 'bitrix';
      $('#previewRankResults').replaceChildren();
    };
    sourceSelect.addEventListener('change', () => {updateSource();changeSource(sourceSelect.value).catch(error=>status(error.message,true));});
    updateSource();
    window.addEventListener('analysis-understanding',event=>renderUnderstanding(event.detail,$('#analysisUnderstanding')));
    window.addEventListener('analysis-reset',()=>{previewEpoch++;});
    window.addEventListener('analysis-start',()=>{previewEpoch++;rankRequest++;$('#previewRankResults').dataset.request='invalid';});
    window.addEventListener('task-evidence',event=>{showEvidence(event.detail.id,event.detail.source);});
    window.addEventListener('task-analysis', async event => {
      const target = $('#previewRankResults'), epoch = previewEpoch, source = event.detail.source;
      try {
        if(event.detail.source!==currentSource) await changeSource(event.detail.source,true);
        if (!snapshot) await load();
        if(epoch!==previewEpoch || source!==currentSource)return;
        if(!snapshot?.configured) throw new Error(t(currentSource==='diwan'?'diwan_setup':'not_connected'));
        await runRank({text: event.detail.text, project_id: currentSource==='diwan'?'diwan':event.detail.project_id || $('#analysisProject').value, category: event.detail.category, exclude_id: event.detail.exclude_id}, target);
        if(event.detail.exclude_id && snapshot.tasks.some(row=>row.id===event.detail.exclude_id)){
          target.append(button(t('review_task'),async()=>{window.dispatchEvent(new CustomEvent('workspace-panel',{detail:'assignmentPanel'}));$('#recommendationTask').value=event.detail.exclude_id;selectionChanged();await runRank({task_id:event.detail.exclude_id});}));
        }
      } catch (error) { if(epoch!==previewEpoch || source!==currentSource)return; target.replaceChildren(node('p', error.message, 'd-error')); window.dispatchEvent(new CustomEvent('recommendation-results',{detail:{error:true}})); }
    });
    $('#recommendationTask').addEventListener('change', () => selectionChanged());

    $('#recommendationRefresh').addEventListener('click', event => action(event.currentTarget, async () => { await api('/refresh', {}); await load(); }));
    $('#recommendationForm').addEventListener('submit', event => {
      event.preventDefault(); action(event.submitter, () => runRank({task_id: $('#recommendationTask').value || null,
        text: $('#recommendationText').value, project_id: $('#recommendationProject').value, category: $('#recommendationCategory').value}));
    });
    [['#markNeedsAssignment', 'needs-assignment', 'confirm_needs'], ['#claimOwnWork', 'self', 'confirm_self'], ['#verifyAssignment', 'verify', null], ['#releaseUncertain','release-uncertain','confirm_release']].forEach(([selector, route, confirm]) => {
      $(selector).addEventListener('click', event => action(event.currentTarget, async () => {
        const id = $('#recommendationTask').value; if (!id) throw new Error(t('select_task'));
        if (confirm && !await confirmAction(event.currentTarget.textContent, t(confirm))) return;
        await api('/tasks/' + id + '/' + route, {confirmed:true}); await load(); selectionChanged();
      }));
    });
    $('#addRecommendationEmployee').addEventListener('click', () => employeeEditor({enabled: false, active: true, projects: [], categories: []}));
    $('#recommendationPolicy').addEventListener('submit', event => {
      event.preventDefault(); action(event.submitter, async () => {
        const employees = employeeRows.map(fields => ({id: fields.id.value.trim(), name: fields.name.value.trim(), enabled: fields.enabled.checked, active: fields.active.checked,
          projects: Array.from(fields.projects.selectedOptions,o=>o.value), categories: split(fields.categories.value), away_from: fields.away_from.value, away_to: fields.away_to.value}));
        const data_fields=Object.fromEntries(Array.from(document.querySelectorAll('[data-field-map]')).filter(input=>input.value.trim()).map(input=>[input.dataset.fieldMap,input.value.trim()]));
        await api('/policy', {data_fields, employees, intake_ids: [], supervisor_ids: [],
          category_field: $('#recommendationCategoryField').value, top_n: Number($('#recommendationTopN').value),
          weights: {similarity: Number($('#weightSimilarity').value), experience: Number($('#weightExperience').value), capacity: Number($('#weightCapacity').value)}});
        policyLoaded = false; await load();
      });
    });
  }
  let suggestionPoll;
  function pollSuggestions(pending) {
    clearTimeout(suggestionPoll);
    if(pending){
      suggestionPoll=setTimeout(()=>{if(!document.hidden && !busy)load().catch(error=>status(error.message,true));},5000);
    }
  }
  window.addEventListener('workspace-snapshot',()=>pollSuggestions(snapshot?.notifications?.some(row=>row.suggestion?.status==='pending')));
  load().catch(error => status(error.message, true));
  setInterval(() => { if (!document.hidden && !busy) load().catch(error => status(error.message, true)); }, 60000);
})();
