# Tienda pública independiente para monacocompras.com: solo la tienda (sin caja, sin datos privados).
# Uso: python3 build_store.py <artifact.html> <salida/index.html>
# Las fotos (data: URI en el catálogo) se guardan como archivos en <salida>/fotos/ y el catálogo apunta a ellas.
import re, sys, json, html, base64, hashlib, os
src = open(sys.argv[1], encoding='utf-8').read()
def blk(i, t='script'):
    m = re.search(rf'<{t} id="{i}"[^>]*>(.*?)</{t}>', src, re.S)
    if not m: sys.exit('falta ' + i)
    return m.group(1)
cat = json.loads(blk('catalog-data'))
cat['enlace'] = 'https://monacocompras.com/'
fdir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])), 'fotos'); os.makedirs(fdir, exist_ok=True)
EXT = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp', 'image/gif': 'gif'}
usadas = set()
for tienda in cat.get('tiendas') or []:
    for p in tienda.get('productos') or []:
        p.pop('fid', None)
        m = re.match(r'data:(image/[\w+.-]+);base64,(.*)$', (p.get('foto') or '').strip(), re.S)
        if not m: continue
        raw = base64.b64decode(m.group(2))
        nombre = hashlib.sha256(raw).hexdigest()[:16] + '.' + EXT.get(m.group(1), 'jpg')
        ruta = os.path.join(fdir, nombre)
        if not os.path.exists(ruta): open(ruta, 'wb').write(raw)
        usadas.add(nombre); p['foto'] = 'fotos/' + nombre
for f in os.listdir(fdir):
    if f not in usadas: os.remove(os.path.join(fdir, f))
t = (cat.get('tiendas') or [{}])[0]
name = (t.get('nombre') or 'Tienda').strip(); desc = (t.get('slogan') or '').strip()
icon = ((t.get('logo') or {}).get('icono') or '')
sf_css, sf_js = blk('sf-css', 'style'), blk('sf-js')
app_css = blk('app-css', 'style'); tokens = app_css[:app_css.index('\n* { box-sizing')] + '\nbody { background: var(--bg); color: var(--ink); font-family: var(--body); }\n'
catj = json.dumps(cat, ensure_ascii=False).replace('<', '\\u003c')
e = html.escape
head = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(name)}</title><meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(name)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="https://monacocompras.com/">
{f'<meta property="og:image" content="https://monacocompras.com/logo.png">' }
<link rel="icon" href="icon.png"><link rel="apple-touch-icon" href="icon.png"><meta name="theme-color" content="{e(t.get('color') or '#5b2a6e')}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Figtree:wght@400;500;600;700&display=swap">
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0;font:14px/1.4 system-ui,-apple-system,sans-serif}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
<style>{tokens}</style><style>{sf_css}</style></head><body><div id="store"></div>
<script id="catalog-data" type="application/json">{catj}</script>
<script>{sf_js}</script>
<script>
(function () {{
  var root = document.getElementById("store"), data = JSON.parse(document.getElementById("catalog-data").textContent), handle = null;
  function show() {{
    var h = window.Storefront.parseHash(location.hash) || {{}};
    try {{ handle && handle.unmount && handle.unmount(); }} catch (e) {{}}
    root.innerHTML = "";
    handle = window.Storefront.mount(root, data, {{ storeId: h.storeId || null, productCode: h.productCode || null, preview: false }});
  }}
  show();
  window.addEventListener("hashchange", show);
}})();
</script></body></html>'''
open(sys.argv[2], 'w', encoding='utf-8').write(head)
print('store', len(head), 'bytes,', len(t.get('productos', [])), 'productos,', len(usadas), 'fotos')
