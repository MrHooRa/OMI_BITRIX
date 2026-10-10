/* Shared interface behavior; source permissions and ranking stay in their services. */
(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const menu = $('#navigationDialog');
  document.querySelectorAll('[data-nav-open]').forEach(button => {
    button.addEventListener('click', () => { menu.showModal(); button.setAttribute('aria-expanded', 'true'); });
    menu.addEventListener('close', () => button.setAttribute('aria-expanded', 'false'));
  });
  document.querySelectorAll('[data-ui-sections]').forEach(root => {
    const sections = Array.from(root.querySelectorAll('[data-ui-section]'));
    const controls = Array.from(root.querySelectorAll('[data-ui-target]'));
    const select = id => {
      if (!sections.some(section => section.id === id)) return;
      sections.forEach(section => { section.hidden = section.id !== id; });
      controls.forEach(control => {
        if (control.dataset.uiTarget === id) control.setAttribute('aria-current', 'page');
        else control.removeAttribute('aria-current');
      });
    };
    controls.forEach(control => control.addEventListener('click', event => {
      event.preventDefault(); select(control.dataset.uiTarget);
      const url = new URL(location.href); url.hash = control.dataset.uiTarget; history.pushState({}, '', url);
    }));
    const restore = () => {
      const requested = location.hash.slice(1);
      select(sections.some(section => section.id === requested) ? requested : sections[0]?.id);
    };
    window.addEventListener('popstate', restore); window.addEventListener('hashchange', restore);
    const forms = root.matches('form') ? [root] : Array.from(root.querySelectorAll('form'));
    forms.forEach(form => {
      // Validate one field after revealing its section; native whole-form
      // validation cannot focus required controls in other hidden sections.
      form.noValidate = true;
      form.addEventListener('submit', event => {
        const invalid = Array.from(form.elements).find(field => field.willValidate && !field.validity.valid);
        if (!invalid) return;
        event.preventDefault(); event.stopImmediatePropagation();
        const section = invalid.closest('[data-ui-section]');
        if (section) {
          select(section.id);
          const url = new URL(location.href); url.hash = section.id; history.replaceState({}, '', url);
        }
        invalid.focus(); invalid.reportValidity();
      }, true);
    });
    restore();
  });
  document.querySelectorAll('.ui-workspace-tools').forEach(tools => {
    tools.addEventListener('keydown', event => { if (event.key === 'Escape') { tools.open = false; tools.querySelector('summary').focus(); } });
    document.addEventListener('click', event => { if (!tools.contains(event.target)) tools.open = false; });
  });
  const tabs = Array.from(document.querySelectorAll('[data-result-panel]'));
  function selectResult(id, focus = false) {
    tabs.forEach(tab => {
      const selected = tab.dataset.resultPanel === id;
      tab.setAttribute('aria-selected', String(selected)); tab.tabIndex = selected ? 0 : -1;
      $('#' + tab.dataset.resultPanel).hidden = !selected;
      if (selected && focus) tab.focus();
    });
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectResult(tab.dataset.resultPanel));
    tab.addEventListener('keydown', event => {
      const rtl = document.documentElement.dir === 'rtl';
      let next;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (event.key === 'ArrowRight') next = (index + (rtl ? -1 : 1) + tabs.length) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index + (rtl ? 1 : -1) + tabs.length) % tabs.length;
      if (next !== undefined) { event.preventDefault(); selectResult(tabs[next].dataset.resultPanel, true); }
    });
  });
  window.addEventListener('result-panel', event => selectResult(event.detail));
  window.addEventListener('analysis-start', event => {
    $('#analysisContext').replaceChildren(); $('#analysisUnderstanding')?.replaceChildren();
    $('#analysisWelcome').hidden = true; $('#analysisResultWorkspace').hidden = false;
    $('#analysisQuerySummary').textContent = event.detail.text || $('#analysisQuery').value;
    $('#openAffinityResults')?.replaceChildren(); $('#openAffinityCount').textContent = '…';
    $('#candidateResultCount').textContent = '…'; $('#relatedResultCount').textContent = '…';
    selectResult('previewRankResults');
  });
  window.addEventListener('analysis-related', event => {
    $('#relatedResultCount').textContent = String(event.detail.count);
    $('#analysisQuerySummary').textContent = event.detail.text;
  });
  window.addEventListener('recommendation-results', event => {
    $('#candidateResultCount').textContent = event.detail.error ? '—' : String(event.detail.count);
    if(event.detail.error)$('#openAffinityCount').textContent='—';
  });
  window.addEventListener('analysis-reset', () => {
    $('#openAffinityResults')?.replaceChildren(); $('#openAffinityCount').textContent = '';
    $('#analysisWelcome').hidden = false; $('#analysisResultWorkspace').hidden = true;
    $('#analysisContext').replaceChildren(); $('#analysisUnderstanding')?.replaceChildren(); $('#analysisStatus').textContent = '';
  });
  $('#refineAnalysis')?.addEventListener('click', () => { $('#analysisQuery').focus(); $('#analyzeForm').scrollIntoView({block:'center'}); });
  // Keep only this tab's draft, scoped to its signed profile and source; never tokens or results.
  const composer=$('#analyzeForm'), workspace=$('#intelligencePage');
  if(composer && workspace){
    const source=()=>$('#workspaceSource').value;
    const key=value=>'omi-task-draft:'+workspace.dataset.draftScope+':'+value;
    const read=value=>{try{const row=JSON.parse(sessionStorage.getItem(key(value))||'null');return row && Date.now()-row.at<1800000?row:null;}catch{return null;}};
    const save=()=>{try{sessionStorage.setItem(key(source()),JSON.stringify({at:Date.now(),text:composer.elements.text.value,category:composer.elements.category.value,project:composer.elements.project_id.value}));}catch{/* Storage may be disabled. */}};
    const restore=()=>{const row=read(source());composer.elements.text.value=row?.text||'';composer.elements.category.value=row?.category||'';if(row?.project)composer.elements.project_id.value=row.project;};
    composer.addEventListener('input',save);composer.addEventListener('change',save);
    window.addEventListener('pagehide',save);
    window.addEventListener('workspace-source',restore);
    window.addEventListener('workspace-snapshot',()=>{const row=read(source());if(row?.project && [...composer.elements.project_id.options].some(o=>o.value===row.project))composer.elements.project_id.value=row.project;});
    const initial=new URLSearchParams(location.search).get('source');if(['diwan','bitrix'].includes(initial))$('#workspaceSource').value=initial;
    restore();
  }
})();
