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
    const button = form.querySelector("button");
    if (!button) return;
    const idle = button.textContent;
    form.addEventListener("submit", () => {
      button.textContent = form.dataset.busy;
      button.disabled = true;
    });
    // Going back to this page can show it as it was left, with the button still busy.
    window.addEventListener("pageshow", () => {
      button.textContent = idle;
      button.disabled = false;
    });
  });
})();

// Names the portfolio account this browser is logged in to on the login link, when the portfolio says who that is.
(() => {
  const link = document.getElementById("portfolio-button");
  if (!link) return;
  fetch(`${link.dataset.portfolioUrl}/sso/me`, { credentials: "include", signal: AbortSignal.timeout(5000) })
    .then((response) => (response.ok ? response.json() : {}))
    .then((data) => {
      if (data.username) link.textContent = `Log in as ${data.username}`;
    })
    .catch(() => {});
})();
