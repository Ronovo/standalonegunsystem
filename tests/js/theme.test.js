import { afterEach, describe, expect, it, vi } from 'vitest';

import { loadScripts, trackListeners } from './helpers.js';

trackListeners();

afterEach(() => {
  delete document.startViewTransition;
  document.documentElement.style.cssText = '';
});

const picker = '<select data-theme-picker><option value="range">Range</option><option value="hud">HUD</option><option value="light">Light</option></select>';
const theme = () => document.documentElement.dataset.theme;
const select = () => document.querySelector('select');

async function load(html = picker) {
  await loadScripts(['theme.js'], html);
  document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true }));
}

function pick(value) {
  select().value = value;
  select().dispatchEvent(new Event('change'));
}

describe('on load', () => {
  it('uses the saved theme and shows it in the picker', async () => {
    localStorage.setItem('theme', 'hud');
    await load();
    expect([theme(), select().value, window.gunTheme.get()]).toEqual(['hud', 'hud', 'hud']);
  });

  it('falls back to the range theme', async () => {
    await load();
    expect([theme(), select().value]).toEqual(['range', 'range']);
  });

  it('still applies a theme when storage is blocked', async () => {
    vi.stubGlobal('localStorage', { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } });
    await load();
    expect(theme()).toBe('range');
    pick('light');
    expect(theme()).toBe('light');
  });
});

describe('picking a theme', () => {
  it('applies and saves it', async () => {
    await load();
    pick('light');
    expect([theme(), localStorage.getItem('theme')]).toEqual(['light', 'light']);
  });

  it('wipes in from the picker when the browser can animate the change', async () => {
    await load();
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })));
    document.startViewTransition = vi.fn((change) => change());
    select().getBoundingClientRect = () => ({ left: 100, top: 10, width: 40, height: 20 });
    pick('hud');
    expect(document.startViewTransition).toHaveBeenCalledOnce();
    expect(theme()).toBe('hud');
    const style = document.documentElement.style;
    expect([style.getPropertyValue('--wipe-x'), style.getPropertyValue('--wipe-y')]).toEqual(['120px', '20px']);
  });

  it('wipes from the top when set by a script', async () => {
    await load();
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })));
    document.startViewTransition = vi.fn((change) => change());
    window.gunTheme.set('light');
    expect([theme(), document.documentElement.style.getPropertyValue('--wipe-x')]).toEqual(['light', '']);
  });

  it('switches without animating for people who prefer reduced motion', async () => {
    await load();
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })));
    document.startViewTransition = vi.fn();
    pick('hud');
    expect(document.startViewTransition).not.toHaveBeenCalled();
    expect(theme()).toBe('hud');
  });
});

describe('another tab', () => {
  it('changing the theme changes this one too', async () => {
    await load();
    window.dispatchEvent(new StorageEvent('storage', { key: 'theme', newValue: 'hud' }));
    expect([theme(), select().value]).toEqual(['hud', 'hud']);
    window.dispatchEvent(new StorageEvent('storage', { key: 'theme', newValue: null }));
    expect(theme()).toBe('range');
  });

  it('changing something else is ignored', async () => {
    await load();
    window.dispatchEvent(new StorageEvent('storage', { key: 'range-mode', newValue: 'forms' }));
    expect(theme()).toBe('range');
  });
});
