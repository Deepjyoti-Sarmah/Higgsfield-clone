#!/usr/bin/env bash
# T-030: synthesise the four source stills used to build the preset previews.
# Run once from the repo root: bash apps/api/app/adapters/fixtures/preview_sources/make_sources.sh
set -euo pipefail
cd "$(dirname "$0")"

render() {
  local out="$1" top="$2" bottom="$3"
  ffmpeg -y -loglevel error -f lavfi \
    -i "gradients=s=1280x720:c0=${top}:c1=${bottom}:x0=0:y0=0:x1=1280:y1=720:d=1" \
    -vf "noise=alls=8:allf=t+u,format=rgb24" -frames:v 1 "$out"
}

render source-01.jpg 0x0b1f2a 0x1f6f6b
render source-02.jpg 0x1a0b2a 0x6b1f5a
render source-03.jpg 0x2a120b 0x6b4a1f
render source-04.jpg 0x0b1a2a 0x2f4a7a
echo "wrote 4 sources in $(pwd)"
