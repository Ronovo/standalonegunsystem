import { afterEach, beforeEach, vi } from 'vitest';

const scripts = {
  'app.js': () => import('../../webapp/static/app.js'),
  'theme.js': () => import('../../webapp/static/theme.js'),
  'range.js': () => import('../../webapp/static/range.js'),
};

/* Every listener a script adds to window or document is removed again after each test, so one test's page
   cannot answer the next test's events. Stubbed globals and spies are cleared with it. */
export function trackListeners() {
  const listeners = [];
  beforeEach(() => {
    for (const target of [window, document]) {
      const listen = target.addEventListener;
      vi.spyOn(target, 'addEventListener').mockImplementation(function track(type, listener, options) {
        listeners.push([target, type, listener, options]);
        return listen.call(this, type, listener, options);
      });
    }
  });
  afterEach(() => {
    for (const [target, type, listener, options] of listeners.splice(0)) target.removeEventListener(type, listener, options);
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    localStorage.clear();
    delete document.documentElement.dataset.theme;
    delete document.body.dataset.rangeMode;
  });
}

/* Runs the named scripts against the given markup, in order, the way the page's scripts run once the body is
   parsed. */
export async function loadScripts(names, html = '') {
  document.body.innerHTML = html;
  vi.resetModules();
  for (const name of names) await scripts[name]();
}
