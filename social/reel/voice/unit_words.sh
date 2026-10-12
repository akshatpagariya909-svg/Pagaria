#!/bin/sh
# Transcribe each voiced phrase on its own (more accurate than the whole track),
# then shift its word times to where the phrase sits in the reel.
# usage: unit_words.sh <work dir> <voice> <out words.json>
S="$1"; V="$2"; OUT="$3"; T="$S/kokoro/vo_$V"
for f in "$T"/t[0-9][0-9].wav; do
  b=$(basename "$f" .wav)
  ffmpeg -loglevel error -y -i "$f" -ar 16000 -ac 1 -c:a pcm_s16le "$T/${b}_16.wav"
  (cd "$S/asr/run" && node transcribe.mjs "$T/${b}_16.wav" ../pkg/package/models "$T/${b}.json" >/dev/null 2>&1)
done
python3 - "$S" "$T" "$OUT" <<'PY'
import json, sys
S, T, OUT = sys.argv[1:4]
units = json.load(open(S + '/kokoro/units.json')); chunks = []
for i, u in enumerate(units):
    for c in json.load(open(f'{T}/t{i:02d}.json'))['chunks']:
        a, b = c['timestamp']
        chunks.append({'text': c['text'], 'timestamp': [round(u['start'] + a, 3), round(u['start'] + (b if b is not None else a + 0.3), 3)]})
json.dump({'chunks': chunks}, open(OUT, 'w'))
print(len(chunks), 'words;', ' '.join(c['text'].strip() for c in chunks))
PY
