"""Build the playable map artboards for the design canvas from the prototype in design/map/.

The engine is design/map/map.js, adapted to the canvas's artboard format (a DCLogic component): the
chrome (review bar, chips, list, opened building) is markup driven by state; the map tiles and labels
are drawn by the engine into two layers it owns. Two boards come out: desktop (1440 x 900) and
phone (390 x 844).

Usage: python3 gen_play.py <out_project_dir> <assets.json>
  assets.json maps file names (data.js, sprite.webp, m0.webp ...) to their uploaded /_blob/ urls.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
A = json.load(open(sys.argv[2]))

css = (HERE.parent / 'map.css').read_text(encoding='utf-8')
engine = (HERE / 'engine.js').read_text(encoding='utf-8')

# ---- CSS: sprite and card sheets from uploads, the phone media query as a .phone class, page rules scoped to the board
css = css.replace('url(sprite.webp)', f"url({A['sprite.webp']})")
sheets = ''.join(f".card .ph.m{k}{{background-image:url({A[f'm{k}.webp']})}}\n" for k in range(11))
m = re.search(r'@media \(max-width: 820px\) \{(.*?)\n\}', css, re.S)
phone_rules = re.sub(r'\n  ([^\n{]+)\{', lambda mm: '\n.phone ' + ', .phone '.join(s.strip() for s in mm.group(1).split(',')) + ' {', m.group(1))
phone_rules = phone_rules.replace('.phone :root', '.phone')
css = css[:m.start()] + phone_rules + css[m.end():]
css = css.replace('html, body { margin: 0; height: 100%; }', 'html, body { margin: 0; }')
css = css.replace("body { background: var(--ground); color: var(--ink); font-family: var(--sans); font-size: 14px; -webkit-font-smoothing: antialiased; overflow: hidden; }",
                  ".root { background: var(--ground); color: var(--ink); font-family: var(--sans); font-size: 14px; -webkit-font-smoothing: antialiased; overflow: hidden; position: relative; }")
css = css.replace('.site { position: relative; height: calc(100% - 46px); overflow: hidden; }', '.site { position: absolute; left: 0; right: 0; top: 46px; bottom: 0; overflow: hidden; }')
css = css.replace('.mapwrap[hidden] { display: none; }', '.mapwrap.off { display: none; }')
css = css.replace('.sheet[hidden] { display: none; }', '')
css = css.replace('.card .ph { width: 100%; aspect-ratio: 4 / 3; background: var(--slot) no-repeat; background-size: 1600% 1000%; }',
                  '.card .ph { width: 100%; aspect-ratio: 4 / 3; background: var(--slot) no-repeat; background-size: 1600% 1000%; flex: none; }\n' + sheets)
css = css.replace('.wall .t { position: relative; aspect-ratio: 4 / 3; background: var(--slot) center / 1600% 1000% no-repeat; overflow: hidden; }',
                  f".wall .t {{ position: relative; aspect-ratio: 4 / 3; background: var(--slot) url({A['m0.webp']}) center / 1600% 1000% no-repeat; overflow: hidden; }}")
css = css.replace('.review { height: 46px;', '.review { position: absolute; left: 0; right: 0; top: 0; height: 46px; box-sizing: border-box;')
css = css.replace('.card .study span {', '.card .study .lab {')
css += "\n.phone .review { gap: 10px; padding: 0 10px; font-size: 12px; }\n.phone .review .note { display: none; }\n.phone .review .lead { display: none; }\n"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
<script src="{data}"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&amp;family=IBM+Plex+Mono:wght@400;500&amp;family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&amp;display=swap">
<style>
body{{margin:0}}
{css}
</style>
</helmet>
"""

MARKUP = """
<div class="root {phone}" style="width: {w}px; height: {h}px">
<div class="review" role="toolbar" aria-label="Review controls">
  <span class="lead">Review controls</span>
  <div class="seg"><span>Opening</span><button type="button" onClick="{{{{ pickAtlas }}}}" aria-pressed="{{{{ isAtlas }}}}">Atlas</button><button type="button" onClick="{{{{ pickGlobe }}}}" aria-pressed="{{{{ isGlobe }}}}">Globe</button></div>
  <div class="seg"><span>Marks</span><button type="button" onClick="{{{{ pickPhotos }}}}" aria-pressed="{{{{ isPhotos }}}}">Photos</button><button type="button" onClick="{{{{ pickDots }}}}" aria-pressed="{{{{ isDots }}}}">Dots</button></div>
  <div class="seg"><span>List</span><button type="button" onClick="{{{{ listOn }}}}" aria-pressed="{{{{ isList }}}}">On</button><button type="button" onClick="{{{{ listOff }}}}" aria-pressed="{{{{ noList }}}}">Off</button></div>
  <span class="note">Drag to look around · scroll or pinch to zoom · click a photo</span>
</div>
<div class="site">
  <header class="bar">
    <a class="mark" href="#">Discover<br><span class="accent">Architecture.</span></a>
    <div class="bar-mid"><div class="search" aria-hidden="true"><svg viewBox="0 0 24 24" width="16" height="16"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>Search a building, architect, city or idea…</div></div>
    <span class="count">{{{{ total }}}}</span>
  </header>
  <div class="wall" aria-hidden="true"><sc-for list="{{{{ wall }}}}" as="t" hint-placeholder-count="8"><div class="t" style="background-position: {{{{ t.bp }}}}"><span class="cap"><b>{{{{ t.name }}}}</b><span>{{{{ t.by }}}}</span></span></div></sc-for></div>
  <nav class="dock" aria-label="Wall controls">
    <button type="button" onClick="{{{{ shuffle }}}}">Shuffle</button>
    <button type="button" onClick="{{{{ openMap }}}}"><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/></svg>Map</button>
    <button type="button" class="go" onClick="{{{{ surprise }}}}">Surprise me</button>
  </nav>
  <div class="mapwrap {{{{ wrapClass }}}}">
    <section class="panel {{{{ panelClass }}}}" role="dialog" aria-modal="true" aria-label="Map" tabindex="-1" ref="{{{{ panelRef }}}}">
      <div class="head">
        <h1>Map <small>{{{{ count }}}}</small></h1>
        <nav class="chips" aria-label="Go to"><sc-for list="{{{{ chips }}}}" as="c" hint-placeholder-count="6"><button type="button" class="chip" onClick="{{{{ c.go }}}}">{{{{ c.label }}}} <small>{{{{ c.n }}}}</small></button></sc-for></nav>
        <label class="find"><span class="sr">Show only buildings matching</span><svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg><input type="search" placeholder="Show only… (Kahn, brick, library)" autocomplete="off" onInput="{{{{ onFind }}}}"></label>
        <button type="button" class="close" onClick="{{{{ closeMap }}}}" aria-label="Close the map"><svg viewBox="0 0 24 24" width="18" height="18"><path d="M5 5l14 14M19 5 5 19"/></svg></button>
      </div>
      <div class="map" ref="{{{{ mapRef }}}}" tabindex="0" role="application" aria-label="World map of buildings. Drag to pan, plus and minus to zoom, 0 for the whole world.">
        <canvas ref="{{{{ cvRef }}}}"></canvas>
        <div class="layer" ref="{{{{ labelsRef }}}}"></div>
        <div class="layer" ref="{{{{ tilesRef }}}}"></div>
        <div class="where">{{{{ where }}}}</div>
        <div class="hint {{{{ hintClass }}}}">Scroll to zoom in · click a stack to open it</div>
        <div class="ctl">
          <button type="button" onClick="{{{{ zin }}}}" aria-label="Zoom in"><svg viewBox="0 0 24 24" width="18" height="18"><path d="M12 5v14M5 12h14"/></svg></button>
          <button type="button" onClick="{{{{ zout }}}}" aria-label="Zoom out"><svg viewBox="0 0 24 24" width="18" height="18"><path d="M5 12h14"/></svg></button>
          <button type="button" onClick="{{{{ zworld }}}}" aria-label="Whole world"><svg viewBox="0 0 24 24" width="18" height="18"><circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c3 3 3 13 0 16M12 4c-3 3-3 13 0 16"/></svg></button>
        </div>
      </div>
      <aside class="list">
        <h2>In view <small>{{{{ inview }}}}</small></h2>
        <div class="rows"><sc-for list="{{{{ rows }}}}" as="r" hint-placeholder-count="8"><button type="button" class="row" onClick="{{{{ r.open }}}}" onMouseEnter="{{{{ r.hover }}}}" onMouseLeave="{{{{ unhover }}}}"><i style="background-position: {{{{ r.bp }}}}"></i><span><b>{{{{ r.name }}}}</b><span>{{{{ r.meta }}}}</span></span></button></sc-for></div>
        <p>{{{{ listNote }}}}</p>
      </aside>
    </section>
  </div>
  <sc-if value="{{{{ cardOpen }}}}" hint-placeholder-val="{{{{ false }}}}">
  <div class="sheet">
    <button type="button" class="veil" onClick="{{{{ closeCard }}}}" aria-label="Close"></button>
    <article class="card" role="dialog" aria-modal="true" tabindex="-1">
      <div class="ph {{{{ card.sheet }}}}" style="background-position: {{{{ card.bp }}}}" role="img" aria-label="{{{{ card.alt }}}}"></div>
      <div class="in">
        <div class="kicker"><span>{{{{ card.kicker }}}}</span><button type="button" class="x" onClick="{{{{ closeCard }}}}" aria-label="Close"><svg viewBox="0 0 24 24" width="16" height="16"><path d="M5 5l14 14M19 5 5 19"/></svg></button></div>
        <h1>{{{{ card.name }}}}</h1>
        <div class="by"><i>by</i> <b>{{{{ card.by }}}}</b></div>
        <div class="meta">{{{{ card.meta }}}}</div>
        <p class="study"><span class="lab">Key features</span>{{{{ card.study }}}}</p>
        <p class="credit">{{{{ card.credit }}}} · <a href="{{{{ card.source }}}}" target="_blank" rel="noopener">source</a></p>
        <div class="acts">
          <a class="go" href="{{{{ card.url }}}}" target="_blank" rel="noopener">Open on the site ↗</a>
          <button type="button" onClick="{{{{ card.near }}}}" class="{{{{ card.nearClass }}}}">{{{{ card.nearLabel }}}}</button>
        </div>
      </div>
    </article>
  </div>
  </sc-if>
</div>
</div>
</x-dc>
"""

SCRIPT = """<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
  constructor(props) {{
    super(props);
    this.state = {{ mode: 'atlas', marks: 'photos', list: true, mapOpen: true, hint: true, count: '', total: '', chips: [], rows: [], inview: '', where: '', wall: [], card: null }};
    this.els = {{}};
    this.refs = {{}};
    for (const k of ['map', 'cv', 'labels', 'tiles', 'panel']) this.refs[k] = el => {{ if (el && this.els[k] !== el) {{ this.els[k] = el; this.start(); }} }};
  }}
  start() {{
    if (this.api || !this.els.map || !this.els.cv || !this.els.labels || !this.els.tiles || !this.els.panel || !window.MAPDATA) return;
    const ui = {{
      set: patch => this.setState(patch),
      card: card => this.setState({{ card }}),
    }};
    this.api = this.engine(this.els, ui, {this_is_phone});
  }}
  engine(els, ui, isPhone) {{
{engine}
  }}
  renderVals() {{
    const s = this.state, api = this.api, card = s.card || {{ sheet: '', bp: '', alt: '', kicker: '', name: '', by: '', meta: '', study: '', credit: '', source: '#', url: '#', near: () => {{}}, nearLabel: '', nearClass: 'none' }};
    const call = (f) => () => {{ if (api) api[f](); }};
    return {{
      isAtlas: s.mode === 'atlas', isGlobe: s.mode === 'globe', isPhotos: s.marks === 'photos', isDots: s.marks === 'dots', isList: s.list, noList: !s.list,
      pickAtlas: () => {{ this.setState({{ mode: 'atlas' }}); if (api) api.setMode('atlas'); }},
      pickGlobe: () => {{ this.setState({{ mode: 'globe' }}); if (api) api.setMode('globe'); }},
      pickPhotos: () => this.setState({{ marks: 'photos' }}), pickDots: () => this.setState({{ marks: 'dots' }}),
      listOn: () => {{ this.setState({{ list: true }}); if (api) setTimeout(api.relayout, 0); }}, listOff: () => {{ this.setState({{ list: false }}); if (api) setTimeout(api.relayout, 0); }},
      panelClass: (s.marks === 'dots' ? 'dots ' : '') + (s.list ? '' : 'nolist'),
      wrapClass: s.mapOpen ? '' : 'off', hintClass: s.hint ? '' : 'gone',
      openMap: () => {{ this.setState({{ mapOpen: true }}); if (api) setTimeout(api.relayout, 0); }}, closeMap: () => this.setState({{ mapOpen: false }}),
      shuffle: call('shuffle'), surprise: call('surprise'), zin: call('zoomIn'), zout: call('zoomOut'), zworld: call('world'),
      onFind: e => {{ if (api) api.find(e.target.value); }},
      unhover: () => {{ if (api) api.hot(null); }},
      closeCard: () => this.setState({{ card: null }}), cardOpen: !!s.card, card,
      total: s.total, count: s.count, chips: s.chips, rows: s.rows, inview: s.inview, where: s.where, wall: s.wall,
      listNote: 'Everything on the map right now, best known first. Click one to open it.',
      panelRef: this.refs.panel, mapRef: this.refs.map, cvRef: this.refs.cv, labelsRef: this.refs.labels, tilesRef: this.refs.tiles,
    }};
  }}
}}
</script>
</body>
</html>
"""

for name, w, h, phone in [('V10Play', 1440, 900, False), ('V10PlayPhone', 390, 844, True)]:
    html = HEAD.format(title='Play the map' + (' on a phone' if phone else ''), data=A['data.js'], css=css) + \
        MARKUP.format(phone='phone' if phone else '', w=w, h=h) + \
        SCRIPT.format(w=w, h=h, engine=engine, this_is_phone='true' if phone else 'false')
    (OUT / f'{name}.dc.html').write_text(html, encoding='utf-8')
    print(name, len(html) // 1024, 'KB')
