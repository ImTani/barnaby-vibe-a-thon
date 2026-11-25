#!/usr/bin/env bash
# Review a rendered shot: a contact sheet (every Nth frame, first and last included) and the frame-to-frame
# difference curve (spikes = pops). Usage: bash video/v2/world/anim/review.sh <shot_id> [N]
set -e
W="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
D="$W/out/anim/$1"; N="${2:-8}"; R="$W/out/_anim_review"; mkdir -p "$R"
n=$(ls "$D"/*.jpg | wc -l)
sel=$(for i in $(seq 1 "$N" "$n") "$n"; do printf "%s/%04d.jpg " "$D" "$i"; done | tr ' ' '\n' | sort -u | tr '\n' ' ')
magick montage -label '%t' $sel -tile 6x -geometry 320x180+2+2 -pointsize 12 "$R/$1_sheet.jpg"
ffmpeg -loglevel error -framerate 24 -i "$D/%04d.jpg" -vf "scale=480:-1,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null - \
  | grep YAVG | awk -F= '{v=$2; printf "%d:%.1f ", NR+1, v} END {print ""}' > "$R/$1_diff.txt"
echo "$n frames; sheet $R/$1_sheet.jpg"; cat "$R/$1_diff.txt"
