#!/bin/sh
# Clean up a voice recording for Instagram.
#  1. cut rumble, reduce steady background noise (fan, hum, hiss)
#  2. bring speech to a set level, then gently lower the noise in pauses
#  3. voice EQ, soft de-ess, light compression
#  4. -14 LUFS loudness, peaks under -1.5 dB (two passes)
# usage: enhance.sh in.(m4a|wav|mp3|mp4) out.wav
set -e
IN="$1"; OUT="$2"
CLEAN="highpass=f=80,lowpass=f=15000,afftdn=nr=24:nf=-50:tn=1"
# Pass 1: how loud is the speech after cleaning?
I=$(ffmpeg -hide_banner -i "$IN" -af "$CLEAN,ebur128" -f null - 2>&1 | grep '^ *I:' | tail -1 | awk '{print $2}')
GAIN=$(python3 -c "print(round(-20 - ($I), 2))")
SHAPE="volume=${GAIN}dB,agate=threshold=0.016:ratio=3:attack=4:release=250:range=0.12,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.0:g=2.5,equalizer=f=11000:t=h:w=0.7:g=1.5,deesser=i=0.3,acompressor=threshold=-22dB:ratio=2.5:attack=6:release=120:makeup=2"
# Pass 2: measure for loudnorm, then render.
STATS=$(ffmpeg -hide_banner -i "$IN" -af "$CLEAN,$SHAPE,loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
get() { echo "$STATS" | grep "\"$1\"" | sed 's/.*: "\(.*\)".*/\1/'; }
ffmpeg -hide_banner -loglevel error -y -i "$IN" -af "$CLEAN,$SHAPE,loudnorm=I=-14:TP=-1.5:LRA=9:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true,aresample=48000" -ac 1 -c:a pcm_s16le "$OUT"
echo "speech was $I LUFS; output:" $(ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E '^ *(I|Peak):' | tail -2 | tr -s ' ')
