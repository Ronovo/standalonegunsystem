import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { loadScripts, trackListeners } from './helpers.js';

let clicked;

trackListeners();

beforeEach(() => {
  vi.useFakeTimers();
  clicked = [];
  document.addEventListener('click', (event) => {
    event.preventDefault();
    clicked.push(event.target.textContent);
  });
});

afterEach(() => {
  vi.useRealTimers();
});

/* Runs app.js against the given markup, the way the page's deferred script runs once the body is parsed. */
async function load(html, fetch = vi.fn(() => new Promise(() => {}))) {
  vi.stubGlobal('fetch', fetch);
  await loadScripts(['app.js'], html);
  await vi.advanceTimersByTimeAsync(0);
  return fetch;
}

const menu = (count) => Array.from({ length: count }, (_, i) => `<button data-key="${i + 1}">Item ${i + 1}</button>`).join('');

function press(key, options = {}, target = document.body) {
  target.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, ...options }));
}

describe('number keys', () => {
  it('pick the menu item with that number', async () => {
    await load(menu(3));
    press('2');
    expect(clicked).toEqual(['Item 2']);
  });

  it('wait for a second digit while a longer number could still match', async () => {
    await load(menu(12));
    press('1');
    expect(clicked).toEqual([]);
    press('2');
    expect(clicked).toEqual(['Item 12']);
  });

  it('take the single digit when no second digit comes', async () => {
    await load(menu(12));
    press('1');
    await vi.advanceTimersByTimeAsync(449);
    expect(clicked).toEqual([]);
    await vi.advanceTimersByTimeAsync(1);
    expect(clicked).toEqual(['Item 1']);
  });

  it('skip a disabled item', async () => {
    await load('<button data-key="1" disabled>Fire</button>');
    press('1');
    expect(clicked).toEqual([]);
  });

  it('focus an item marked data-focus instead of clicking it', async () => {
    await load('<select data-key="1" data-focus><option>M1911</option></select>');
    press('1');
    expect(document.activeElement).toBe(document.querySelector('select'));
    expect(clicked).toEqual([]);
  });

  it('start over after a number with no item', async () => {
    await load(menu(3));
    press('9');
    press('1');
    expect(clicked).toEqual(['Item 1']);
  });

  it('ignore other keys and keys held with Ctrl, Alt or Meta', async () => {
    await load(menu(3));
    press('a');
    for (const modifier of ['ctrlKey', 'altKey', 'metaKey']) press('2', { [modifier]: true });
    press('3');
    expect(clicked).toEqual(['Item 3']);
  });

  it('are left alone while typing in a field', async () => {
    await load(`${menu(3)}<input name="shots"><select name="size"></select><textarea></textarea>`);
    for (const field of document.querySelectorAll('input, select, textarea')) press('1', {}, field);
    expect(clicked).toEqual([]);
  });
});

describe('Escape', () => {
  it('goes back', async () => {
    await load(`<button data-back>Back</button>${menu(3)}`);
    press('Escape');
    expect(clicked).toEqual(['Back']);
  });

  it('does nothing on a page with no way back', async () => {
    await load(menu(3));
    press('Escape');
    expect(clicked).toEqual([]);
  });

  it('leaves a field without going back', async () => {
    await load('<button data-back>Back</button><input name="shots">');
    const field = document.querySelector('input');
    field.focus();
    press('Escape', {}, field);
    expect(document.activeElement).toBe(document.body);
    expect(clicked).toEqual([]);
  });

  it('cancels a number still waiting for its second digit', async () => {
    await load(`<button data-back>Back</button>${menu(12)}`);
    press('1');
    press('Escape');
    await vi.advanceTimersByTimeAsync(450);
    expect(clicked).toEqual(['Back']);
  });
});

describe('tabs', () => {
  const tabs = `<div data-tabs>
    <input type="radio" name="class" value="a" data-tab checked><input type="radio" name="class" value="b" data-tab>
    <ol data-panel="a"></ol><ol data-panel="b"></ol></div>`;
  const hidden = () => ['a', 'b'].map((name) => document.querySelector(`[data-panel="${name}"]`).hidden);

  it('show only the panel of the checked tab', async () => {
    await load(tabs);
    expect(hidden()).toEqual([false, true]);
    const other = document.querySelector('[value="b"]');
    other.checked = true;
    other.dispatchEvent(new Event('change', { bubbles: true }));
    expect(hidden()).toEqual([true, false]);
  });
});

describe('busy forms', () => {
  const form = '<form data-busy="Firing…"><button data-key="1"><span class="key">1</span><span class="label">Run report</span></button></form>';
  const label = () => document.querySelector('.label').textContent;

  it('show the busy text and disable the button while submitting', async () => {
    await load(form);
    document.querySelector('form').dispatchEvent(new Event('submit'));
    const button = document.querySelector('button');
    expect([label(), button.querySelector('.key').textContent, button.disabled]).toEqual(['Firing…', '1', true]);
  });

  it('with a plain button show the busy text on the button itself', async () => {
    await load('<form data-busy="Firing…"><button>Run report</button></form>');
    document.querySelector('form').dispatchEvent(new Event('submit'));
    expect(document.querySelector('button').textContent).toBe('Firing…');
  });

  it('come back ready when the page is shown again', async () => {
    await load(form);
    document.querySelector('form').dispatchEvent(new Event('submit'));
    window.dispatchEvent(new Event('pageshow'));
    const button = document.querySelector('button');
    expect([label(), button.querySelector('.key').textContent, button.disabled]).toEqual(['Run report', '1', false]);
  });

  it('without a button are left alone', async () => {
    await load('<form data-busy="Firing…"><input name="shots"></form>');
    document.querySelector('form').dispatchEvent(new Event('submit'));
    expect(document.querySelector('input').disabled).toBe(false);
  });
});

describe('toasts', () => {
  const list = '<div id="toasts"><div class="toast">Weapon is reloaded!</div></div>';

  it('fade the server messages after five seconds', async () => {
    await load(list);
    const toast = document.querySelector('.toast');
    await vi.advanceTimersByTimeAsync(4999);
    expect(toast.classList.contains('leaving')).toBe(false);
    await vi.advanceTimersByTimeAsync(1);
    expect(toast.classList.contains('leaving')).toBe(true);
    await vi.advanceTimersByTimeAsync(400);
    expect(document.querySelector('.toast')).toBeNull();
  });

  it('can be added by other scripts', async () => {
    await load(list);
    const toast = window.gunToast('Out of ammo');
    expect(toast.textContent).toBe('Out of ammo');
    expect(document.querySelectorAll('.toast')).toHaveLength(2);
    await vi.advanceTimersByTimeAsync(5400);
    expect(document.querySelectorAll('.toast')).toHaveLength(0);
  });

  it('go nowhere on a page without the list', async () => {
    await load(menu(1));
    expect(window.gunToast('lost')).toBeNull();
  });
});

describe('portfolio login link', () => {
  const link = '<a id="portfolio-button" href="/sso/login" data-portfolio-url="http://portfolio.test">Log in with portfolio account</a>';
  const answer = (ok, body) => vi.fn(async () => ({ ok, json: async () => body }));
  const text = () => document.getElementById('portfolio-button').textContent;

  it('names the account this browser is logged in to', async () => {
    const fetch = await load(link, answer(true, { username: 'ronovo' }));
    expect(fetch).toHaveBeenCalledWith('http://portfolio.test/sso/me', { credentials: 'include', signal: expect.any(AbortSignal) });
    expect(text()).toBe('Log in as ronovo');
  });

  it('keeps its text when nobody is logged in to the portfolio', async () => {
    await load(link, answer(true, {}));
    expect(text()).toBe('Log in with portfolio account');
  });

  it('keeps its text when the portfolio answers with an error', async () => {
    const fetch = await load(link, answer(false, { username: 'ronovo' }));
    expect(fetch).toHaveBeenCalledOnce();
    expect(text()).toBe('Log in with portfolio account');
  });

  it('keeps its text when the portfolio cannot be reached', async () => {
    await load(link, vi.fn(async () => { throw new TypeError('Failed to fetch'); }));
    expect(text()).toBe('Log in with portfolio account');
  });

  it('is not looked up on pages without it', async () => {
    const fetch = await load(menu(3));
    expect(fetch).not.toHaveBeenCalled();
  });
});
