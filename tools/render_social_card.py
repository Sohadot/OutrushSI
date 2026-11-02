"""Render the source SVG to a crawler-compatible 1200x630 JPEG."""
from pathlib import Path
from io import BytesIO
import cairosvg
from PIL import Image

root = Path(__file__).resolve().parents[1]
source = root / "assets/social-card.svg"
output = root / "assets/social-card.jpg"
image = Image.open(BytesIO(cairosvg.svg2png(url=str(source)))).convert("RGB")
assert image.size == (1200, 630)
image.save(output, "JPEG", quality=90, optimize=True, progressive=True, subsampling=0)
assert output.stat().st_size < 1000000
print(f"Generated {output} ({output.stat().st_size} bytes)")
