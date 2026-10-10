(() => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  document.addEventListener('submit', event => {
    const form = event.target;
    if (form.method?.toUpperCase() !== 'POST' || new URL(form.action).origin !== location.origin) return;
    if (!form.querySelector('[name="_csrf"]')) {
      const input = document.createElement('input');
      input.type = 'hidden'; input.name = '_csrf'; input.value = token || '';
      form.append(input);
    }
  }, true);
  const original = window.fetch.bind(window);
  window.fetch = (input, options = {}) => {
    const method = (options.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
    const url = new URL(input instanceof Request ? input.url : input, location.href);
    if (url.origin === location.origin && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
      options = {...options, headers: new Headers(options.headers || (input instanceof Request ? input.headers : {}))};
      options.headers.set('X-CSRF-Token', token || '');
    }
    return original(input, options);
  };
})();

document.querySelector('#testWorkspace')?.addEventListener('click', async event => {
  const button = event.currentTarget;
  const status = document.querySelector('#workspaceTestStatus');
  const ar = document.documentElement.lang === 'ar';
  button.disabled = true;
  status.textContent = ar ? 'جارٍ الاختبار…' : 'Testing…';
  try {
    const result = await fetch('/api/workspace/test', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({path:document.querySelector('#vault_root').value})});
    if (!result.ok) throw new Error();
    status.textContent = ar ? 'نجحت اختبارات القراءة والكتابة والأسماء العربية والمسار الطويل.' : 'Read/write, Unicode and long-path checks passed.';
  } catch (_) {
    status.textContent = ar ? 'تعذر الاختبار. تحقق من صلاحيات المجلد ودعم المسارات الطويلة.' : 'Folder test failed. Check permissions and long-path support.';
  } finally { button.disabled = false; }
});
