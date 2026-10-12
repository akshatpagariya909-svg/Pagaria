# Cuts the clips and scenes to the voice: each segment covers a stretch of the audio,
# and clips with taps are gently time-stretched so each tap lands on the word that names it.
import json, subprocess, sys, os
S = sys.argv[1]; R = S + '/reel'; C = R + '/clips'; SEG = R + '/segs'; os.makedirs(SEG, exist_ok=True)
FPS = 30
words = [[c['text'].strip(), c['timestamp'][0], c['timestamp'][1]] for c in json.load(open(S + '/voice/words.json'))['chunks']]
def at(word, after=0.0):
    for t, a, b in words:
        if a >= after and t.lower().strip(',.') .startswith(word.lower()): return a
    raise SystemExit('word not found: ' + word)
def marks(name): return dict(json.load(open(f'{C}/{name}.json'))['marks'])
END = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', S + '/voice/enhanced.wav']))

t_or = at('you', 14.0)
t_shuffle = at('shuffle'); t_surprise = at('surprise'); t_photos = at('photos'); t_couple = at('couple'); t_links = at('links')
t_dumb = at('dumbed'); t_light = at('light'); t_court = at('courtyard'); t_type = at('type', 62); t_mov = at('movement'); t_reg = at('region'); t_etc = at('etc')
t_all = at('All', 66); t_still = at("It's", 69); t_link = at('Link', 72)
mo, mf, ms = marks('open'), marks('filters'), marks('shuffle')
open_start = t_surprise - 1.0; shuffle_start = t_shuffle - 1.0; filt_start = at('And', 57)

# (clip, audio_start, audio_end, anchors: [(clip_time, audio_time)])
PLAN = [
  ('scene_intro', 0.0, 8.3, [(0, 0.0)]),
  ('scene_mood', 8.3, t_or, [(0, 8.3)]),
  ('scene_search', t_or, 20.8, [(0, t_or)]),
  ('scene_flip', 20.8, at('So', 28)), 
  ('scene_logo', at('So', 28), at("It's", 31.5), [(0, at('So', 28))]),
  ('wall', at("It's", 31.5), shuffle_start, [(0.6, at("It's", 31.5))]),
  ('shuffle', shuffle_start, open_start, [(ms['shuffle1'] - 1.0, shuffle_start)]),
  ('open', open_start, filt_start, [(mo['surprise'] - 1.0, open_start), (mo['surprise'], t_surprise), (mo['photo2'], t_photos),
                                   (mo['study'], t_couple), (mo['links'], t_links)]),
  ('filters', filt_start, t_all - 0.15, [(mf['filter'] - 0.6, filt_start), (mf['filter'], filt_start + 0.6), (mf['light'], t_light), (mf['courtyard'], t_court),
                                       (mf['types'], t_type), (mf['movs'], t_mov), (mf['where'], t_reg), (mf['when'], t_etc), (mf['show'], t_etc + 0.9)]),
  ('scene_credit', t_all - 0.15, t_still - 0.1, [(0, t_all - 0.15)]),
  ('ending', t_still - 0.1, t_link - 0.1, [(0.6, t_still - 0.1)]),
  ('scene_end', t_link - 0.1, END, [(0, t_link - 0.1)]),
]
PLAN[3] = ('scene_flip', 20.8, PLAN[3][2], [(0, 20.8)])

def dur(f): return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))
files = []
for i, (clip, a0, a1, anchors) in enumerate(PLAN):
    src = f'{C}/{clip}.mp4'; cd = dur(src)
    frames = round(a1 * FPS) - round(a0 * FPS)
    # Pieces between anchors are stretched; after the last anchor the clip plays at normal speed.
    pts = sorted(anchors) + [(anchors[-1][0] + (a1 - anchors[-1][1]), a1)]
    parts, chain = [], []
    for k in range(len(pts) - 1):
        (c0, x0), (c1, x1) = pts[k], pts[k + 1]
        c0 = max(0, c0); c1 = min(cd, c1)
        if c1 - c0 < 0.02 or x1 - x0 < 0.02: continue
        f = (x1 - x0) / (c1 - c0)
        chain.append(f'[0:v]trim=start={c0:.3f}:end={c1:.3f},setpts=(PTS-STARTPTS)*{f:.5f}[p{k}]'); parts.append(f'[p{k}]')
        print(f'{clip:13s} clip {c0:6.2f}-{c1:6.2f} -> {x0:6.2f}-{x1:6.2f}  x{f:.2f}')
    fc = ';'.join(chain) + f';{"".join(parts)}concat=n={len(parts)}:v=1:a=0,fps={FPS},tpad=stop_mode=clone:stop_duration=10,scale=1080:1920,setsar=1,format=yuv420p[v]'
    out = f'{SEG}/{i:02d}_{clip}.mp4'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-filter_complex', fc, '-map', '[v]', '-frames:v', str(frames),
                    '-c:v', 'libx264', '-crf', '15', '-preset', 'medium', '-r', str(FPS), out], check=True)
    files.append(out)
open(f'{SEG}/list.txt', 'w').write(''.join(f"file '{f}'\n" for f in files))
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{SEG}/list.txt', '-c', 'copy', f'{R}/base.mp4'], check=True)
# Captions on top, cleaned voice under, short fade at the very end.
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f'{R}/base.mp4', '-i', f'{R}/caps/captions.mov', '-i', S + '/voice/enhanced.wav',
  '-filter_complex', f'[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];[2:a]afade=t=out:st={END-0.4:.2f}:d=0.4[a]',
  '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-profile:v', 'high', '-crf', '17', '-preset', 'slow', '-r', str(FPS), '-pix_fmt', 'yuv420p',
  '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', f'{R}/discover-architecture-reel.mp4'], check=True)
print('done', dur(f'{R}/discover-architecture-reel.mp4'))
