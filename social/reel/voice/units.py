# Splits the original recording's words into phrases at natural pauses, with the text
# fixed for speaking (ArchDaily, punctuation), and the time window each phrase must fill.
import json, sys
S, voice = sys.argv[1], sys.argv[2]
w = [[c['text'].strip(), c['timestamp'][0], c['timestamp'][1]] for c in json.load(open(S + '/voice/words.json'))['chunks']]
fix = {'Arc': 'Arch', 'Daily': 'Daily', 'everyone': 'every one'}
units, cur = [], []
for k, (t, a, b) in enumerate(w):
    if t and all(ch in ',.' for ch in t):
        if cur: cur[-1][0] += t[0]
        continue
    t = t.replace(',,', ',').replace(' ,', ',')
    if t == 'Arc' and k + 1 < len(w) and w[k + 1][0].startswith('Daily'): t = 'ArchDaily'
    elif t.startswith('Daily') and k and w[k - 1][0] == 'Arc': continue
    if t == 'everyone': t = 'every one'
    if t == 'photos' and k + 1 < len(w) and w[k + 1][0] == 'who': t = 'photos,'
    if t == 'the' and k + 1 < len(w) and w[k + 1][0] == 'light': t = 'like'
    cur.append([t, a, b])
    nxt = w[k + 1] if k + 1 < len(w) else None
    if not nxt or (nxt[1] - b) > 0.32 or (t[-1] in '.?' and len(cur) > 3):
        units.append(cur); cur = []
if cur: units.append(cur)
out = []
for i, u in enumerate(units):
    nxt = units[i + 1][0][1] if i + 1 < len(units) else u[-1][2] + 0.6
    text = ' '.join(x[0] for x in u)
    text = text[0].upper() + text[1:]
    out.append({'id': f'u{i:02d}', 'text': text, 'voice': voice, 'start': u[0][1], 'end': u[-1][2], 'next': nxt})
json.dump(out, open(S + '/kokoro/units.json', 'w'), indent=1)
for o in out: print(f"{o['start']:6.2f}-{o['end']:6.2f} (room to {o['next']:6.2f})  {o['text']}")
