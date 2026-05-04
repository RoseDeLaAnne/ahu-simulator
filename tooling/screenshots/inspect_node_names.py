"""Quick utility: dump node names from window.pvu3d to verify classification."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8767/#3d-studio"


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_function(
            "() => !!(window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized())",
            timeout=20000,
        )
        page.wait_for_timeout(4500)
        result = page.evaluate(
            "() => (window.pvu3d && window.pvu3d.getMeshRoles) ? window.pvu3d.getMeshRoles() : null"
        )
        if not result:
            print("getMeshRoles not available")
            return
        out_path = Path(__file__).resolve().parent / "node_names.txt"
        with out_path.open("w", encoding="utf-8") as fh:
            from collections import Counter
            kinds = Counter(item["kind"] for item in result)
            sections = Counter((item["section"] or "-") for item in result)
            fh.write(f"Total mesh entries: {len(result)}\n")
            fh.write(f"Kinds: {dict(kinds)}\n")
            fh.write(f"Sections: {dict(sections)}\n\n")
            for item in sorted(result, key=lambda x: (x["source"], x["kind"], x["name"])):
                fh.write(
                    f"[{item['source']}] kind={item['kind']:<22} section={(item['section'] or '-'):<10} "
                    f"name={item['name']:<50} parent={item['parent']}\n"
                )
        print(f"Wrote {out_path}")
        browser.close()


if __name__ == "__main__":
    main()
