# Launch reel

Tools for the first Instagram reel: the owner records the voice, Claude makes the visuals.

- `enhance.sh in.m4a out.wav` cleans the voice recording: cuts rumble, reduces steady background noise, evens the level, lowers noise in pauses, adds light voice EQ, de-essing and compression, and sets Instagram loudness (about -14 LUFS, peaks under -1.5 dB). Needs ffmpeg.
- `transcribe.mjs audio16k.wav <models dir> out.json` writes the words with their timings, for captions and for cutting the visuals to the voice. It runs Whisper small offline through `@huggingface/transformers@3.7.5`; the model files come from the npm package `sts-whisper-small` (fetched with `npm pack`, which runs no install scripts). Convert audio first with `ffmpeg -i in.wav -ar 16000 -ac 1 audio16k.wav`.
- `record.js` records phone-sized (1080 × 1920, 30 fps) clips of the site served locally on port 8765 (`cd site && python3 -m http.server 8765`): the wall scrolling, Shuffle, Surprise me (set to land on Chand Baori), an opened building, and the filters. Taps show a soft circle so viewers can follow. Run `node social/reel/record.js [clip ...]` with Playwright on `NODE_PATH`.

The video files themselves are not committed; they are large and easy to remake.
