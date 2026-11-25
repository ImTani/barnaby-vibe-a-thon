"""Exposure stats for review: luma percentiles, clipped share, mean saturation, and the black level, per image.

  runtime/voice/.venv/Scripts/python scripts/dev/img_stats.py a.png b.jpg ...   [--crop x0,y0,x1,y1 as fractions]
"""
from __future__ import annotations

import sys

import numpy as np
from PIL import Image


def stats(path: str, crop=None) -> str:
    im = Image.open(path).convert("RGB")
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    a = np.asarray(im, dtype=np.float32) / 255.0
    y = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 1e-3, (mx - mn) / np.maximum(mx, 1e-3), 0)
    p = np.percentile(y, [1, 5, 50, 95, 99]) * 255
    clip = float((mx > 0.985).mean() * 100)
    return (f"{path.split('/')[-1][:34]:34} luma p1 {p[0]:5.1f} p5 {p[1]:5.1f} p50 {p[2]:5.1f} p95 {p[3]:5.1f} "
            f"p99 {p[4]:5.1f} | clip {clip:5.2f}% | sat {sat.mean():.3f}")


if __name__ == "__main__":
    args, crop = [], None
    it = iter(sys.argv[1:])
    for a in it:
        if a == "--crop":
            crop = [float(v) for v in next(it).split(",")]
        else:
            args.append(a)
    for a in args:
        print(stats(a.replace("\\", "/"), crop))
