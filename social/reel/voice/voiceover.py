# Voices each phrase with Kokoro and places it where the original phrase started,
# speeding a phrase up (up to 1.3x) only when it would run into the next one.
# usage: voiceover.py <work dir> <voice> <out.wav>
import json, subprocess, sys, os
S, voice, OUT = sys.argv[1:4]
K = S + '/kokoro'; TMP = f'{K}/vo_{voice}'; os.makedirs(TMP, exist_ok=True)
units = json.load(open(K + '/units.json')); lines = json.load(open(K + '/script_lines.json'))
assert len(units) == len(lines), (len(units), len(lines))
RUN = ['node', 'tts.mjs', '../model_quantized.onnx', '../pkgs/x_expo/package/src/tokenizer.json']
def gen(items):
    p = f'{TMP}/batch.json'; json.dump(items, open(p, 'w'))
    subprocess.run(RUN + [p, TMP], cwd=K + '/run', check=True, capture_output=True)
def trimmed(i):
    # cut the model's leading/trailing silence, return length
    src, dst = f'{TMP}/u{i:02d}.wav', f'{TMP}/t{i:02d}.wav'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-af',
      'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,aresample=48000',
      dst], check=True)
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', dst]))
items = [{'id': f'u{i:02d}', 'text': t, 'voice': voice, 'speed': 1} for i, t in enumerate(lines)]
gen(items)
speeds = [1.0] * len(units); lens = [trimmed(i) for i in range(len(units))]
redo = []
for i, u in enumerate(units):
    room = (u['next'] - u['start'] - 0.06) if i + 1 < len(units) else 99
    if lens[i] > room:
        speeds[i] = min(1.3, lens[i] / room * 1.03); redo.append(i)
if redo:
    gen([dict(items[i], speed=round(speeds[i], 3)) for i in redo])
    for i in redo: lens[i] = trimmed(i)
inputs, chains = [], []
for i, u in enumerate(units):
    inputs += ['-i', f'{TMP}/t{i:02d}.wav']
    d = int(round(u['start'] * 1000))
    chains.append(f'[{i}:a]adelay={d}|{d}[a{i}]')
    room = (u['next'] - u['start']) if i + 1 < len(units) else 99
    flag = '  OVERLAP' if lens[i] > room else ''
    print(f"u{i:02d} start {u['start']:6.2f} len {lens[i]:5.2f} room {min(room, 99):5.2f} speed {speeds[i]:.2f}{flag}")
fc = ';'.join(chains) + ';' + ''.join(f'[a{i}]' for i in range(len(units))) + f'amix=inputs={len(units)}:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[out]'
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *inputs, '-filter_complex', fc, '-map', '[out]', '-ac', '1', '-c:a', 'pcm_s16le', OUT], check=True)
print('total', subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', OUT]).decode().strip())
