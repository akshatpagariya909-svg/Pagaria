import sys, importlib, os
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
OUT = os.path.join(os.path.dirname(__file__), '..', 'img')
mods = [importlib.import_module(m) for m in sys.argv[1].split(',')]
names = sys.argv[2].split(',')
thumbs = []
for n in names:
    fn = None
    for m in mods:
        fn = getattr(m, n, None) or fn
    a = fn()
    key = n.replace('_fix', '')
    p = os.path.join(OUT, key + '.jpg')
    a.save(p)
    im = Image.open(p); im.thumbnail((300, 300)); thumbs.append(im)
cols = 6
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * 304, rows * 304), 'white')
for i, t in enumerate(thumbs):
    sheet.paste(t, ((i % cols) * 304 + 2, (i // cols) * 304 + 2))
sheet.save(os.path.join(OUT, '..', sys.argv[3]))
