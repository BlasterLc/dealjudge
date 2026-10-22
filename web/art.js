"use strict";

// Authored SVG: UI icons (24 grid, 1.75 stroke) and flat product illustrations (48 grid).
// Illustrations stand in for store photos: the stores and products are fictional.

const SVG_NS = "http://www.w3.org/2000/svg";

const ICONS = {
  check: '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.8 2.8L16 9.5"/>',
  minus: '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
  warn: '<path d="M12 3.5 21.5 20h-19z"/><path d="M12 10v4.5M12 17.2v.1"/>',
  eye: '<path d="M2.5 12s3.5-6.5 9.5-6.5S21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  back: '<path d="M15 5l-7 7 7 7"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.8v.1"/>',
  trash: '<path d="M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 12.5h9l1-12.5"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  spinner: '<path d="M12 3a9 9 0 1 0 9 9"/>',
};

const ART = {
  headphones:
    '<path d="M10 27v-3a14 14 0 0 1 28 0v3"/><rect x="7" y="26" width="8" height="13" rx="3.5"/><rect x="33" y="26" width="8" height="13" rx="3.5"/>',
  ssd:
    '<rect x="8" y="12" width="32" height="24" rx="4"/><path d="M14 20h10M14 26h6"/><circle cx="33" cy="28" r="2.2"/>',
  airfryer:
    '<path d="M11 14a13 13 0 0 1 26 0v1H11z"/><path d="M12 15v17a4 4 0 0 0 4 4h16a4 4 0 0 0 4-4V15"/><path d="M19 26h10M24 20v2"/>',
  vacuum:
    '<circle cx="24" cy="26" r="15"/><circle cx="24" cy="26" r="5"/><path d="M24 11v5M14 14l3 3"/>',
  keyboard:
    '<rect x="5" y="13" width="38" height="22" rx="4"/><path d="M11 20h2M17 20h2M23 20h2M29 20h2M35 20h2M11 26h2M17 26h14M35 26h2"/>',
  watch:
    '<path d="M18 10h12l1.5 6h-15zM18 38h12l1.5-6h-15z"/><rect x="14" y="16" width="20" height="16" rx="5"/><path d="M24 20.5V24l2.5 1.8"/>',
  laptop:
    '<rect x="10" y="12" width="28" height="19" rx="3"/><path d="M5 36h38l-2.5-5h-33z"/>',
  shoe:
    '<path d="M6 32c0-5 3-7 6-8l6-2 4 4 8 2c4 1 8 3 8 8v1H6z"/><path d="M6 36h36M20 26l-2 3M25 28l-2 3"/>',
};

function svgEl(markup, size, cls, viewBox) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", viewBox);
  svg.setAttribute("width", size);
  svg.setAttribute("height", size);
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", viewBox === "0 0 24 24" ? "1.75" : "1.9");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  if (cls) svg.setAttribute("class", cls);
  svg.innerHTML = markup;
  return svg;
}

const icon = (name, size = 20, cls = "") => svgEl(ICONS[name], size, "icon " + cls, "0 0 24 24");

// A framed illustration tile standing in for the product photo.
function photo(kind, size = 56) {
  const tile = document.createElement("span");
  tile.className = "photo";
  tile.style.setProperty("--size", size + "px");
  if (ART[kind]) tile.append(svgEl(ART[kind], Math.round(size * 0.66), "photo-art", "0 0 48 48"));
  return tile;
}

// The mark: a judge's gavel, black on white.
function logoMark(size = 28) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 32 32");
  svg.setAttribute("width", size);
  svg.setAttribute("height", size);
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("class", "logo-mark");
  svg.innerHTML =
    '<rect width="32" height="32" rx="8" fill="currentColor"/>' +
    '<g fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">' +
    '<rect x="11.5" y="5.5" width="11" height="6.5" rx="1.6" transform="rotate(38 17 9)" fill="#fff" stroke="none"/>' +
    '<path d="M15.5 14.5 7 23"/><path d="M6 26.5h10"/></g>';
  return svg;
}

// Which illustration a product name gets, whatever the language it arrives in.
const KIND_WORDS = [
  ["headphones", ["audifon", "headphone", "auricular"]],
  ["ssd", ["ssd"]],
  ["airfryer", ["freidora", "air fryer"]],
  ["vacuum", ["aspiradora", "vacuum"]],
  ["keyboard", ["teclado", "keyboard"]],
  ["watch", ["smartwatch", "reloj"]],
  ["laptop", ["notebook", "laptop"]],
  ["shoe", ["zapatilla", "running shoe", "shoe"]],
];

const fold = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

function kindOf(name) {
  const n = fold(name);
  const hit = KIND_WORDS.find(([, words]) => words.some((w) => n.includes(w)));
  return hit ? hit[0] : "ssd";
}
