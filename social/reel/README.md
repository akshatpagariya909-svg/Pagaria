# Launch reel

Tools for the first Instagram reel: the owner records the voice, Claude makes the visuals.

- `enhance.sh in.m4a out.wav` cleans the voice recording: cuts rumble, reduces steady background noise, evens the level, lowers noise in pauses, adds light voice EQ, de-essing and compression, and sets Instagram loudness (about -14 LUFS, peaks under -1.5 dB). Needs ffmpeg.
- `transcribe.mjs audio16k.wav <models dir> out.json` writes the words with their timings, for captions and for cutting the visuals to the voice. It runs Whisper small offline through `@huggingface/transformers@3.7.5`; the model files come from the npm package `sts-whisper-small` (fetched with `npm pack`, which runs no install scripts). Convert audio first with `ffmpeg -i in.wav -ar 16000 -ac 1 audio16k.wav`.
- `record.js` records phone-sized (1080 × 1920, 30 fps) clips of the site served locally on port 8765 (`cd site && python3 -m http.server 8765`): the wall scrolling, Shuffle, Surprise me (set to land on Chand Baori), an opened building, and the filters. Taps show a soft circle so viewers can follow. Run `node social/reel/record.js [clip ...]` with Playwright on `NODE_PATH`.

The video files themselves are not committed; they are large and easy to remake.

## Making the reel from a voice recording

Everything runs in one work folder `W` (Claude used its scratchpad): `W/voice/raw.m4a` is the recording.

1. `enhance.sh W/voice/raw.m4a W/voice/enhanced.wav`, then convert to 16 kHz and run `transcribe.mjs` to get `W/voice/words.json`.
2. `scenes/scenes.html` holds the title scenes (intro wall, unnamed moodboard, search box, flipping cards, wordmark, photo credit, end card), in the site's colours and type. Serve `scenes/` on port 8766 with a link `scenes/images → site/images`, serve `site/` on 8765, then `OUT=W/reel/clips node record.js` records every clip and scene and logs when each tap happens.
3. `captions.py W` groups the words into short lines (with fixes for misheard words such as "Arc Daily"); `render_caps.js W <seconds>` draws each line with the spoken word in sunset red.
4. `assemble.py W` cuts each clip to the voice, stretching the site clips slightly so every tap lands on the word that names it, overlays captions and adds the cleaned voice. Output: `W/reel/discover-architecture-reel.mp4` (1080 × 1920, 30 fps, about -14 LUFS).

`caption.txt` is the post caption, with credits for every photo in the title scenes (under Instagram's 2,200-character limit).

## Free AI voice (Kokoro)

`voice/` replaces the recorded voice with a free, offline AI voice, keeping the recording's timing so the cuts and captions still line up.

- Model: Kokoro-82M (Apache-2.0), the q8 ONNX file from the npm package `kokoro-q8-shards` (join `kokoro-q8.part0–5.bin`; sha256 `fbae9257…1478`). Voices and text handling come from `kokoro-js@1.2.1`; the tokenizer is Kokoro's own `tokenizer.json`, found bundled in `expo-kokoro`. Packages were fetched with `npm pack`, which runs no install scripts.
- `units.py W <voice>` splits the original words into phrases at natural pauses and records where each started. `script_lines.json` is the text each phrase is voiced from (the owner's words, lightly tidied).
- `voiceover.py W <voice> out.wav` voices each phrase with `tts.mjs` and places it where the original started, speeding a phrase up (at most 1.3x) only if it would run into the next.
- `unit_words.sh W <voice> words.json` transcribes each phrase on its own for exact captions, then the usual `captions.py`, `render_caps.js` and `assemble.py` build the reel.
