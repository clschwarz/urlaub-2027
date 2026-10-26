#!/usr/bin/env python3
"""Fetch resort pages, collect image URLs from the HTML (incl. lazy-load attrs), download the
largest ones, resize to max 1400px and store as images/<prefix>-NN.jpg plus a manifest."""
import re, sys, io, os, html, urllib.request, urllib.parse
from PIL import Image

TARGETS = {
    "oasis": [
        "https://www.grecotel.com/luxme-oasis/olympia-aqua-park/",
        "https://www.grecotel.com/luxme-oasis/family-holidays/",
        "https://www.grecotel.com/luxme-oasis/",
    ],
    "botanica": [
        "https://costabotanica.grecotel.com",
        "https://www.grecotel.com/resort-costabotanica/",
        "https://www.tropicalsky.co.uk/europe-holidays/greece/corfu/grecotel-lux-me-costa-botanica",
    ],
    "bluebay": [
        "https://jet2holidays.com/greece/rhodes/ialyssos/blue-bay-resort",
        "https://www.easyjet.com/en/holidays/greece/rhodes/ialyssos/blue-bay-resort",
    ],
    "kids": [
        "https://ikosresorts.com/resorts/ikos-olivia/kids/",
        "https://ikosresorts.com/resorts/ikos-odisia/kids/",
        "https://www.sani-resort.com/en/family",
        "https://www.sani-resort.com/en/sani-club",
        "https://www.marriott.com/en-us/hotels/klxwi-the-westin-resort-costa-navarino/experiences/childrens-activities/",
    ],
}
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "text/html,*/*"}
IMG_RE = re.compile(r'https?://[^\s"\'<>\\]+?\.(?:jpe?g|png|webp)(?:\?[^\s"\'<>\\]*)?', re.I)
SKIP = re.compile(r'logo|icon|favicon|sprite|flag|badge|award|payment|avatar|placeholder|loader|arrow|map_|/map|pin\.|svg|tripadvisor|trustpilot|1x1|blank|dummy', re.I)

def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read() if binary else r.read().decode("utf-8", "replace")

os.makedirs("images", exist_ok=True)
for prefix, pages in TARGETS.items():
    seen, cands = set(), []
    for p in pages:
        try:
            doc = html.unescape(get(p))
        except Exception as e:
            print(prefix, "page failed", p, e); continue
        for m in IMG_RE.findall(doc):
            u = m.strip()
            if SKIP.search(u) or u in seen: continue
            seen.add(u); cands.append(u)
    print(prefix, "candidates", len(cands))
    keep, n = [], 0
    for u in cands:
        if n >= 10: break
        try:
            data = get(u, binary=True)
            im = Image.open(io.BytesIO(data)); im.load()
        except Exception as e:
            continue
        w, h = im.size
        if w < 700 or h < 400 or w / h > 3.5 or h / w > 1.6: continue
        n += 1
        out = f"images/{prefix}-{n:02d}.jpg"
        im = im.convert("RGB"); im.thumbnail((1400, 1400))
        im.save(out, "JPEG", quality=82, optimize=True)
        keep.append(f"{out} {w}x{h} {u}")
        print("saved", out, w, h, u[:100])
    with open(f"images/{prefix}.txt", "w") as f:
        f.write("\n".join(keep) + "\n")
