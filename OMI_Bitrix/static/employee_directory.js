(() => {
  'use strict';
  if (!document.querySelector('#directoryForm')) return;
  const sourceName = source => source === 'bitrix' ? 'Bitrix24' : t('diwan');
  const localDate = value => { if(!value)return '—'; const d=new Date(value); return Number.isNaN(d.getTime()) ? '—' : d.toLocaleString(document.documentElement.lang || 'en'); };
  const $ = selector => document.querySelector(selector);
  const t = key => window.DIWAN_I18N?.['d_' + key] || key;
  const node = (tag, text, cls) => {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (cls) el.className = cls;
    return el;
  };
  const status = (target, message, error=false) => {
    $(target).textContent = message;
    $(target).classList.toggle('d-error', error);
  };
  async function api(url, payload) {
    const response = await fetch(url, payload === undefined ? {} : {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || t('error_invalid_input'));
    return data;
  }
  const control = (container, key, value, label, type='text', onChange) => {
    const wrap = node('label', label), input = node('input');
    input.type = type;
    if (type === 'checkbox') { input.checked = Boolean(value); wrap.className='d-directory-check'; }
    else input.value = value || '';
    input.name = key;
    input.addEventListener(type === 'checkbox' ? 'change' : 'input', () =>
      onChange(type === 'checkbox' ? input.checked : input.value));
    wrap.append(input); container.append(wrap);
    return input;
  };
  const button = (label, handler) => {
    const el = node('button', label, 'btn secondary'); el.type='button';
    el.addEventListener('click', handler); return el;
  };
  let people = [], page = 1, dirty = false;
  const modified = () => { dirty = true; status('#directoryStatus',t('directory_unsaved')); };
  function render() {
    const query = $('#directorySearch').value.trim().toLocaleLowerCase();
    const filtered = people.filter(p => (p.name+' '+p.team+' '+p.accounts.map(a=>a.id).join(' '))
      .toLocaleLowerCase().includes(query));
    page = Math.min(page, Math.max(1,Math.ceil(filtered.length/20)));
    const target = $('#directoryRows'); target.replaceChildren();
    if (!filtered.length) target.append(node('p',t('directory_empty'),'help'));
    filtered.slice((page-1)*20,page*20).forEach(person => {
      const row = node('fieldset', undefined, 'd-employee');
      row.append(node('legend',person.name));
      const identities=node('p',person.accounts.map(a=>sourceName(a.source)+' · '+a.id).join(' / '),'help');
      identities.dir='auto'; row.append(identities);
      person.accounts.forEach(a=>{
        const details=[a.email,a.department,a.position].filter(Boolean).map(v=>Array.isArray(v)?v.join(', '):String(v));
        if(details.length){const info=node('p',sourceName(a.source)+' · '+details.join(' · '),'help');info.dir='auto';row.append(info);}
      });
      const fields=node('div',undefined,'d-grid');
      [['name','directory_name','text'],['team','directory_team','text'],['active','directory_active','checkbox'],
        ['away_from','away_from','date'],['away_to','away_to','date']].forEach(([key,label,type]) =>
        control(fields,key,person[key],t(label),type,value=>{person[key]=value;modified();}));
      person.accounts.forEach(account => {
        const input=control(fields,'enabled_'+account.source,account.enabled,
          t('directory_enabled')+' · '+sourceName(account.source),'checkbox',value=>{account.enabled=value;modified();});
        // Linking cannot grant Bitrix project membership or bypass source status.
        if(account.source==='bitrix' && !(account.source_enabled ?? account.enabled)) input.disabled=true;
        if(!account.active) fields.append(node('p',account.source+' · '+t('directory_source_inactive'),'help'));
      });
      row.append(fields);
      if(person.accounts.length>1)row.append(button(t('directory_unlink'),()=>{
        people=people.flatMap(p=>p===person ? person.accounts.map(a=>({
          ...person,person_id:globalThis.crypto?.randomUUID?.() || 'local-'+Date.now()+'-'+Math.random().toString(36).slice(2),accounts:[a],linked:false
        })) : [p]);modified();render();
      }));
      target.append(row);
    });
    const paging=$('#directoryPaging');paging.replaceChildren();
    const prev=button(t('history_prev'),()=>{page--;render();});prev.disabled=page<=1;
    const next=button(t('history_next'),()=>{page++;render();});next.disabled=page*20>=filtered.length;
    paging.append(prev,node('span',page+' / '+Math.max(1,Math.ceil(filtered.length/20))+' · '+filtered.length),next);
    const link=$('#directoryLinkForm');
    ['bitrix','diwan'].forEach(source=>{
      const select=link.elements[source], selected=select.value;
      select.replaceChildren(new Option(t('directory_choose'),''));
      people.filter(p=>p.accounts.length===1 && p.accounts[0].source===source).forEach(p=>{
        select.append(new Option(p.name+' · '+p.accounts[0].id,p.person_id));
      });select.value=selected;
    });
    link.querySelector('button').disabled=people.filter(p=>p.accounts.length===1 &&
      p.accounts[0].source==='bitrix').length===0 || people.filter(p=>p.accounts.length===1 &&
      p.accounts[0].source==='diwan').length===0;
  }
  async function loadDirectory() {
    const data = await api('/api/employees');
    people=data.people;dirty=false;
    $('#directorySources').textContent=Object.entries(data.sources).map(([source,value])=>
      sourceName(source)+' · '+t(value.complete?'complete':'partial')+' · '+localDate(value.updated_at)).join(' / ');
    render();
  }
  $('#directorySearch').addEventListener('input',()=>{page=1;render();});
  $('#directoryLinkForm').addEventListener('submit',event=>{
    event.preventDefault();
    const left=people.find(p=>p.person_id===event.target.elements.bitrix.value);
    const right=people.find(p=>p.person_id===event.target.elements.diwan.value);
    if(!left || !right || left===right)return;
    people=people.filter(p=>p!==left && p!==right);
    const starts=[left.away_from,right.away_from].filter(Boolean).sort();
    const ends=[left.away_to,right.away_to].filter(Boolean).sort();
    people.push({...left,active:left.active && right.active,team:left.team || right.team,
      away_from:starts[0] || '',away_to:ends.at(-1) || '',
      accounts:[...left.accounts,...right.accounts],linked:true});
    modified();render();
  });
  $('#directoryForm').addEventListener('submit',async event=>{
    event.preventDefault();const save=event.submitter;save.disabled=true;
    status('#directoryStatus',t('working'));
    try { const data=await api('/api/employees',{people});people=data.people;dirty=false;render();
      status('#directoryStatus',t('saved')); }
    catch(error){status('#directoryStatus',error.message,true);}
    finally{save.disabled=false;}
  });
  window.addEventListener('employees-saved',()=>{
    if(!dirty)loadDirectory().catch(error=>status('#directoryStatus',error.message,true));
    else status('#directoryStatus',t('directory_reload_hint'));
  });
  window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
  loadDirectory().catch(error=>status('#directoryStatus',error.message,true));

  function domainRow(value={}) {
    const row=node('fieldset',undefined,'d-employee'), fields=node('div',undefined,'d-grid');
    const data={id:value.id||'',ar:value.ar||'',en:value.en||'',aliases:(value.aliases||[]).join('\n')};
    [['id','domain_id'],['ar','name_ar'],['en','name_en']].forEach(([key,label])=>{
      const input=control(fields,key,data[key],t(label),'text',v=>data[key]=v);
      input.required=true;input.maxLength=key==='id'?40:120;
      if(key!=='ar')input.dir='ltr';
    });
    const wrap=node('label',t('domain_aliases')), aliases=node('textarea');aliases.value=data.aliases;
    aliases.rows=3;aliases.required=true;aliases.addEventListener('input',()=>data.aliases=aliases.value);
    wrap.append(aliases);row.append(fields,wrap,button(t('remove'),()=>row.remove()));
    row.read=()=>({...data,aliases:data.aliases.split('\n').map(v=>v.trim()).filter(Boolean)});
    $('#domainRulesRows').append(row);
  }
  api('/api/intelligence/domains').then(data=>{
    $('#builtInDomains').append(node('p',t('domain_builtin')+': '+(data.builtins.map(v=>
      v[window.WC_LANG==='ar'?'ar':'en']).join('، ') || t('no_discovered_topics')),'help'));
    data.domains.forEach(domainRow);
  }).catch(error=>status('#domainRulesStatus',error.message,true));
  $('#addDomainRule').addEventListener('click',()=>domainRow());
  $('#domainRulesForm').addEventListener('submit',async event=>{
    event.preventDefault();const save=event.submitter;save.disabled=true;
    status('#domainRulesStatus',t('working'));
    try {await api('/api/intelligence/domains',{domains:[...$('#domainRulesRows').children].map(row=>row.read())});
      status('#domainRulesStatus',t('saved'));}
    catch(error){status('#domainRulesStatus',error.message,true);}
    finally{save.disabled=false;}
  });
})();

