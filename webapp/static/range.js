// Live fire: the range's forms post over fetch and the panels are swapped in place, then the pull is played out
// shot by shot on the lane. In forms mode nothing here intercepts, and the page reloads as it always did.
(() => {
  const panels = document.getElementById("range-panels");
  const stateNode = document.getElementById("range-state");
  if (!panels || !stateNode) return;

  const MODE_KEY = "range-mode";
  const SHOT_MS = 170;
  const MARK_MS = 900;
  let state = JSON.parse(stateNode.textContent);
  let busy = false;

  const read = () => {
    try {
      return localStorage.getItem(MODE_KEY);
    } catch {
      return null;
    }
  };
  const write = (value) => {
    try {
      localStorage.setItem(MODE_KEY, value);
    } catch {}
  };
  const mode = () => (read() === "forms" ? "forms" : "live");
  const showMode = () => {
    document.body.dataset.rangeMode = mode();
    for (const button of document.querySelectorAll("[data-range-mode]")) {
      button.classList.toggle("active", button.dataset.rangeMode === mode());
    }
  };
  for (const button of document.querySelectorAll("[data-range-mode]")) {
    button.addEventListener("click", () => {
      write(button.dataset.rangeMode);
      showMode();
    });
  }
  showMode();

  const toast = (text) => window.gunToast?.(text);
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const bound = (name) => panels.querySelector(`[data-bind="${name}"]`);
  const reduceMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

  const swap = (html) => {
    const apply = () => {
      panels.innerHTML = html;
    };
    if (document.startViewTransition && !reduceMotion()) document.startViewTransition(apply);
    else apply();
  };

  async function post(form, submitter) {
    const body = new FormData(form);
    if (submitter?.name) body.append(submitter.name, submitter.value);
    const response = await fetch(form.action, { method: "POST", body, headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  const showHealth = (health, max) => {
    const meter = panels.querySelector(".meter.health .meter-fill");
    if (meter) meter.style.width = `${Math.round((health / max) * 100)}%`;
    const text = bound("health");
    if (text) text.textContent = health;
  };

  const showAmmo = (ammo, max) => {
    const text = bound("ammo");
    if (text) text.textContent = `${ammo}/${max}`;
    const pips = bound("pips");
    if (pips) [...pips.children].forEach((pip, i) => pip.classList.toggle("on", i < ammo));
    const meter = panels.querySelector(".meter.ammo .meter-fill");
    if (meter) meter.style.width = `${Math.round((ammo / max) * 100)}%`;
  };

  const place = (fx, mark, damage) => {
    const spot = document.createElement("i");
    spot.className = `impact ${mark === "-" ? "miss" : mark === "*" ? "crit" : "hit"}`;
    spot.style.left = `${mark === "-" ? 5 + Math.random() * 90 : 30 + Math.random() * 40}%`;
    spot.style.top = `${mark === "-" ? 5 + Math.random() * 90 : 20 + Math.random() * 50}%`;
    fx.append(spot);
    if (damage) {
      const number = document.createElement("b");
      number.className = `float ${mark === "*" ? "crit" : "hit"}`;
      number.textContent = `-${damage}`;
      number.style.left = spot.style.left;
      number.style.top = spot.style.top;
      fx.append(number);
      setTimeout(() => number.remove(), MARK_MS);
    }
    setTimeout(() => spot.remove(), MARK_MS);
  };

  // Plays the newest pull: the swapped panels already show the end state, so the lane is wound back to how it
  // stood and each shot moves it forward.
  function play(previous, next) {
    const pull = next.last_pull;
    const fx = bound("fx");
    const dummy = bound("dummy");
    const reticle = bound("reticle");
    const { max_health: maxHealth } = next.dummy;
    const { max_ammo: maxAmmo } = next.weapon;
    const step = reduceMotion() ? 0 : SHOT_MS;
    dummy?.classList.remove("destroyed");
    showHealth(previous.dummy.health, maxHealth);
    showAmmo(previous.weapon.ammo, maxAmmo);
    reticle?.classList.add("firing");
    pull.shots.forEach(([damage, after], i) => {
      setTimeout(() => {
        if (fx) place(fx, pull.marks[i], damage);
        showHealth(after, maxHealth);
        showAmmo(previous.weapon.ammo - i - 1, maxAmmo);
      }, i * step);
    });
    const done = pull.shots.length * step;
    setTimeout(() => {
      reticle?.classList.remove("firing");
      if (next.dummy.destroyed) dummy?.classList.add("destroyed");
    }, done);
  }

  async function reloadWithProgress(button) {
    const seconds = button && !reduceMotion() ? Number(button.dataset.seconds) || 0 : 0;
    if (!seconds) return;
    button.style.setProperty("--reload", `${seconds}s`);
    button.classList.add("reloading");
    await wait(seconds * 1000);
  }

  panels.addEventListener("submit", async (event) => {
    const form = event.target;
    if (mode() !== "live" || !form.dataset.live) return;
    event.preventDefault();
    if (busy) return;
    busy = true;
    const previous = state;
    const action = form.dataset.live;
    try {
      if (action === "reload") await reloadWithProgress(event.submitter);
      const data = await post(form, event.submitter);
      if (data.redirect) {
        location.assign(data.redirect);
        return;
      }
      state = data.state;
      if (action === "fire" && state.pulls !== previous.pulls) {
        panels.innerHTML = data.html;
        play(previous, state);
      } else {
        swap(data.html);
      }
      if (data.message) toast(data.message);
    } catch {
      toast("The range did not answer. Try again.");
    } finally {
      busy = false;
    }
  });
})();
