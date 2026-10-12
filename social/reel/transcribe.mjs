// Transcribe a 16 kHz mono WAV with Whisper small, offline, with word timings.
import { pipeline, env } from '@huggingface/transformers';
import fs from 'fs';
env.allowRemoteModels = false;
env.localModelPath = process.argv[3];
const wav = fs.readFileSync(process.argv[2]);
// Read 16-bit PCM data from a canonical WAV (find the 'data' chunk).
let off = 12, data;
while (off < wav.length) { const id = wav.toString('ascii', off, off + 4), size = wav.readUInt32LE(off + 4);
  if (id === 'data') { data = wav.subarray(off + 8, off + 8 + size); break; } off += 8 + size; }
const pcm = new Float32Array(data.length / 2);
for (let i = 0; i < pcm.length; i++) pcm[i] = data.readInt16LE(i * 2) / 32768;
const asr = await pipeline('automatic-speech-recognition', 'Xenova/whisper-small', { dtype: 'q8' });
let out;
try { out = await asr(pcm, { return_timestamps: 'word', chunk_length_s: 30, stride_length_s: 5, language: 'en', task: 'transcribe' }); }
catch (e) { console.error('word timestamps failed, using segments:', e.message);
  out = await asr(pcm, { return_timestamps: true, chunk_length_s: 30, stride_length_s: 5, language: 'en', task: 'transcribe' }); }
fs.writeFileSync(process.argv[4], JSON.stringify(out, null, 1));
console.log(out.text);
