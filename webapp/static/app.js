(() => {
  let buffer = "";
  let timer = null;

  const targets = () => [...document.querySelectorAll("[data-key]")];

  const activate = (el) => {
    if (el.hasAttribute("data-focus")) el.focus();
    else el.click();
  };

  const flush = () => {
    const match = targets().find((el) => el.dataset.key === buffer && !el.disabled);
    buffer = "";
    if (match) activate(match);
  };

  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.target.closest("input, select, textarea")) {
      if (event.key === "Escape") event.target.blur();
      return;
    }
    if (event.key === "Escape") {
      document.querySelector("[data-back]")?.click();
      return;
    }
    if (!/^[0-9]$/.test(event.key)) return;

    // Wait briefly for a second digit only when a longer key (e.g. "12") could still match.
    buffer += event.key;
    clearTimeout(timer);
    const longer = targets().some((el) => el.dataset.key.length > buffer.length && el.dataset.key.startsWith(buffer));
    if (longer) timer = setTimeout(flush, 450);
    else flush();
  });

  document.querySelectorAll("form[data-busy]").forEach((form) => {
    form.addEventListener("submit", () => {
      const button = form.querySelector("button");
      if (!button) return;
      button.textContent = form.dataset.busy;
      button.disabled = true;
    });
  });
})();
