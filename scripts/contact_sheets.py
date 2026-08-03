from pathlib import Path
from PIL import Image, ImageDraw
import sys, re

folder = Path(sys.argv[1])
files = sorted(folder.glob("page-*.png"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)))
thumb_w = 296
for batch in range(0, len(files), 8):
    chunk = files[batch:batch+8]
    thumbs = []
    for f in chunk:
        im = Image.open(f).convert("RGB")
        h = round(im.height * thumb_w / im.width)
        im = im.resize((thumb_w, h))
        canvas = Image.new("RGB", (thumb_w, h+28), "white")
        canvas.paste(im, (0, 28))
        ImageDraw.Draw(canvas).text((8, 6), f.stem, fill="black")
        thumbs.append(canvas)
    cell_h = max(im.height for im in thumbs)
    sheet = Image.new("RGB", (thumb_w*4, cell_h*2), (225,225,225))
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i%4)*thumb_w, (i//4)*cell_h))
    sheet.save(folder / f"contact-{batch//8+1}.jpg", quality=88)
