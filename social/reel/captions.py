# Turns Whisper word timings into short caption lines, with fixes for misheard words.
import json, sys
S = sys.argv[1]
w = [[c['text'].strip(), c['timestamp'][0], c['timestamp'][1]] for c in json.load(open(S + '/voice/words.json'))['chunks']]
out = []; i = 0
while i < len(w):
    t, a, b = w[i]
    nxt = w[i + 1][0] if i + 1 < len(w) else ''
    if t == 'Arc' and nxt.startswith('Daily'):
        out.append(['ArchDaily' + nxt[5:], a, w[i + 1][2]]); i += 2; continue
    if t and all(ch in ',.' for ch in t):          # stray punctuation: attach to previous word
        if out and out[-1][0][-1] not in ',.': out[-1][0] += t[0]
        i += 1; continue
    if t == 'everyone': t = 'every one'
    if t == 'the' and nxt == 'light': i += 1; continue
    t = t.replace(' ,', ',').replace(',,', ',')
    if t == 'movement': t = 'movement,'
    if t == 'photos' and nxt == 'who': t = 'photos,'
    out.append([t, a, b]); i += 1
WEAK = set('a an the of to and or is has been be for you your we it in on at that with kind what if there are our so just can do how by still go get end either half'.split())
groups, cur = [], []
for k, x in enumerate(out):
    cur.append(x)
    nxt = out[k + 1] if k + 1 < len(out) else None
    chars = sum(len(y[0]) + 1 for y in cur)
    if not nxt or x[0][-1] in '.,?' or (nxt[1] - x[2]) > 0.35:
        groups.append(cur); cur = []; continue
    if len(cur) >= 5 or chars >= 24:
        carry = []
        while len(cur) > 2 and cur[-1][0].lower() in WEAK: carry.insert(0, cur.pop())
        groups.append(cur); cur = carry
if cur: groups.append(cur)
# Fold a tiny leftover line ("at or", "it and") into the next one when it follows closely.
merged = []
for g in groups:
    if merged and len(merged[-1]) <= 2 and sum(len(x[0]) for x in merged[-1]) <= 6 and merged[-1][-1][0][-1] not in '.,?' \
       and g[0][1] - merged[-1][-1][2] < 1.0 and len(merged[-1]) + len(g) <= 6:
        merged[-1] = merged[-1] + g
    else:
        merged.append(g)
json.dump(merged, open(S + '/reel/caps/groups.json', 'w'))
for g in merged: print(f"{g[0][1]:6.2f}-{g[-1][2]:6.2f}", ' '.join(x[0] for x in g))
