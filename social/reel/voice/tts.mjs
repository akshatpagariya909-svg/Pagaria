// Offline Kokoro-82M speech: kokoro-js does the text clean-up, phonemes and voice styles;
// the ONNX model runs directly in onnxruntime-node, and the tokenizer is Kokoro's own vocab.
// usage: node tts.mjs <model.onnx> <tokenizer.json> <lines.json> <outdir>
//   lines.json: [{ "id": "a", "text": "...", "voice": "am_michael", "speed": 1 }]
import { KokoroTTS } from 'kokoro-js';
import { Tensor } from '@huggingface/transformers';
import * as ort from 'onnxruntime-node';
import fs from 'fs';
const [modelPath, tokPath, linesPath, out] = process.argv.slice(2);
const vocab = JSON.parse(fs.readFileSync(tokPath, 'utf8')).model.vocab;
const session = await ort.InferenceSession.create(modelPath);
const tokenizer = phonemes => {
  const ids = [0, ...[...phonemes].map(ch => vocab[ch]).filter(x => x !== undefined), 0];
  return { input_ids: new Tensor('int64', BigInt64Array.from(ids.map(BigInt)), [1, ids.length]) };
};
const model = async ({ input_ids, style, speed }) => {
  const feeds = {};
  for (const name of session.inputNames) {
    const t = name.includes('style') ? style : name.includes('speed') ? speed : input_ids;
    feeds[name] = new ort.Tensor(t.type, t.data, t.dims);
  }
  const r = await session.run(feeds);
  return { waveform: r[session.outputNames[0]] };
};
const tts = new KokoroTTS(model, tokenizer);
fs.mkdirSync(out, { recursive: true });
for (const l of JSON.parse(fs.readFileSync(linesPath, 'utf8'))) {
  const audio = await tts.generate(l.text, { voice: l.voice, speed: l.speed || 1 });
  audio.save(`${out}/${l.id}.wav`);
  console.log(l.id, (audio.audio.length / audio.sampling_rate).toFixed(2) + 's');
}
