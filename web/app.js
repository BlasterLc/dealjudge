"use strict";

const LEVELS_ES = { sin_oferta: "sin oferta", marginal: "marginal", buena: "buena", muy_buena: "muy buena", excepcional: "excepcional" };
const clp = (n) => "$" + new Intl.NumberFormat("es-CL").format(n);
const pct = (n) => n.toLocaleString("es-CL", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

const STAMPS = {
  avisar: { label: "Avisar", kind: "alert" },
  callar: { label: "No avisar", kind: "silent" },
  avisar_con_advertencia: { label: "Avisar con cautela", kind: "caution" },
};

function headline(c) {
  const v = c.verdict;
  if (v.action === "callar") {
    return c.stats.spike_peak ? "No es un descuento real: el precio estaba inflado" : "No hay una oferta real";
  }
  if (v.action === "avisar_con_advertencia") return "Podría ser buena, pero hay dudas";
  return `Descuento real: oferta ${LEVELS_ES[v.level] || v.level}`;
}

function daysText(n) {
  if (n === null || n === undefined) return "sin bajas";
  if (n === 0) return "hoy";
  return n === 1 ? "hace 1 día" : `hace ${n} días`;
}

function chart(c, width) {
  const W = Math.max(280, Math.round(width)), H = W < 420 ? 220 : 250, L = W < 420 ? 52 : 64, R = 14, T = 14, B = 30;
  const prices = c.series.map((p) => p.price);
  const hi = Math.max(...prices, c.baseline_median), lo = Math.min(...prices, c.baseline_median);
  const pad = (hi - lo) * 0.12 || hi * 0.05;
  const y0 = lo - pad, y1 = hi + pad;
  const x = (i) => L + (i / Math.max(prices.length - 1, 1)) * (W - L - R);
  const y = (v) => T + (1 - (v - y0) / (y1 - y0)) * (H - T - B);
  const NS = "http://www.w3.org/2000/svg";
  const s = (tag, attrs, text) => {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, v);
    if (text !== undefined) n.textContent = text;
    return n;
  };
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": `Precio de los últimos ${prices.length} días de ${c.product}: hoy ${clp(c.current)}, mediana ${clp(c.baseline_median)}.` });

  for (let k = 0; k < 3; k++) {
    const v = y0 + ((y1 - y0) * (k + 0.5)) / 3, yy = y(v);
    svg.append(s("line", { x1: L, x2: W - R, y1: yy, y2: yy, class: "grid" }));
    svg.append(s("text", { x: L - 8, y: yy + 4, "text-anchor": "end" }, clp(Math.round(v / 100) * 100)));
  }
  const ym = y(c.baseline_median);
  svg.append(s("line", { x1: L, x2: W - R, y1: ym, y2: ym, class: "median" }));
  svg.append(s("text", { x: L + 6, y: ym - 6 }, `mediana ${clp(c.baseline_median)}`));

  const inflated = c.stats.spike_peak ? c.baseline_median * 1.15 : Infinity;
  svg.append(s("polyline", { class: "line", points: prices.map((p, i) => `${x(i)},${y(p)}`).join(" ") }));
  const spike = prices.map((p, i) => (p >= inflated ? [x(i), y(p)] : null));
  if (spike.some(Boolean)) {
    svg.append(s("polyline", { class: "line-spike", points: spike.filter(Boolean).map(([a, b]) => `${a},${b}`).join(" ") }));
    const peakI = prices.indexOf(Math.max(...prices));
    svg.append(s("text", { x: Math.min(x(peakI), W - R - 4), y: y(prices[peakI]) - 8, "text-anchor": "end", class: "note-red" }, `pico inflado ${clp(prices[peakI])}`));
  }
  const last = prices.length - 1;
  svg.append(s("circle", { cx: x(last), cy: y(c.current), r: 4.5, class: "today" }));
  svg.append(s("text", { x: x(last) - 8, y: y(c.current) + (c.current <= c.baseline_median ? 18 : -10), "text-anchor": "end" }, `hoy ${clp(c.current)}`));
  svg.append(s("text", { x: L, y: H - 8 }, `hace ${last} d`));
  svg.append(s("text", { x: W - R, y: H - 8, "text-anchor": "end" }, "hoy"));

  const fig = el("figure", "chart");
  fig.append(svg, el("figcaption", "", "Precio diario. La línea punteada es la mediana de los 90 días anteriores a cualquier subida reciente."));
  return fig;
}

function receipt(c, threshold) {
  const root = document.getElementById("receipt");
  root.replaceChildren();
  const cs = getComputedStyle(root);
  const inner = root.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  const stamp = STAMPS[c.verdict.action];
  const big = el("span", `stamp stamp-big ${stamp.kind}`, stamp.label);
  big.setAttribute("aria-hidden", "true");

  root.append(big, el("h2", "product", c.product), el("p", "store", `${c.store_label} · ${c.stats.days_of_history} días de historial`));
  root.append(el("p", "verdict", headline(c)));
  if (c.verdict.action !== "callar") root.append(el("p", "reason", c.verdict.reason));

  const lines = el("dl", "lines");
  const row = (label, value, cls) => {
    const d = el("div"), dt = el("dt", "", label), dd = el("dd", cls || "", value);
    d.append(dt, dd);
    lines.append(d);
  };
  row("Precio hoy", clp(c.current));
  if (c.advertised_list_price) row("Anunciado por la tienda", clp(c.advertised_list_price), "struck");
  row("Mediana de 90 días", clp(c.baseline_median));
  row("Mínimo de 90 días", clp(c.stats.min_price));
  row("Descuento real", `${pct(c.stats.real_discount_pct)} %`);
  row("Última baja", daysText(c.stats.days_since_last_drop));
  root.append(lines);

  root.append(el("h3", "section", "El precio"), chart(c, inner));

  root.append(el("h3", "section", c.verdict.action === "callar" ? "Por qué no avisó" : "Lo que recibirías"));
  root.append(el("p", c.verdict.action === "callar" ? "message muted" : "message", c.notice));

  const t = threshold === null || threshold === undefined ? "" : `, umbral ${String(threshold).replace(".", ",")}`;
  root.append(el("p", "fine",
    `Decider 2B leyó el historial: nivel ${LEVELS_ES[c.verdict.level] || c.verdict.level}, confianza ${String(c.verdict.confidence).replace(".", ",")}${t}. ` +
    "El modelo mide; la regla de aviso es código. Datos simulados, tiendas ficticias."));
}

let current = null;

function select(cases, i, threshold, list) {
  current = { cases, i, threshold };
  [...list.children].forEach((li, k) => li.firstElementChild.setAttribute("aria-current", k === i ? "true" : "false"));
  receipt(cases[i], threshold);
}

async function main() {
  const data = await (await fetch("data/demo.json")).json();
  const list = document.getElementById("roll");
  data.cases.forEach((c, i) => {
    const li = el("li");
    const b = el("button", "ticket");
    b.type = "button";
    const stamp = STAMPS[c.verdict.action];
    b.append(el("span", "ticket-name", c.product));
    const meta = el("span", "ticket-meta");
    meta.append(el("span", "", c.store_label), el("span", "ticket-price", clp(c.current)));
    b.append(meta);
    const sw = el("span", "ticket-stamp");
    sw.append(el("span", `stamp ${stamp.kind}`, stamp.label));
    b.append(sw);
    b.addEventListener("click", () => {
      select(data.cases, i, data.threshold, list);
      if (window.matchMedia("(max-width: 880px)").matches) {
        document.getElementById("receipt").scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      }
    });
    li.append(b);
    list.append(li);
  });
  select(data.cases, 0, data.threshold, list);
}

let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => current && receipt(current.cases[current.i], current.threshold), 150);
});

main().catch((err) => {
  document.getElementById("receipt").textContent = "No se pudieron cargar los datos de la demo: " + err.message;
});
