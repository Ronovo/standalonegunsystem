// Loaded in <head> on every page, so the saved theme is on <html> before the first paint.
(() => {
  const root = document.documentElement;
  const KEY = "theme";
  const DEFAULT = "range";
  const read = () => {
    try {
      return localStorage.getItem(KEY);
    } catch {
      return null;
    }
  };
  const write = (value) => {
    try {
      localStorage.setItem(KEY, value);
    } catch {}
  };
  const pickers = () => document.querySelectorAll("select[data-theme-picker]");
  const show = (theme) => {
    root.dataset.theme = theme;
    for (const picker of pickers()) picker.value = theme;
  };

  show(read() || DEFAULT);

  const set = (theme, from) => {
    write(theme);
    if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
      show(theme);
      return;
    }
    if (from) {
      const box = from.getBoundingClientRect();
      root.style.setProperty("--wipe-x", `${box.left + box.width / 2}px`);
      root.style.setProperty("--wipe-y", `${box.top + box.height / 2}px`);
    }
    document.startViewTransition(() => show(theme));
  };
  window.gunTheme = { get: () => root.dataset.theme, set };

  // Keeps every open tab on the same theme.
  addEventListener("storage", (event) => {
    if (event.key === KEY) show(event.newValue || DEFAULT);
  });

  addEventListener("DOMContentLoaded", () => {
    for (const picker of pickers()) {
      picker.value = root.dataset.theme;
      picker.addEventListener("change", () => set(picker.value, picker));
    }
  });
})();
