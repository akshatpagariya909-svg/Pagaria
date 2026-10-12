// Renders one transparent 1080x1920 PNG per caption state (line + spoken word in red),
// then lists them with durations for ffmpeg.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const S = process.argv[2], END = +process.argv[3];
const groups = JSON.parse(fs.readFileSync(path.join(S, 'reel/caps/groups.json')));
const OUT = path.join(S, 'reel/caps/png'); fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true });
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.setContent(`<html><head><link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=block" rel="stylesheet">
    <style>html,body{margin:0;background:transparent;width:1080px;height:1920px}
    #c{position:absolute;left:50%;top:1390px;transform:translate(-50%,-50%);width:max-content;max-width:940px;box-sizing:border-box;padding:20px 34px 24px;border-radius:28px;background:#fff;
      box-shadow:0 10px 40px rgba(0,0,0,.18),0 0 0 2px rgba(17,17,16,.06);font-family:Archivo,sans-serif;font-weight:800;font-size:66px;line-height:1.08;
      letter-spacing:-.015em;color:#111110;text-align:center;text-wrap:balance}
    #c b{font-weight:800;color:#DA3A26}</style></head><body><div id="c"></div></body></html>`, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const list = []; let n = 0, t = 0;
  const blank = path.join(OUT, 'blank.png');
  await p.evaluate(() => document.getElementById('c').style.display = 'none');
  await p.screenshot({ path: blank, omitBackground: true });
  await p.evaluate(() => document.getElementById('c').style.display = '');
  const push = (file, until) => { if (until - t > 0.0005) { list.push(`file '${file}'\nduration ${(until - t).toFixed(4)}`); t = until; } };
  for (let g = 0; g < groups.length; g++) {
    const words = groups[g], next = groups[g + 1];
    push(blank, words[0][1]);
    // Hold the line through a short pause; clear it for a longer one.
    const lineEnd = next ? (next[0][1] - words[words.length - 1][2] < 0.6 ? next[0][1] : words[words.length - 1][2] + 0.25) : END;
    for (let k = 0; k < words.length; k++) {
      const html = words.map((w, j) => j === k ? `<b>${esc(w[0])}</b>` : esc(w[0])).join(' ');
      await p.evaluate(h => document.getElementById('c').innerHTML = h, html);
      const file = path.join(OUT, String(n++).padStart(4, '0') + '.png');
      await p.screenshot({ path: file, omitBackground: true });
      push(file, k + 1 < words.length ? words[k + 1][1] : lineEnd);
    }
  }
  push(blank, END);
  list.push(`file '${blank}'`);
  fs.writeFileSync(path.join(S, 'reel/caps/list.txt'), list.join('\n') + '\n');
  console.log(n, 'caption frames');
  await b.close();
})();
