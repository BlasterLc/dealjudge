"use strict";

// Every string the interface shows lives here. The agent's own texts (verdict reason, alert text)
// come from data/demo.<lang>.json, written by the Python side in the same language.

const LANGS = ["es", "en"];

const UI = {
  es: {
    htmlTitle: "Dealjudge · ¿Es de verdad una oferta?",
    tagline: "¿Es de verdad una oferta?",
    langLabel: "Idioma",
    sim: "Datos simulados · tiendas ficticias · precios en CLP",
    myProducts: "Mis productos",
    watchedCount: (n) => (n === 1 ? "1 producto vigilado" : `${n} productos vigilados`),
    add: "Agregar producto",
    back: "Mis productos",
    loadError: "No se pudieron cargar los datos de la demo.",
    retry: "Reintentar",
    noscript: "Esta página necesita JavaScript para mostrar los veredictos.",
    notFound: "Ese producto ya no está en tu lista.",
    pickOne: "Elige un producto para ver su veredicto.",

    // statuses
    action: { alert: "Avisar", stay_silent: "Callar", alert_with_warning: "Avisar con cautela", watching: "Vigilando" },
    level: { no_deal: "sin oferta", marginal: "marginal", good: "buena", very_good: "muy buena", exceptional: "excepcional" },
    levelLine: (l) => `Oferta ${l}`,
    listFact: (c) => {
      if (c.kind === "watching") return "Reuniendo historial";
      if (c.kind === "below") return `${c.pct} bajo la mediana`;
      if (c.kind === "above") return `${c.pct} sobre la mediana`;
      return "En la mediana";
    },

    // verdict
    storeMeta: (store, days) => `${store} · ${days} días de historial`,
    factBelow: (price, pct, median) => `Hoy cuesta ${price}: ${pct} bajo la mediana de 90 días (${median}).`,
    factAbove: (price, pct, median) => `Hoy cuesta ${price}: ${pct} sobre la mediana de 90 días (${median}).`,
    factAt: (price, median) => `Hoy cuesta ${price}, igual que la mediana de 90 días (${median}).`,
    factSpike: (peak, list) =>
      list
        ? `El precio subió hasta ${peak} y la tienda anuncia ${list}: ese "antes" no es el precio de siempre.`
        : `El precio subió hasta ${peak} hace unas semanas.`,
    verdictHeading: "Veredicto",
    why: "Por qué",
    warnTitle: "Ten cautela con este veredicto",
    warnBody: {
      short_history: (days) => `Solo hay ${days} días de historial y se necesitan 14 para juzgar. Por regla, avisa con cautela antes de consultar al modelo.`,
      low_confidence: () => "Decider duda de su respuesta: su señal queda bajo el umbral. Compruébalo antes de comprar.",
      unreadable: () => "No se pudo leer con seguridad la respuesta del modelo. Compruébalo antes de comprar.",
      unknown_level: () => "No se pudo clasificar el nivel de la oferta. Compruébalo antes de comprar.",
      _: () => "Hay dudas sobre este veredicto. Compruébalo antes de comprar.",
    },
    chartHeading: (n) => (n >= 90 ? "Precio de los últimos 90 días" : `Precio de los últimos ${n} días`),
    chartCaption: "Precio diario. La línea punteada es la mediana de los 90 días anteriores a cualquier subida reciente.",
    chartAria: (n, product, cur, med) => `Precio de los últimos ${n} días de ${product}: hoy ${cur}, mediana ${med}.`,
    chartMedian: (v) => `mediana ${v}`,
    chartToday: (v) => `hoy ${v}`,
    chartPeak: (v) => `pico ${v}`,
    chartDaysAgo: (n) => `hace ${n} d`,
    chartNow: "hoy",
    chartHint: "Pasa el cursor o usa ← → para ver cada día.",
    figures: "Las cifras",
    priceToday: "Precio hoy",
    listPrice: "Anunciado por la tienda",
    median: "Mediana de 90 días",
    minimum: "Mínimo de 90 días",
    realDiscount: "Descuento real",
    lastDrop: "Última baja",
    never: "sin bajas",
    today: "hoy",
    daysAgo: (n) => (n === 1 ? "hace 1 día" : `hace ${n} días`),
    confHeading: "Cuánta seguridad tiene",
    confBody: (c, t, code) =>
      `La señal de Decider es ${c} y el umbral es ${t}. ${code === "short_history" ? "Aquí no decide la señal: con menos de 14 días de historial la regla avisa con advertencia antes de mirarla." : Number(c.replace(",", ".")) >= Number(t.replace(",", ".")) ? "Está sobre el umbral: la regla decide sin advertencia." : "Está bajo el umbral: la regla avisa con advertencia."} No es una probabilidad de acierto: esa señal vive en una escala baja y el umbral se calibró con datos.`,
    confScale: "Escala de la señal de Decider, de 0 a 1",
    confSignal: "señal",
    confThreshold: "umbral",
    noticeAlert: "Lo que recibirías",
    noticeSilent: "Por qué no avisó",
    fine: "Decider 2B mide; la regla de aviso es código; Bedrock solo redacta con las cifras del código.",

    // watching (just added)
    watchingFact: (price) => `Hoy cuesta ${price}. Todavía no hay historial para juzgarlo.`,
    watchingBody: "Dealjudge necesita 14 días de precios para dar un veredicto. Hasta entonces, si ve una baja, te avisará con cautela.",
    watchingChart: "El gráfico de 90 días aparece cuando haya historial.",
    remove: "Dejar de vigilar",
    removed: (name) => `Dejaste de vigilar ${name}.`,
    added: (name) => `Ahora vigilas ${name}.`,

    // add flow
    addTitle: "Agregar producto",
    addLead: "Escribe qué quieres vigilar. Te muestro lo que entendí y tú confirmas.",
    addLabel: "Producto",
    addPlaceholder: "Ej.: audífonos inalámbricos",
    addSubmit: "Buscar",
    addTry: "O prueba con",
    addLooking: "Buscando en las tiendas…",
    addUnderstood: "Esto entendí",
    addQuestion: "¿Es este el producto?",
    addConfirm: "Sí, vigilar este",
    addReject: "No es este",
    addNone: (q) => `No encontré «${q}» en la demo. Prueba con uno de estos:`,
    addNoMore: "No tengo más coincidencias. Prueba con otras palabras.",
    addAlready: "Ya vigilas este producto.",
    addStore: "Tienda",
    addPrice: "Precio hoy",
    addSimNote: "Búsqueda simulada: en la demo solo conozco unos pocos productos de tiendas ficticias.",
    cancel: "Cancelar",
    catalog: {
      headphones: "Audífonos inalámbricos",
      ssd: "SSD 1TB",
      airfryer: "Freidora de aire",
      vacuum: "Aspiradora robot",
      keyboard: "Teclado mecánico",
      watch: "Smartwatch",
      laptop: "Notebook gama media",
      shoe: "Zapatillas running",
    },
  },

  en: {
    htmlTitle: "Dealjudge · Is it really a deal?",
    tagline: "Is it really a deal?",
    langLabel: "Language",
    sim: "Simulated data · fictional stores · prices in CLP",
    myProducts: "My products",
    watchedCount: (n) => (n === 1 ? "1 product watched" : `${n} products watched`),
    add: "Add product",
    back: "My products",
    loadError: "The demo data could not be loaded.",
    retry: "Try again",
    noscript: "This page needs JavaScript to show the verdicts.",
    notFound: "That product is no longer in your list.",
    pickOne: "Pick a product to see its verdict.",

    action: { alert: "Alert", stay_silent: "Stay silent", alert_with_warning: "Alert with caution", watching: "Watching" },
    level: { no_deal: "no deal", marginal: "marginal", good: "good", very_good: "very good", exceptional: "exceptional" },
    levelLine: (l) => `Offer level: ${l}`,
    listFact: (c) => {
      if (c.kind === "watching") return "Gathering history";
      if (c.kind === "below") return `${c.pct} below the median`;
      if (c.kind === "above") return `${c.pct} above the median`;
      return "At the median";
    },

    storeMeta: (store, days) => `${store} · ${days} days of history`,
    factBelow: (price, pct, median) => `It costs ${price} today: ${pct} below the 90-day median (${median}).`,
    factAbove: (price, pct, median) => `It costs ${price} today: ${pct} above the 90-day median (${median}).`,
    factAt: (price, median) => `It costs ${price} today, the same as the 90-day median (${median}).`,
    factSpike: (peak, list) =>
      list
        ? `The price rose to ${peak} and the store advertises ${list}: that "before" is not the usual price.`
        : `The price rose to ${peak} a few weeks ago.`,
    verdictHeading: "Verdict",
    why: "Why",
    warnTitle: "Be careful with this verdict",
    warnBody: {
      short_history: (days) => `There are only ${days} days of history and 14 are needed to judge. By rule it alerts with caution before asking the model.`,
      low_confidence: () => "Decider doubts its own answer: its signal is below the threshold. Check before you buy.",
      unreadable: () => "The model's answer could not be read reliably. Check before you buy.",
      unknown_level: () => "The offer level could not be classified. Check before you buy.",
      _: () => "There are doubts about this verdict. Check before you buy.",
    },
    chartHeading: (n) => (n >= 90 ? "Price over the last 90 days" : `Price over the last ${n} days`),
    chartCaption: "Daily price. The dotted line is the median of the 90 days before any recent spike.",
    chartAria: (n, product, cur, med) => `Price of ${product} over the last ${n} days: today ${cur}, median ${med}.`,
    chartMedian: (v) => `median ${v}`,
    chartToday: (v) => `today ${v}`,
    chartPeak: (v) => `peak ${v}`,
    chartDaysAgo: (n) => `${n} d ago`,
    chartNow: "today",
    chartHint: "Hover or use ← → to see each day.",
    figures: "The figures",
    priceToday: "Price today",
    listPrice: "Advertised by the store",
    median: "90-day median",
    minimum: "90-day low",
    realDiscount: "Real discount",
    lastDrop: "Last drop",
    never: "no drops",
    today: "today",
    daysAgo: (n) => (n === 1 ? "1 day ago" : `${n} days ago`),
    confHeading: "How sure it is",
    confBody: (c, t, code) =>
      `Decider's signal is ${c} and the threshold is ${t}. ${code === "short_history" ? "The signal does not decide here: with under 14 days of history the rule alerts with a warning before looking at it." : Number(c) >= Number(t) ? "It is above the threshold: the rule decides without a warning." : "It is below the threshold: the rule alerts with a warning."} It is not a probability of being right: that signal lives on a low scale and the threshold was calibrated on data.`,
    confScale: "Decider signal scale, from 0 to 1",
    confSignal: "signal",
    confThreshold: "threshold",
    noticeAlert: "What you would get",
    noticeSilent: "Why it stayed silent",
    fine: "Decider 2B measures; the alert rule is code; Bedrock only writes the text from the code's figures.",

    watchingFact: (price) => `It costs ${price} today. There is no history yet to judge it.`,
    watchingBody: "Dealjudge needs 14 days of prices to give a verdict. Until then, if it sees a drop, it will alert you with caution.",
    watchingChart: "The 90-day chart appears once there is history.",
    remove: "Stop watching",
    removed: (name) => `You stopped watching ${name}.`,
    added: (name) => `You are now watching ${name}.`,

    addTitle: "Add product",
    addLead: "Type what you want to watch. I show you what I understood and you confirm.",
    addLabel: "Product",
    addPlaceholder: "E.g. wireless headphones",
    addSubmit: "Search",
    addTry: "Or try",
    addLooking: "Looking across stores…",
    addUnderstood: "This is what I understood",
    addQuestion: "Is this the product?",
    addConfirm: "Yes, watch this",
    addReject: "Not this one",
    addNone: (q) => `I could not find "${q}" in the demo. Try one of these:`,
    addNoMore: "I have no more matches. Try other words.",
    addAlready: "You already watch this product.",
    addStore: "Store",
    addPrice: "Price today",
    addSimNote: "Simulated search: in the demo I only know a few products from fictional stores.",
    cancel: "Cancel",
    catalog: {
      headphones: "Wireless headphones",
      ssd: "1TB SSD",
      airfryer: "Air fryer",
      vacuum: "Robot vacuum",
      keyboard: "Mechanical keyboard",
      watch: "Smartwatch",
      laptop: "Mid-range laptop",
      shoe: "Running shoes",
    },
  },
};

// What the simulated search "knows": fictional stores, today's price, and words that find it.
// Words are accent-free, lower case, in both languages.
const CATALOG = [
  { id: "headphones", store: "Mercado Alba", price: 38990, words: ["audifono", "auricular", "headphone", "earphone", "headset", "inalambric", "wireless"] },
  { id: "ssd", store: "Casa Cobre", price: 52990, words: ["ssd", "disco", "solid", "almacenamiento", "storage", "1tb"] },
  { id: "airfryer", store: "Tienda Brisa", price: 64990, words: ["freidora", "fryer", "aire", "air"] },
  { id: "vacuum", store: "Bazar Faro", price: 189990, words: ["aspiradora", "vacuum", "robot"] },
  { id: "keyboard", store: "Casa Cobre", price: 44990, words: ["teclado", "keyboard", "mecanic"] },
  { id: "watch", store: "Mercado Alba", price: 79990, words: ["reloj", "watch", "smartwatch"] },
  { id: "laptop", store: "Tienda Brisa", price: 429990, words: ["notebook", "laptop", "portatil", "computador", "gama"] },
  { id: "shoe", store: "Bazar Faro", price: 59990, words: ["zapatilla", "zapato", "shoe", "sneaker", "running", "trotar"] },
];
