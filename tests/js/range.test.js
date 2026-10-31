import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { loadScripts, trackListeners } from './helpers.js';

trackListeners();

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })));
});

afterEach(() => {
  vi.useRealTimers();
  delete document.startViewTransition;
});

const state = (over = {}) => ({
  weapon: { ammo: 7, max_ammo: 7, pellets: 1, reload_seconds: 2 },
  dummy: { health: 200, max_health: 200, destroyed: false },
  hit_chance: 0.8,
  pulls: 0,
  last_pull: null,
  ...over,
});

const panels = ({ ammo = 7, health = 200, destroyed = false, lane = true } = {}) => `
  <span class="pips" data-bind="pips">${'<i class="on"></i>'.repeat(ammo)}${'<i></i>'.repeat(7 - ammo)}</span>
  <span data-bind="ammo">${ammo}/7</span>
  <span class="meter health"><span class="meter-fill" style="width: ${health / 2}%"></span></span>
  <span data-bind="health">${health}</span>
  ${lane ? `<div class="dummy${destroyed ? ' destroyed' : ''}" data-bind="dummy"></div>
  <div class="reticle" data-bind="reticle"></div>
  <div class="lane-fx" data-bind="fx"></div>` : ''}
  <form data-live="fire" action="/range/fire"><button name="go" value="1">Fire</button></form>
  <form data-live="mode" action="/range/mode"><button name="mode" value="fa">Auto</button></form>
  <form data-live="reload" action="/range/reload"><button data-seconds="2">Reload</button></form>
  <form action="/range/leave"><button>Quit</button></form>`;

const page = (current = state(), html = panels()) => `
  <div class="mode-switch"><button data-range-mode="live">Live</button><button data-range-mode="forms">Forms</button></div>
  <div id="range-panels">${html}</div>
  <script type="application/json" id="range-state">${JSON.stringify(current)}</script>
  <div id="toasts"></div>`;

const answer = (data, ok = true) => vi.fn(async () => ({ ok, status: ok ? 200 : 500, json: async () => data }));

async function load(html = page(), fetch = answer({}), scripts = ['app.js', 'range.js']) {
  vi.stubGlobal('fetch', fetch);
  await loadScripts(scripts, html);
  return fetch;
}

const form = (action) => document.querySelector(`form[data-live="${action}"], form[action="/range/${action}"]`);
const text = (name) => document.querySelector(`[data-bind="${name}"]`)?.textContent;
const toasts = () => [...document.querySelectorAll('.toast')].map((toast) => toast.textContent);
const mode = () => document.body.dataset.rangeMode;

async function submit(action, withButton = true) {
  const target = form(action);
  const submitter = withButton ? target.querySelector('button') : null;
  const event = new SubmitEvent('submit', { bubbles: true, cancelable: true, submitter });
  target.dispatchEvent(event);
  await vi.advanceTimersByTimeAsync(0);
  return event;
}

const pull = (marks, shots) => ({ mode: 'Single Shot', distance: 50, marks, hits: 0, damage: 0, pellets: 1, shots });

describe('a page without the range', () => {
  it('is left alone', async () => {
    await load('<p>Armory</p>');
    expect(mode()).toBeUndefined();
  });
});

describe('the mode switch', () => {
  it('starts on live fire and remembers a change', async () => {
    await load();
    expect(mode()).toBe('live');
    expect(document.querySelector('[data-range-mode="live"]').classList.contains('active')).toBe(true);
    document.querySelector('[data-range-mode="forms"]').click();
    expect([mode(), localStorage.getItem('range-mode')]).toEqual(['forms', 'forms']);
    expect(document.querySelector('[data-range-mode="forms"]').classList.contains('active')).toBe(true);
  });

  it('comes back as it was left', async () => {
    localStorage.setItem('range-mode', 'forms');
    await load();
    expect(mode()).toBe('forms');
  });

  it('works without storage', async () => {
    vi.stubGlobal('localStorage', { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); }, clear() {} });
    await load();
    expect(mode()).toBe('live');
    document.querySelector('[data-range-mode="forms"]').click();
    expect(mode()).toBe('live');
  });
});

describe('forms mode', () => {
  it('lets the forms post as usual', async () => {
    localStorage.setItem('range-mode', 'forms');
    const fetch = await load();
    const event = await submit('fire');
    expect(event.defaultPrevented).toBe(false);
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe('live fire', () => {
  it('posts the form with its button and plays the pull shot by shot', async () => {
    const after = state({ weapon: { ammo: 4, max_ammo: 7, pellets: 1, reload_seconds: 2 }, dummy: { health: 100, max_health: 200, destroyed: false },
      pulls: 1, last_pull: pull('+*-', [[40, 160, 1], [60, 100, 1], [0, 100, 0]]) });
    const fetch = await load(page(), answer({ html: panels({ ammo: 4, health: 100 }), state: after, message: null }));
    const event = await submit('fire');
    expect(event.defaultPrevented).toBe(true);
    const [url, options] = fetch.mock.calls[0];
    expect(url).toContain('/range/fire');
    expect([options.method, options.headers.Accept, options.body.get('go')]).toEqual(['POST', 'application/json', '1']);

    expect(document.querySelector('.reticle').classList.contains('firing')).toBe(true);
    expect([text('health'), text('ammo')]).toEqual(['160', '6/7']);
    expect(document.querySelectorAll('.pips .on')).toHaveLength(6);
    expect(document.querySelector('.impact.hit')).not.toBeNull();
    expect(document.querySelector('.float').textContent).toBe('-40');
    await vi.advanceTimersByTimeAsync(170);
    expect([text('health'), text('ammo')]).toEqual(['100', '5/7']);
    expect(document.querySelector('.impact.crit')).not.toBeNull();
    expect(document.querySelector('.float.crit').textContent).toBe('-60');
    await vi.advanceTimersByTimeAsync(170);
    expect([text('health'), text('ammo')]).toEqual(['100', '4/7']);
    expect(document.querySelector('.impact.miss')).not.toBeNull();
    expect(document.querySelectorAll('.float')).toHaveLength(2);
    expect(document.querySelector('.meter.health .meter-fill').style.width).toBe('50%');
    await vi.advanceTimersByTimeAsync(170);
    expect(document.querySelector('.reticle').classList.contains('firing')).toBe(false);
    await vi.advanceTimersByTimeAsync(900);
    expect(document.querySelectorAll('.impact, .float')).toHaveLength(0);
  });

  it('topples the dummy once the last shot has landed', async () => {
    const after = state({ weapon: { ammo: 6, max_ammo: 7 }, dummy: { health: 0, max_health: 200, destroyed: true }, pulls: 1, last_pull: pull('+', [[200, 0, 1]]) });
    await load(page(), answer({ html: panels({ ammo: 6, health: 0, destroyed: true }), state: after, message: null }));
    await submit('fire');
    expect(document.querySelector('.dummy').classList.contains('destroyed')).toBe(false);
    await vi.advanceTimersByTimeAsync(170);
    expect(document.querySelector('.dummy').classList.contains('destroyed')).toBe(true);
  });

  it('plays the pull at once for people who prefer reduced motion', async () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })));
    const after = state({ weapon: { ammo: 5, max_ammo: 7 }, dummy: { health: 120, max_health: 200, destroyed: false }, pulls: 1, last_pull: pull('++', [[40, 160, 1], [40, 120, 1]]) });
    await load(page(), answer({ html: panels({ ammo: 5, health: 120 }), state: after, message: null }));
    await submit('fire');
    await vi.advanceTimersByTimeAsync(0);
    expect([text('health'), text('ammo')]).toEqual(['120', '5/7']);
  });

  it('copes with a lane that has no dummy on it', async () => {
    const after = state({ weapon: { ammo: 6, max_ammo: 100 }, dummy: { health: 160, max_health: 200, destroyed: true }, pulls: 1, last_pull: pull('+', [[40, 160, 1]]) });
    const bare = '<span class="meter ammo"><span class="meter-fill"></span></span><form data-live="fire" action="/range/fire"><button>Fire</button></form>';
    await load(page(state(), bare), answer({ html: bare, state: after, message: null }));
    await submit('fire');
    await vi.advanceTimersByTimeAsync(400);
    expect(document.querySelector('.meter.ammo .meter-fill').style.width).toBe('6%');
    expect(toasts()).toEqual([]);
  });

  it('shows a message instead of a pull when the shot could not be taken', async () => {
    await load(page(), answer({ html: panels(), state: state(), message: 'Out of Ammo! Try Reloading.' }));
    await submit('fire');
    expect(toasts()).toEqual(['Out of Ammo! Try Reloading.']);
    expect(document.querySelector('.reticle').classList.contains('firing')).toBe(false);
  });

  it('swaps the panels with a view transition for other actions', async () => {
    document.startViewTransition = vi.fn((change) => change());
    const fetch = await load(page(), answer({ html: '<p id="swapped">Fire mode is now Fully Automatic</p>', state: state(), message: 'Fire mode is now Fully Automatic' }));
    await submit('mode');
    expect(fetch.mock.calls[0][1].body.get('mode')).toBe('fa');
    expect(document.startViewTransition).toHaveBeenCalledOnce();
    expect(document.getElementById('swapped')).not.toBeNull();
    expect(toasts()).toEqual(['Fire mode is now Fully Automatic']);
  });

  it('swaps the panels plainly when the browser cannot animate', async () => {
    await load(page(), answer({ html: '<p id="swapped">done</p>', state: state(), message: null }));
    await submit('mode');
    expect(document.getElementById('swapped')).not.toBeNull();
  });

  it('runs the reload timer before asking for the reload', async () => {
    const fetch = await load(page(), answer({ html: '<p id="swapped">reloaded</p>', state: state(), message: 'Weapon is reloaded!' }));
    await submit('reload');
    const button = document.querySelector('form[data-live="reload"] button');
    expect([button.classList.contains('reloading'), button.style.getPropertyValue('--reload')]).toEqual([true, '2s']);
    expect(fetch).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(1999);
    expect(fetch).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(1);
    expect(fetch).toHaveBeenCalledOnce();
    expect(document.getElementById('swapped')).not.toBeNull();
  });

  it('reloads straight away with reduced motion or no timing on the button', async () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })));
    let fetch = await load(page(), answer({ html: panels(), state: state(), message: null }));
    await submit('reload');
    expect(fetch).toHaveBeenCalledOnce();

    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })));
    const noTiming = panels().replace(' data-seconds="2"', '');
    fetch = await load(page(state(), noTiming), answer({ html: noTiming, state: state(), message: null }));
    await submit('reload');
    expect(fetch).toHaveBeenCalledOnce();

    fetch = await load(page(), answer({ html: panels(), state: state(), message: null }));
    await submit('reload', false);
    expect(fetch).toHaveBeenCalledOnce();
  });

  it('ignores a second submit while one is in flight', async () => {
    const fetch = await load(page(), vi.fn(() => new Promise(() => {})));
    await submit('fire');
    await submit('mode');
    expect(fetch).toHaveBeenCalledOnce();
  });

  it('says so when the range does not answer, then takes the next submit', async () => {
    const fetch = await load(page(), vi.fn(async () => { throw new TypeError('Failed to fetch'); }));
    await submit('fire');
    expect(toasts()).toEqual(['The range did not answer. Try again.']);
    await submit('fire');
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it('treats an error status as no answer', async () => {
    await load(page(), answer({}, false));
    await submit('fire');
    expect(toasts()).toEqual(['The range did not answer. Try again.']);
  });

  it('follows the server to the setup page when the range is gone', async () => {
    const fetch = await load(page(), answer({ redirect: '/range/setup' }));
    await submit('fire');
    expect(fetch).toHaveBeenCalledOnce();
    expect(document.querySelector('form[data-live="fire"]')).not.toBeNull();
    expect(toasts()).toEqual([]);
  });

  it('leaves forms that are not range actions alone', async () => {
    const fetch = await load();
    const event = await submit('leave');
    expect(event.defaultPrevented).toBe(false);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('works without the toast script', async () => {
    const fetch = await load(page(), answer({ html: panels(), state: state(), message: 'Ammo already full. No need to reload.' }), ['range.js']);
    await submit('mode');
    expect(fetch).toHaveBeenCalledOnce();
    expect(toasts()).toEqual([]);
  });
});
