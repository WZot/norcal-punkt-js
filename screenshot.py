#!/usr/bin/env python3
"""Take a screenshot of the generated calendar page using Playwright."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Screenshot the calendar page")
    parser.add_argument(
        "-i", "--input", default="dist/index.html",
        help="Path to the HTML file (default: dist/index.html)",
    )
    parser.add_argument(
        "-o", "--output", default="screenshot.png",
        help="Output screenshot path (default: screenshot.png)",
    )
    parser.add_argument(
        "--width", type=int, default=1280,
        help="Viewport width (default: 1280)",
    )
    parser.add_argument(
        "--full-page", action="store_true", default=True,
        help="Capture full page (default: True)",
    )
    args = parser.parse_args()

    html_path = Path(args.input).resolve()
    if not html_path.exists():
        print(f"Error: {html_path} not found. Run generate.py first.", file=sys.stderr)
        sys.exit(1)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": 800})
        page.goto(f"file://{html_path}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=args.output, full_page=args.full_page)
        browser.close()

    print(f"Screenshot saved to {args.output}")


if __name__ == "__main__":
    main()
