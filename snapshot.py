#!/usr/bin/env python3
"""Registra precios de tiendas chilenas en SQLite: cada pasada es una "foto" del momento.

Dealjudge necesita historial (mediana de N dias, dias desde la ultima baja) para juzgar si
un descuento es real. Este script solo observa y guarda; no decide nada.

Uso:
  python3 snapshot.py --once            una pasada y salir
  python3 snapshot.py                   en bucle, una pasada cada INTERVAL segundos
  python3 snapshot.py --once --amazon   incluye Amazon (prueba; suele bloquear)

Env:
  DB_PATH    archivo SQLite (default dealjudge.db)
  INTERVAL   segundos entre pasadas (default 21600 = 6 h)
  DELAY      segundos de espera entre consultas (default 1)
  PORT       si existe, sirve GET /health y, con TOKEN, GET /db y GET /stats
  TOKEN      secreto para descargar la base: /db?token=...
"""
import hmac, html, json, os, re, sqlite3, sys, tempfile, threading, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
DB_PATH = os.environ.get("DB_PATH", "dealjudge.db")
INTERVAL = int(os.environ.get("INTERVAL", "21600"))
DELAY = float(os.environ.get("DELAY", "1"))
TOKEN = os.environ.get("TOKEN", "")

# product, consultas por fuente, filtros sobre el titulo (include / must / exclude)
PRODUCTS = [
    {"name": "Audifonos inalambricos", "include": r"aud[ií]fonos|auriculares|earbuds",
     "must": r"inal[aá]mbric|bluetooth|wireless|tws",
     "exclude": r"funda|case\b|estuche|repuesto|almohadilla|cable|soporte|ni[ñn]o|kids|gamer",
     "queries": ["audifonos inalambricos bluetooth"]},
    {"name": "SSD 1TB", "include": r"ssd", "must": r"\b1 ?tb\b|1000 ?gb",
     "exclude": r"carcasa|enclosure|adaptador|cable|caddy|hdd|disco duro|consola|xbox|playstation|ps5|notebook|laptop|tablet|celular",
     "queries": ["ssd 1tb"]},
    {"name": "Freidora de aire", "include": r"freidora", "must": r"aire|air ?fryer",
     "exclude": r"repuesto|accesorio|papel|molde|rejilla|funda|silicona",
     "queries": ["freidora de aire"]},
    {"name": "Aspiradora robot", "include": r"aspiradora|robot", "must": r"robot",
     "exclude": r"repuesto|filtro|cepillo|bolsa|bater[ií]a|accesorio",
     "queries": ["aspiradora robot"]},
    {"name": "Teclado mecanico", "include": r"teclado", "must": r"mec[aá]nico|mechanical",
     "exclude": r"keycap|switch(es)?\b|cubierta|piano|musical|repuesto|alfombra|mousepad",
     "queries": ["teclado mecanico"]},
    {"name": "Smartwatch", "include": r"smart ?watch|reloj inteligente",
     "exclude": r"correa|malla|protector|funda|cargador|vidrio|film|ni[ñn]o|kids|bandas?\b",
     "queries": ["smartwatch"]},
    {"name": "Notebook gama media", "include": r"notebook|laptop", "must": r"ryzen 5|core i5|\bi5[- ]",
     "exclude": r"funda|mochila|cargador|bater[ií]a|base|soporte|reacondicionado|refurbished|usado|cooler|repuesto",
     "queries": ["notebook ryzen 5", "notebook core i5"]},
    {"name": "Zapatillas running", "include": r"zapatill", "must": r"running|correr|trail",
     "exclude": r"ni[ñn]o|kids|infantil|plantilla|cordones|bolso|calcet",
     "queries": ["zapatillas running"]},
]


def get(url, cookie=None):
    headers = {"User-Agent": UA, "Accept-Language": "es-CL,es;q=0.9"}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")


def next_data(page):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    return json.loads(m.group(1)) if m else None


# Cada fuente devuelve dicts {title, store, price, currency, url, extra}. "extra" guarda
# campos crudos de la tienda (precio de lista, tarjeta...) para descubrir despues cuales sirven.
def fetch_knasta(q):
    d = next_data(get("https://knasta.cl/results?q=" + urllib.parse.quote(q)))
    out = []
    for p in (d or {}).get("props", {}).get("pageProps", {}).get("initialData", {}).get("products", []):
        cands = [x for x in (p.get("current_price"), p.get("price_internet")) if isinstance(x, (int, float)) and x > 0]
        if cands:
            out.append({"title": p["title"], "store": p["retail"], "price": min(cands), "currency": "CLP",
                        "url": p["url"], "extra": {k: v for k, v in p.items() if k not in ("title", "url", "image")}})
    return out


def fetch_sodimac(q):
    d = next_data(get("https://www.sodimac.cl/sodimac-cl/search?Ntt=" + urllib.parse.quote(q)))
    try:
        res = d["props"]["pageProps"]["searchProps"]["searchData"]["results"]
    except (TypeError, KeyError):
        return []
    out = []
    for p in res:
        prices = [x["priceWithoutFormatting"] for x in p.get("prices", []) if x.get("priceWithoutFormatting")]
        if prices:
            url = p.get("url") or "https://www.sodimac.cl/sodimac-cl/product/%s" % p["productId"]
            out.append({"title": p["displayName"], "store": "sodimac", "price": min(prices), "currency": "CLP",
                        "url": url, "extra": {"prices": p.get("prices")}})
    return out


def fetch_paris(q):
    page = get("https://www.paris.cl/search?q=" + urllib.parse.quote(q)).replace('\\"', '"')
    return [{"title": html.unescape(m.group(1)), "store": "paris", "price": int(m.group(3)), "currency": "CLP",
             "url": m.group(2), "extra": {}}
            for m in re.finditer(r'"@type":"Product","name":"([^"]+)","url":"([^"]+)".{0,600}?"price":(\d+)', page)]


def fetch_amazon(q):
    """Prueba: Amazon cambia el HTML y bloquea con captcha; si falla, queda fuera."""
    page = get("https://www.amazon.com/s?k=" + urllib.parse.quote(q))
    if "captcha" in page.lower() and "s-search-result" not in page:
        raise RuntimeError("Amazon devolvio captcha")
    out = []
    for blk in page.split('data-component-type="s-search-result"')[1:]:
        asin = re.search(r'data-asin="(\w+)"', blk)
        title = re.search(r"<h2[^>]*>.*?<span[^>]*>(.*?)</span>", blk, re.S)
        price = re.search(r'a-offscreen">\s*([^<]+)<', blk)
        if asin and title and price:
            text = html.unescape(price.group(1)).strip()
            cur = "CLP" if "CLP" in text else "USD"
            num = re.sub(r"[^\d]", "", text) if cur == "CLP" else re.sub(r"[^\d.]", "", text)
            if num:
                out.append({"title": html.unescape(re.sub("<[^>]+>", "", title.group(1))), "store": "amazon",
                            "price": float(num), "currency": cur, "url": "https://www.amazon.com/dp/" + asin.group(1),
                            "extra": {"price_text": text}})
    return out


SOURCES = [("knasta", fetch_knasta), ("sodimac", fetch_sodimac), ("paris", fetch_paris)]


def matches(product, title):
    rx = lambda k: re.compile(product[k], re.I) if product.get(k) else None
    inc, must, exc = rx("include"), rx("must"), rx("exclude")
    return not ((inc and not inc.search(title)) or (must and not must.search(title)) or (exc and exc.search(title)))


def collect(product, sources):
    """Consulta cada fuente con cada query; una fuente caida no tumba la pasada."""
    items, errors = {}, []
    for src, fn in sources:
        for q in product["queries"]:
            try:
                for it in fn(q):
                    it["source"] = src
                    items[it["url"]] = it
            except Exception as e:
                errors.append("%s '%s': %s" % (src, q, e))
            time.sleep(DELAY)
    keep = [it for it in items.values() if matches(product, html.unescape(it["title"]))]
    return keep, errors, len(items)


def open_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY, ts TEXT NOT NULL, product TEXT NOT NULL, source TEXT NOT NULL,
        store TEXT NOT NULL, url TEXT NOT NULL, title TEXT NOT NULL, price REAL NOT NULL,
        currency TEXT NOT NULL, extra TEXT)""")
    db.execute("CREATE INDEX IF NOT EXISTS ix_url_ts ON snapshots (url, ts)")
    db.execute("CREATE INDEX IF NOT EXISTS ix_product_ts ON snapshots (product, ts)")
    return db


def run_pass(db, sources):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    total = 0
    for product in PRODUCTS:
        keep, errors, raw = collect(product, sources)
        db.executemany(
            "INSERT INTO snapshots (ts, product, source, store, url, title, price, currency, extra) VALUES (?,?,?,?,?,?,?,?,?)",
            [(ts, product["name"], it["source"], it["store"], it["url"], html.unescape(it["title"]), it["price"],
              it["currency"], json.dumps(it["extra"], ensure_ascii=False)) for it in keep])
        db.commit()
        total += len(keep)
        print("%-24s %3d guardados (de %d resultados)%s" % (product["name"], len(keep), raw,
              "  | %d errores" % len(errors) if errors else ""), flush=True)
        for e in errors:
            print("  ! " + e, file=sys.stderr)
    print("pasada ok %s: %d filas en %s" % (ts, total, DB_PATH), flush=True)


class Handler(BaseHTTPRequestHandler):
    """/health abierto; /db y /stats exigen ?token= (y TOKEN configurado)."""

    def _send(self, code, body, ctype="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/health":
            return self._send(200, b"ok")
        given = urllib.parse.parse_qs(url.query).get("token", [""])[0]
        if url.path not in ("/db", "/stats") or not TOKEN or not hmac.compare_digest(given, TOKEN):
            return self._send(404, b"not found")
        src = sqlite3.connect(DB_PATH)
        try:
            if url.path == "/stats":
                rows = src.execute("SELECT product, COUNT(*), COUNT(DISTINCT ts), MIN(ts), MAX(ts) FROM snapshots GROUP BY product").fetchall()
                return self._send(200, json.dumps(rows, ensure_ascii=False).encode(), "application/json")
            with tempfile.NamedTemporaryFile(suffix=".db") as tmp:  # copia consistente aunque se este escribiendo
                dst = sqlite3.connect(tmp.name)
                src.backup(dst)
                dst.close()
                self._send(200, open(tmp.name, "rb").read(), "application/octet-stream")
        finally:
            src.close()

    def log_message(self, *a):
        pass


def serve(port):
    threading.Thread(target=ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever, daemon=True).start()
    print("http en :%d (descarga %s)" % (port, "activa" if TOKEN else "desactivada: falta TOKEN"), flush=True)


def main():
    sources = SOURCES + ([("amazon", fetch_amazon)] if "--amazon" in sys.argv else [])
    db = open_db()
    if os.environ.get("PORT"):
        serve(int(os.environ["PORT"]))
    while True:
        t0 = time.time()
        try:
            run_pass(db, sources)
        except Exception as e:
            print("pasada fallida: %s" % e, file=sys.stderr)
        if "--once" in sys.argv:
            return
        time.sleep(max(60, INTERVAL - (time.time() - t0)))


if __name__ == "__main__":
    main()
