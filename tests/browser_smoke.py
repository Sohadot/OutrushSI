"""Ephemeral desktop/mobile browser smoke and screenshot capture.

Runs only in GitHub Actions. No live deployment or external network requests.
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "browser-preview"
OUTPUT.mkdir(parents=True, exist_ok=True)
SERVER = subprocess.Popen(
    [sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1", "--directory", str(ROOT)],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
BASE = "http://127.0.0.1:8765"

try:
    time.sleep(1)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        results = []
        for label, width, height in [
            ("desktop", 1440, 1000),
            ("tablet", 820, 1050),
            ("mobile", 390, 844),
            ("mobile-small", 320, 700),
        ]:
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            for path, suffix in [("/", "concept"), ("/acquire/", "acquire")]:
                response = page.goto(BASE + path, wait_until="networkidle")
                assert response is not None and response.status == 200, f"{label}: {path}: HTTP response"
                assert page.locator("h1").is_visible(), f"{label}: {path}: missing H1"
                assert page.locator("a[href='/acquire/']").count() > 0 or path == "/acquire/", f"{label}: missing acquisition path"
                if path == "/acquire/":
                    assert page.locator('a[href*="dynadot.com/fr/market/user-listings/outrush.si"]').count() == 1
                    assert page.locator('a[href^="mailto:agent@sohadot.com"]').count() >= 1
                else:
                    assert page.locator("svg.flow-visual").count() == 1
                    assert page.locator("#meaning").count() == 1
                dimensions = page.evaluate("({ viewport: innerWidth, page: document.documentElement.scrollWidth })")
                assert dimensions["page"] <= dimensions["viewport"] + 2, (
                    f"{label}: {path}: horizontal overflow {dimensions}"
                )
                await_path = OUTPUT / f"{label}-{suffix}.png"
                page.screenshot(path=str(await_path), full_page=True, animations="disabled")
                results.append({"viewport":label,"page":suffix,"horizontalOverflow":False,"screenshot":str(await_path.relative_to(ROOT))})
            assert not errors, f"{label}: JS exceptions: {errors}"
            page.close()
        # Simulate a touch-first handset requesting a larger desktop viewport.
        # This catches the miniature desktop layout seen in the user's screenshot.
        touch = browser.new_context(
            viewport={"width": 980, "height": 1000},
            device_scale_factor=1,
            has_touch=True,
            is_mobile=True,
        )
        touch_page = touch.new_page()
        touch_page.goto(BASE + "/", wait_until="networkidle")
        touch_layout = touch_page.evaluate("""() => ({
            coarse: matchMedia('(pointer: coarse)').matches,
            columns: getComputedStyle(document.querySelector('.hero')).gridTemplateColumns,
            navHidden: getComputedStyle(document.querySelector('.desktop-nav')).display === 'none'
        })""")
        assert touch_layout["coarse"], f"Touch emulation not active: {touch_layout}"
        assert touch_layout["navHidden"], f"Desktop navigation should collapse on touch: {touch_layout}"
        touch_page.screenshot(path=str(OUTPUT / "touch-desktop-request-concept.png"), full_page=True, animations="disabled")
        results.append({"viewport":"touch-desktop-request","page":"concept","screenshot":"artifacts/browser-preview/touch-desktop-request-concept.png"})
        touch.close()
        browser.close()
        (OUTPUT / "manifest.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(json.dumps(results, indent=2))
finally:
    SERVER.terminate()
    try:
        SERVER.wait(timeout=4)
    except subprocess.TimeoutExpired:
        SERVER.kill()
