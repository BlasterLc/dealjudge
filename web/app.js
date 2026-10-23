"use strict";

// Dealjudge, static demo. No backend: the verdicts are the ones in data/demo.<lang>.json and the
// "agent" that reads a typed product is a small simulated catalog (see CATALOG in i18n.js).

const STORE_KEY = "dealjudge.v1";
const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)");

const app = {
  lang: "es",
  data: {},        // lang -> parsed json
  mine: [],        // catalog ids the user added
  add: { q: "", stage: "input", matches: [], idx: 0, error: "" },
  addTimer: 0,
};

/* ---------- small helpers ---------- */

const h = (tag, props, ...kids) => {
  const n = document.createElement(tag);
  if (typeof props === "string") n.className = props;
  else if (props) for (const [k, v] of Object.entries(props)) {
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (v === true) n.setAttribute(k, "");
    else if (v !== false && v != null) n.setAttribute(k, v);
  }
  for (const k of kids.flat()) if (k != null && k !== false) n.append(k);
  return n;
};
const T = () => UI[app.lang];
const locale = () => (app.lang === "es" ? "es-CL" : "en-US");
const money = (n) => "$" + new Intl.NumberFormat(locale()).format(Math.round(n));
const pct = (n) => {
  const s = n.toLocaleString(locale(), { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  return app.lang === "es" ? `${s} %` : `${s}%`;
};
const dec = (n) => n.toLocaleString(locale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const shortDate = (iso) => new Date(iso + "T12:00:00").toLocaleDateString(locale(), { day: "numeric", month: "short" });

function load(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode: the list just won't persist */ }
}

let toastTimer = 0;
function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("on");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("on"), 3200);
}

/* ---------- items: demo cases + products the user added ---------- */

function statusOf(action) {
  return {
    alert: { cls: "st-alert", icon: "check" },
    stay_silent: { cls: "st-silent", icon: "minus" },
    alert_with_warning: { cls: "st-warn", icon: "warn" },
    watching: { cls: "st-watch", icon: "eye" },
  }[action];
}

function statusPill(action, big) {
  const s = statusOf(action);
  return h("span", { class: `status ${s.cls}${big ? " status-lg" : ""}` }, icon(s.icon, big ? 18 : 14), T().action[action]);
}

function deltaOf(c) {
  const p = c.stats.real_discount_pct;
  return { kind: p >= 0.05 ? "below" : p <= -0.05 ? "above" : "at", pct: pct(Math.abs(p)) };
}

function items() {
  const cases = (app.data[app.lang]?.cases ?? []).map((c) => ({
    id: c.id, name: c.product, store: c.store_label, price: c.current, photo: kindOf(c.product), action: c.verdict.action, c,
    fact: deltaOf(c),
  }));
  const mine = app.mine
    .map((id) => CATALOG.find((x) => x.id === id))
    .filter(Boolean)
    .map((x) => ({ id: "mine-" + x.id, name: T().catalog[x.id], store: x.store, price: x.price, photo: x.id, action: "watching", fact: { kind: "watching" }, mine: x.id }));
  return [...mine.reverse(), ...cases];
}

/* ---------- routing ---------- */

function route() {
  const hash = location.hash.replace(/^#\/?/, "");
  if (hash === "add") return { view: "add" };
  if (hash.startsWith("p/")) return { view: "detail", id: decodeURIComponent(hash.slice(2)) };
  return { view: "list" };
}

let firstRender = true;
function render({ focus = false } = {}) {
  const r = route();
  const list = items();
  let view = r.view;
  let current = null;
  if (view === "detail") {
    current = list.find((i) => i.id === r.id);
    if (!current) view = "list";
  }
  if (view === "list") {
    current = list.find((i) => i.c) ?? list[0];  // home: a judged offer, so the first thing seen is a verdict
    view = current ? "detail" : "list";
  }
  document.body.dataset.view = view;

  renderList(list, current && view === "detail" ? current.id : null);
  const pane = document.getElementById("pane-main");
  pane.replaceChildren();
  if (view === "add") pane.append(addView());
  else if (current) pane.append(detailView(current));
  else pane.append(h("p", { class: "state", text: T().pickOne }));
  pane.firstElementChild?.classList.add("enter");
  if (current && current.c) drawCharts(pane);
  if (view === "add") document.getElementById("add-q")?.focus({ preventScroll: true });

  if (focus && !firstRender) {
    window.scrollTo({ top: 0, behavior: "auto" });
    if (view !== "add") pane.focus({ preventScroll: true });
  }
  firstRender = false;
}

/* ---------- chrome: brand, language, static strings ---------- */

function renderChrome() {
  const t = T();
  document.documentElement.lang = app.lang;
  document.title = t.htmlTitle;
  document.getElementById("brand").replaceChildren(logoMark(28), "Dealjudge");
  document.getElementById("tagline").textContent = t.tagline;
  document.getElementById("sim").textContent = t.sim;
  document.getElementById("skip").textContent = app.lang === "es" ? "Saltar al contenido" : "Skip to content";
  const box = document.getElementById("lang");
  box.setAttribute("aria-label", t.langLabel);
  box.replaceChildren(...LANGS.map((l) =>
    h("button", { type: "button", "aria-pressed": String(l === app.lang), lang: l, "aria-label": l === "es" ? "Español" : "English", text: l.toUpperCase(), onclick: () => setLang(l) })));
}

async function setLang(lang) {
  if (lang === app.lang && app.data[lang]) return;
  app.lang = lang;
  save(STORE_KEY + ".lang", lang);
  renderChrome();
  await ensureData();
  render();
}

async function ensureData() {
  if (app.data[app.lang]) return true;
  try {
    const res = await fetch(`data/demo.${app.lang}.json`);
    if (!res.ok) throw new Error(res.status);
    app.data[app.lang] = await res.json();
    return true;
  } catch (err) {
    const pane = document.getElementById("pane-main");
    document.body.dataset.view = "detail";
    document.getElementById("pane-list").replaceChildren();
    pane.replaceChildren(h("div", { class: "state", role: "alert" },
      h("p", { text: T().loadError }),
      h("button", { class: "btn btn-ghost", type: "button", text: T().retry, onclick: async () => { if (await ensureData()) render(); } })));
    return false;
  }
}

/* ---------- list ---------- */

// Wide screens: the list sits at the left. Narrow ones: it sits below the verdict.
function renderList(list, currentId) {
  const t = T();
  const pane = document.getElementById("pane-list");
  pane.replaceChildren(
    h("div", { class: "list-head" },
      h("div", null,
        h("h2", { class: "list-title", id: "list-title", text: t.myProducts }),
        h("p", { class: "list-count", text: t.watchedCount(list.length) })),
      h("a", { class: "btn btn-ghost", href: "#/add" }, icon("plus", 18), t.add)),
    h("ul", { class: "items", role: "list" }, list.map((it) => h("li", null, itemLink(it, it.id === currentId)))));
}

function itemLink(it, selected) {
  const t = T();
  return h("a", { class: "item", href: "#/p/" + encodeURIComponent(it.id), "aria-current": selected ? "page" : null },
    photo(it.photo, 52),
    h("span", null,
      h("span", { class: "item-name", text: it.name }), h("br"),
      h("span", { class: "item-store", text: it.store }), h("br"),
      h("span", { class: "item-price", text: money(it.price) })),
    h("span", { class: "item-side" }, statusPill(it.action), h("span", { class: "item-fact", text: t.listFact(it.fact) })));
}

/* ---------- detail ---------- */

function backLink() {
  return h("a", { class: "btn btn-quiet back", href: "#/" }, icon("back", 18), T().back);
}

function detailView(it) {
  return it.c ? verdictView(it) : watchingView(it);
}

function watchingView(it) {
  const t = T();
  return h("article", null,
    h("header", { class: "d-head" }, photo(it.photo, 72),
      h("div", null, h("h1", { class: "d-title", text: it.name }), h("p", { class: "d-meta", text: it.store }))),
    h("div", { class: "verdict" },
      statusPill("watching", true),
      h("p", { class: "verdict-fact", text: t.watchingFact(money(it.price)) }),
      h("p", { class: "watch-body", text: t.watchingBody })),
    h("section", { class: "sec" }, h("h3", { text: t.chartHeading(90) }), h("div", { class: "chart-empty", text: t.watchingChart })),
    h("div", { class: "row-actions" },
      h("button", { class: "btn btn-ghost", type: "button", onclick: () => removeMine(it) }, icon("trash", 18), t.remove)));
}

function verdictView(it) {
  const t = T();
  const c = it.c, v = c.verdict, s = c.stats;
  const d = it.fact;
  const fact = d.kind === "below" ? t.factBelow(money(c.current), d.pct, money(c.baseline_median))
    : d.kind === "above" ? t.factAbove(money(c.current), d.pct, money(c.baseline_median))
    : t.factAt(money(c.current), money(c.baseline_median));
  const warnFn = t.warnBody[v.reason_code] || t.warnBody._;

  return h("article", null,
    h("header", { class: "d-head" }, photo(it.photo, 72),
      h("div", null, h("h1", { class: "d-title", text: it.name }), h("p", { class: "d-meta", text: t.storeMeta(c.store_label, s.days_of_history) }))),

    h("div", { class: `verdict ${statusOf(v.action).cls}` },
      h("p", { class: "verdict-action" }, icon(statusOf(v.action).icon, 26), t.action[v.action]),
      h("p", { class: "verdict-fact", text: fact }),
      s.spike_peak ? h("p", { class: "verdict-spike", text: t.factSpike(money(s.spike_peak), c.advertised_list_price ? money(c.advertised_list_price) : null) }) : null,
      v.action === "alert_with_warning"
        ? h("div", { class: "warn", role: "note" }, icon("warn", 22),
            h("div", null, h("h3", { text: t.warnTitle }), h("p", { text: warnFn(s.days_of_history) })))
        : null),

    deciderView(c),

    v.action !== "stay_silent"
      ? h("section", { class: "sec" }, h("h2", { text: t.noticeAlert }), h("p", { class: "notice", text: c.notice }))
      : null,

    h("section", { class: "sec" },
      h("h2", { text: t.figures }),
      factsList(c),
      h("details", { class: "fold" },
        h("summary", null, icon("chart", 18), t.chartToggle(c.series.length)),
        h("figure", { class: "chart" },
          h("div", { class: "chart-box", "data-case": c.id }),
          h("figcaption", { text: t.chartCaption })))),

    h("p", { class: "fine" }, t.fine, " ", h("span", { class: "mono", text: c.id })));
}

/* ---------- how Decider decided: the three typed answers, then the code rule ---------- */

function meter(value, label, thr) {
  const at = (x) => `${Math.round(Math.min(Math.max(x, 0), 1) * 100)}%`;
  return h("span", { class: "meter", role: "img", "aria-label": `${label}, ${T().thrTick} ${dec(thr)}` },
    h("i", { style: `width:${at(value)}` }), h("u", { style: `left:${at(thr)}`, title: `${T().thrTick} ${dec(thr)}` }));
}

function deciderView(c) {
  const t = T(), v = c.verdict, m = c.decider;
  const thr = app.data[app.lang].threshold;
  if (!m || m.failed) {
    return h("section", { class: "sec decider" }, h("h2", { text: t.deciderHeading }),
      h("p", { class: "decider-lead", text: m?.failed ? t.deciderFailed : t.deciderLead(dec(thr)) }));
  }
  const yn = (p) => (p >= 0.5 ? t.yes : t.no);
  const sure = (p) => Math.max(p, 1 - p);
  const realSure = sure(m.is_real_p);
  const row = (q, answer, conf, note, key) =>
    h("li", { class: "q", "data-q": key },
      h("span", { class: "q-text", text: q }),
      h("b", { class: "q-answer", text: answer }),
      conf == null
        ? h("span", { class: "q-code", text: t.byCode })
        : h("span", { class: "q-conf" }, meter(conf, `${t.sure} ${dec(conf)}`, thr), h("span", { class: "q-num", text: `${t.sure} ${dec(conf)}` })),
      note ? h("span", { class: "q-note", text: note }) : null);

  const fitsByCode = m.fits_used != null;
  const rows = [
    row(t.qReal, yn(m.is_real_p), realSure, null, "is_real"),
    row(t.qLevel, t.level[v.level] ?? v.level, m.level_conf, null, "level"),
    fitsByCode
      ? row(t.qFits, m.fits_used >= 0.5 ? t.yes : t.no, null, t.modelSaid(yn(m.fits_p), dec(sure(m.fits_p))), "fits")
      : row(t.qFits, yn(m.fits_p), sure(m.fits_p), null, "fits"),
  ];

  return h("section", { class: "sec decider", "aria-labelledby": "decider-h" },
    h("p", { class: "eyebrow", text: t.deciderEyebrow }),
    h("h2", { id: "decider-h", text: t.deciderHeading }),
    h("p", { class: "decider-lead", text: t.deciderLead(dec(thr)) }),
    h("ol", { class: "qs" }, rows),
    h("div", { class: "rule" },
      h("h3", { text: t.ruleHeading }),
      confScale(v.confidence, thr),
      h("p", { class: "rule-out" }, statusPill(v.action), h("span", { text: " " + v.reason })),
      h("p", { class: "conf-body", text: t.confBody(dec(v.confidence), dec(thr), v.reason_code) })),
    m.latency_ms != null ? h("p", { class: "latency", text: t.latency(m.latency_ms) }) : null);
}

function factsList(c) {
  const t = T(), s = c.stats;
  const rows = [
    [t.priceToday, money(c.current)],
    c.advertised_list_price ? [t.listPrice, money(c.advertised_list_price), "struck"] : null,
    [t.median, money(c.baseline_median)],
    [t.minimum, money(s.min_price)],
    [t.realDiscount, pct(s.real_discount_pct)],
    [t.lastDrop, s.days_since_last_drop == null ? t.never : s.days_since_last_drop === 0 ? t.today : t.daysAgo(s.days_since_last_drop)],
    [app.lang === "es" ? "Nivel de oferta" : "Offer level", t.level[c.verdict.level] ?? c.verdict.level],
  ].filter(Boolean);
  return h("dl", { class: "facts" }, rows.map(([k, val, cls]) => h("div", null, h("dt", { text: k }), h("dd", { class: cls || "", text: val }))));
}

function confScale(conf, thr) {
  const t = T();
  const at = (x) => `${Math.min(Math.max(x, 0), 1) * 100}%`;
  return h("div", null,
    h("div", { class: "scale", role: "img", "aria-label": `${t.confScale}: ${t.confSignal} ${dec(conf)}, ${t.confThreshold} ${dec(thr)}` },
      h("div", { class: "scale-track" }),
      h("div", { class: "scale-mark thr", style: `left:${at(thr)}` }, `${t.confThreshold} ${dec(thr)}`, h("i")),
      h("div", { class: "scale-mark sig", style: `left:${at(conf)}` }, h("i"), `${t.confSignal} ${dec(conf)}`)),
    h("div", { class: "scale-ends" }, h("span", { text: "0" }), h("span", { text: "1" })));
}

/* ---------- 90-day chart ---------- */

const NS = "http://www.w3.org/2000/svg";
const s = (tag, attrs, text) => {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, v);
  if (text !== undefined) n.textContent = text;
  return n;
};

function drawCharts(root) {
  root.querySelectorAll(".chart-box").forEach((box) => {
    const c = app.data[app.lang].cases.find((x) => x.id === box.dataset.case);
    if (!c) return;
    let last = 0;
    const paint = () => {
      const w = Math.floor(box.clientWidth);
      if (!w || w === last) return;
      last = w;
      chart(box, c, w);
    };
    paint();
    if ("ResizeObserver" in window) new ResizeObserver(paint).observe(box);
  });
}

function chart(box, c, width) {
  const t = T();
  const prices = c.series.map((p) => p.price);
  const n = prices.length;
  const W = Math.max(280, width - 16), H = W < 480 ? 230 : 280;
  const L = W < 420 ? 54 : 62, R = 12, TOP = 28, B = 28;
  const hi = Math.max(...prices, c.baseline_median), lo = Math.min(...prices, c.baseline_median);
  const pad = (hi - lo) * 0.14 || hi * 0.05;
  const y0 = lo - pad, y1 = hi + pad;
  const x = (i) => L + (i / Math.max(n - 1, 1)) * (W - L - R);
  const y = (val) => TOP + (1 - (val - y0) / (y1 - y0)) * (H - TOP - B);

  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", tabindex: 0,
    "aria-label": t.chartAria(n, c.product, money(c.current), money(c.baseline_median)) + " " + t.chartHint });

  for (let k = 0; k < 4; k++) {
    const val = y0 + ((y1 - y0) * (k + 0.5)) / 4, yy = y(val);
    svg.append(s("line", { x1: L, x2: W - R, y1: yy, y2: yy, class: "grid" }));
    svg.append(s("text", { x: L - 8, y: yy + 4, "text-anchor": "end" }, money(Math.round(val / 100) * 100)));
  }
  const ym = y(c.baseline_median);
  svg.append(s("line", { x1: L, x2: W - R, y1: ym, y2: ym, class: "median" }));

  svg.append(s("polyline", { class: "line", points: prices.map((p, i) => `${x(i).toFixed(1)},${y(p).toFixed(1)}`).join(" ") }));

  // The inflated stretch gets its own colour AND a label, so it never relies on colour alone.
  const peak = c.stats.spike_peak;
  if (peak) {
    const cut = c.baseline_median * 1.15;
    let run = [];
    const flush = () => { if (run.length > 1) svg.append(s("polyline", { class: "line-spike", points: run.join(" ") })); run = []; };
    prices.forEach((p, i) => { if (p >= cut) run.push(`${x(i).toFixed(1)},${y(p).toFixed(1)}`); else flush(); });
    flush();
    const pi = prices.indexOf(Math.max(...prices));
    const right = x(pi) > W * 0.55;
    svg.append(s("text", { x: x(pi) + (right ? -8 : 8), y: y(prices[pi]) + 4, "text-anchor": right ? "end" : "start", class: "t-peak halo" }, t.chartPeak(money(prices[pi]))));
  }

  const mx = L + 6;
  svg.append(s("text", { x: mx, y: ym - 8, class: "t-median halo" }, t.chartMedian(money(c.baseline_median))));

  const lx = x(n - 1), ly = y(c.current);
  svg.append(s("circle", { cx: lx, cy: ly, r: 5, class: "today" }));
  const above = c.current <= c.baseline_median;
  svg.append(s("text", { x: lx - 10, y: ly + (above ? 20 : -12), "text-anchor": "end", class: "t-today halo" }, t.chartToday(money(c.current))));
  svg.append(s("text", { x: L, y: H - 8 }, t.chartDaysAgo(n - 1)));
  svg.append(s("text", { x: W - R, y: H - 8, "text-anchor": "end" }, t.chartNow));

  const cursor = s("line", { class: "cursor", y1: TOP, y2: H - B, opacity: 0 });
  const dot = s("circle", { class: "cursor-dot", r: 4.5, opacity: 0 });
  svg.append(cursor, dot);

  const tip = h("div", { class: "chart-tip", role: "status" });
  const show = (i) => {
    i = Math.min(Math.max(i, 0), n - 1);
    const px = x(i);
    cursor.setAttribute("x1", px); cursor.setAttribute("x2", px); cursor.setAttribute("opacity", 1);
    dot.setAttribute("cx", px); dot.setAttribute("cy", y(prices[i])); dot.setAttribute("opacity", 1);
    tip.replaceChildren(h("b", { text: money(prices[i]) }), " · " + shortDate(c.series[i].day));
    tip.classList.add("on");
    const half = tip.offsetWidth / 2;
    tip.style.left = Math.min(Math.max(px + 8 - half, 8), box.clientWidth - tip.offsetWidth - 8) + "px";
    return i;
  };
  const hide = () => { cursor.setAttribute("opacity", 0); dot.setAttribute("opacity", 0); tip.classList.remove("on"); };
  const indexAt = (clientX) => {
    const r = svg.getBoundingClientRect();
    const px = ((clientX - r.left) / r.width) * W;
    return Math.round(((px - L) / (W - L - R)) * (n - 1));
  };
  let kb = n - 1;
  svg.addEventListener("pointermove", (e) => { kb = show(indexAt(e.clientX)); });
  svg.addEventListener("pointerdown", (e) => { kb = show(indexAt(e.clientX)); });
  svg.addEventListener("pointerleave", hide);
  svg.addEventListener("blur", hide);
  svg.addEventListener("keydown", (e) => {
    const step = { ArrowLeft: -1, ArrowRight: 1, PageUp: -7, PageDown: 7 }[e.key];
    if (e.key === "Home") kb = show(0);
    else if (e.key === "End") kb = show(n - 1);
    else if (step) kb = show(kb + step);
    else if (e.key === "Escape") return hide();
    else return;
    e.preventDefault();
  });

  box.replaceChildren(svg, tip);
}

/* ---------- add and confirm a product ---------- */

const fold2 = (str) => fold(str).replace(/[^a-z0-9]+/g, " ").trim();

function search(q) {
  const tokens = fold2(q).split(" ").filter((w) => w.length >= 2);
  if (!tokens.length) return [];
  return CATALOG
    .map((p) => {
      const names = fold2(UI.es.catalog[p.id] + " " + UI.en.catalog[p.id]);
      const score = tokens.filter((tk) => p.words.some((w) => w.includes(tk) || (tk.length >= 4 && tk.includes(w))) || names.includes(tk)).length;
      return { p, score };
    })
    .filter((m) => m.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((m) => m.p);
}

function addView() {
  const t = T();
  const a = app.add;
  const form = h("form", { class: "field", novalidate: true, onsubmit: (e) => { e.preventDefault(); runSearch(document.getElementById("add-q").value); } },
    h("label", { for: "add-q", text: t.addLabel }),
    h("div", { class: "field-row" },
      h("input", { class: "input", id: "add-q", name: "q", type: "text", autocomplete: "off", enterkeyhint: "search", placeholder: t.addPlaceholder, value: a.q }),
      h("button", { class: "btn btn-primary", type: "submit" }, icon("search", 18), t.addSubmit)),
    h("div", { class: "chips" }, h("span", { class: "chips-label", text: t.addTry }), suggestionChips()));
  return h("article", null,
    backLink(),
    h("h1", { class: "d-title", text: t.addTitle }),
    h("p", { class: "add-lead", text: t.addLead }),
    form,
    h("div", { class: "agent", id: "agent", "aria-live": "polite" }, agentBlock()),
    h("p", { class: "add-note", text: t.addSimNote }));
}

function suggestionChips() {
  return CATALOG.slice(0, 4).map((p) => h("button", { class: "chip", type: "button", text: T().catalog[p.id],
    onclick: () => { document.getElementById("add-q").value = T().catalog[p.id]; runSearch(T().catalog[p.id]); } }));
}

function refreshAgent() {
  const box = document.getElementById("agent");
  if (box) box.replaceChildren(...[].concat(agentBlock()));
}

function runSearch(q) {
  const a = app.add;
  clearTimeout(app.addTimer);
  a.q = q.trim();
  a.error = "";
  if (!a.q) { a.stage = "input"; return refreshAgent(); }
  a.stage = "loading";
  refreshAgent();
  app.addTimer = setTimeout(() => {
    a.matches = search(a.q);
    a.idx = 0;
    a.stage = a.matches.length ? "found" : "none";
    refreshAgent();
  }, REDUCED.matches ? 0 : 650);
}

function agentBlock() {
  const t = T(), a = app.add;
  if (a.stage === "loading") return h("p", { class: "agent-status" }, icon("spinner", 18), t.addLooking);
  if (a.stage === "none") {
    return h("p", { class: "error" }, icon("info", 18), t.addNone(a.q));
  }
  if (a.stage === "found") {
    const p = a.matches[a.idx];
    return h("div", { class: "understood" },
      h("h3", { text: t.addUnderstood }),
      h("div", { class: "u-main" }, photo(p.id, 72), h("p", { class: "u-name", text: t.catalog[p.id] })),
      h("dl", { class: "u-dl" },
        h("div", null, h("dt", { text: t.addStore }), h("dd", { text: p.store })),
        h("div", null, h("dt", { text: t.addPrice }), h("dd", { text: money(p.price) }))),
      h("p", { class: "u-q", text: t.addQuestion }),
      a.error ? h("p", { class: "error" }, icon("info", 18), a.error) : null,
      h("div", { class: "row-actions" },
        h("button", { class: "btn btn-primary", type: "button", id: "add-confirm", onclick: () => confirmAdd(p) }, icon("check", 18), t.addConfirm),
        h("button", { class: "btn btn-ghost", type: "button", onclick: rejectMatch }, t.addReject)));
  }
  return [];
}

function rejectMatch() {
  const a = app.add;
  a.error = "";
  if (a.idx + 1 < a.matches.length) { a.idx += 1; return refreshAgent(); }
  a.stage = "input";
  a.q = "";
  const q = document.getElementById("add-q");
  if (q) { q.value = ""; q.focus(); }
  refreshAgent();
  const box = document.getElementById("agent");
  if (box) box.replaceChildren(h("p", { class: "error" }, icon("info", 18), T().addNoMore));
}

function confirmAdd(p) {
  if (app.mine.includes(p.id)) { app.add.error = T().addAlready; return refreshAgent(); }
  app.mine.push(p.id);
  save(STORE_KEY + ".mine", app.mine);
  app.add = { q: "", stage: "input", matches: [], idx: 0, error: "" };
  toast(T().added(T().catalog[p.id]));
  location.hash = "#/p/mine-" + p.id;
}

function removeMine(it) {
  app.mine = app.mine.filter((id) => id !== it.mine);
  save(STORE_KEY + ".mine", app.mine);
  toast(T().removed(it.name));
  location.hash = "#/";
}

/* ---------- boot ---------- */

async function boot() {
  const param = new URLSearchParams(location.search).get("lang");
  const stored = load(STORE_KEY + ".lang", null);
  const guess = (navigator.language || "es").toLowerCase().startsWith("es") ? "es" : "en";
  app.lang = [param, stored, guess].find((l) => LANGS.includes(l));
  const mine = load(STORE_KEY + ".mine", []);
  app.mine = Array.isArray(mine) ? mine.filter((id) => CATALOG.some((x) => x.id === id)) : [];

  renderChrome();
  if (!(await ensureData())) return;
  render();
  window.addEventListener("hashchange", () => render({ focus: true }));
}

boot();
