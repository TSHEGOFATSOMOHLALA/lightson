const TYPE_LABELS = {
  power: "Power",
  water: "Water",
  internet: "Wi-Fi / fibre",
  mobile_data: "Mobile data",
};

const state = { type: "", search: "" };

const el = {
  form: document.getElementById("report-form"),
  area: document.getElementById("area"),
  description: document.getElementById("description"),
  formMessage: document.getElementById("form-message"),
  feedMessage: document.getElementById("feed-message"),
  outages: document.getElementById("outages"),
  areas: document.getElementById("areas"),
  search: document.getElementById("search"),
  chips: document.querySelectorAll(".chip"),
};

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = "Something went wrong. Try again.";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = "Check the details you entered.";
    } catch (_) { /* keep default */ }
    throw new Error(detail);
  }
  return res.json();
}

function timeAgo(iso) {
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.floor(hours / 24);
  return `${days} d ago`;
}

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderOutage(o) {
  const li = make("li", "outage");
  li.dataset.type = o.outage_type;

  const top = make("div", "outage-top");
  top.append(
    make("span", "outage-title", `${TYPE_LABELS[o.outage_type]} out in ${o.area}`),
    make("span", "outage-time", `Reported ${timeAgo(o.created_at)}`)
  );
  li.append(top);

  if (o.description) li.append(make("p", "outage-desc", o.description));

  const bottom = make("div", "outage-bottom");
  const affected = make("p", "affected");
  const strong = make("strong", "", String(o.confirmations));
  affected.append(
    strong,
    ` ${o.confirmations === 1 ? "person" : "people"} affected`
  );

  const actions = make("div", "actions");
  const meToo = make("button", "btn", "I'm affected too");
  meToo.type = "button";
  meToo.addEventListener("click", () => act(o.id, "confirm", meToo));
  const fixed = make("button", "btn", "It's back");
  fixed.type = "button";
  fixed.addEventListener("click", () => act(o.id, "resolve", fixed));
  actions.append(meToo, fixed);

  bottom.append(affected, actions);
  li.append(bottom);
  return li;
}

function setMessage(node, text, kind) {
  node.textContent = text || "";
  node.className = "message" + (kind ? ` is-${kind}` : "");
}

async function loadOutages() {
  const params = new URLSearchParams({ limit: "100" });
  if (state.type) params.set("outage_type", state.type);
  if (state.search.trim()) params.set("area", state.search.trim());
  try {
    const items = await api(`/outages?${params}`);
    el.outages.replaceChildren(...items.map(renderOutage));
    if (items.length === 0) {
      const empty = make(
        "li",
        "empty",
        state.search || state.type
          ? "No reports match. Try another area or type."
          : "Nothing reported right now. If something is down, report it on the left."
      );
      el.outages.append(empty);
    }
    setMessage(el.feedMessage, "");
  } catch (err) {
    setMessage(el.feedMessage, "Can't load reports. Check your connection and try again.", "error");
  }
}

async function loadAreas() {
  try {
    const items = await api("/areas");
    if (items.length === 0) {
      el.areas.replaceChildren(make("li", "area-empty", "No active reports."));
      return;
    }
    el.areas.replaceChildren(
      ...items.slice(0, 5).map((a) => {
        const li = make("li");
        li.append(
          make("span", "", a.area),
          make("span", "count", `${a.active_reports} ${a.active_reports === 1 ? "report" : "reports"}`)
        );
        return li;
      })
    );
  } catch (_) {
    /* leave previous list in place */
  }
}

async function act(id, action, button) {
  button.disabled = true;
  try {
    await api(`/outages/${id}/${action}`, { method: "POST" });
    button.classList.add("is-flash");
    button.textContent = action === "confirm" ? "Added" : "Marked as back";
    setTimeout(refresh, 600);
  } catch (err) {
    button.disabled = false;
    setMessage(el.feedMessage, err.message, "error");
  }
}

function refresh() {
  return Promise.all([loadOutages(), loadAreas()]);
}

el.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const area = el.area.value.trim();
  if (area.length < 2) {
    setMessage(el.formMessage, "Enter your suburb or street.", "error");
    el.area.focus();
    return;
  }
  const submit = el.form.querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    const data = new FormData(el.form);
    const result = await api("/outages", {
      method: "POST",
      body: JSON.stringify({
        outage_type: data.get("outage_type"),
        area,
        description: el.description.value.trim(),
      }),
    });
    const merged = result.confirmations > 1;
    setMessage(
      el.formMessage,
      merged
        ? "Already reported here. We added you to the count."
        : "Reported. Your neighbours can see it now.",
      "ok"
    );
    el.description.value = "";
    await refresh();
  } catch (err) {
    setMessage(el.formMessage, err.message, "error");
  } finally {
    submit.disabled = false;
  }
});

el.chips.forEach((chip) =>
  chip.addEventListener("click", () => {
    el.chips.forEach((c) => c.classList.toggle("is-active", c === chip));
    state.type = chip.dataset.type;
    loadOutages();
  })
);

let searchTimer;
el.search.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.search = el.search.value;
    loadOutages();
  }, 250);
});

refresh();
setInterval(refresh, 30000);
