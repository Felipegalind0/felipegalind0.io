#!/usr/bin/env python3
"""
Scrape Polycam profile page for capture data (thumbnails + orbit videos).
Downloads orbit videos to public/polycam/ and writes a JSON manifest
for the PolycamGallery widget to consume.

Usage:
    source .venv/bin/activate
    python scripts/scrape-polycam.py [--username Felipegalind0]
"""

import argparse
import json
import re
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "public" / "polycam"
MANIFEST = ROOT / "src" / "data" / "polycam.json"


def scrape_captures(username: str) -> list[dict]:
    """Open the Polycam profile in a headless browser and extract capture data."""
    url = f"https://poly.cam/@{username}"
    print(f"Scraping {url} ...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Scroll to load all captures
        prev_count = 0
        for _ in range(20):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            links = page.query_selector_all("a[href*='/capture/']")
            if len(links) == prev_count and len(links) > 0:
                break
            prev_count = len(links)

        # Scroll back to top
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        # Extract basic data from all capture links
        captures = page.evaluate("""() => {
            const links = document.querySelectorAll('a[href*="/capture/"]');
            return Array.from(links).map(a => {
                const href = a.getAttribute('href') || '';
                const idMatch = href.match(/capture\\/([A-F0-9-]+)/i);
                const img = a.querySelector('img');
                const alt = img ? img.getAttribute('alt') : null;
                const name = alt ? alt.replace(' 3D Model', '').trim() : null;
                return {
                    id: idMatch ? idMatch[1] : null,
                    name: name,
                    thumbnail: img ? img.src : null,
                };
            });
        }""")

        # Hover over each capture to get video URLs
        links = page.query_selector_all("a[href*='/capture/']")
        print(f"Found {len(links)} captures, hovering to extract video URLs...")

        for i, link in enumerate(links):
            link.scroll_into_view_if_needed()
            link.hover()
            page.wait_for_timeout(800)

            # Find the video element that appeared
            video = page.query_selector(f"a[href*='{captures[i]['id']}'] video source, a[href*='{captures[i]['id']}'] video")
            if video:
                src = video.get_attribute("src")
                if src:
                    captures[i]["video"] = src
                    print(f"  [{i+1}/{len(links)}] {captures[i]['name']}: got video")
                else:
                    print(f"  [{i+1}/{len(links)}] {captures[i]['name']}: video element but no src")
            else:
                print(f"  [{i+1}/{len(links)}] {captures[i]['name']}: no video")

        browser.close()

    captures = [c for c in captures if c.get("id")]
    print(f"\nExtracted {len(captures)} captures")
    return captures


def download_file(url: str, dest: Path) -> bool:
    """Download a file if it doesn't already exist."""
    if dest.exists():
        print(f"  skip (exists): {dest.name}")
        return True
    try:
        print(f"  downloading: {dest.name}")
        urllib.request.urlretrieve(url, str(dest))
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Scrape Polycam captures")
    parser.add_argument("--username", default="Felipegalind0")
    args = parser.parse_args()

    captures = scrape_captures(args.username)

    if not captures:
        print("No captures found!")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    manifest = []
    for i, cap in enumerate(captures):
        cid = cap["id"]
        entry = {
            "id": cid,
            "name": cap.get("name") or f"capture-{i}",
            "polyUrl": f"https://poly.cam/capture/{cid}",
        }

        # Download video
        if cap.get("video"):
            video_name = f"{cid}.mp4"
            if download_file(cap["video"], OUT_DIR / video_name):
                entry["video"] = f"/polycam/{video_name}"

        # Download thumbnail
        if cap.get("thumbnail"):
            thumb_name = f"{cid}_thumb.jpg"
            if download_file(cap["thumbnail"], OUT_DIR / thumb_name):
                entry["thumbnail"] = f"/polycam/{thumb_name}"

        manifest.append(entry)

    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written to {MANIFEST}")
    print(f"Videos/thumbs saved to {OUT_DIR}")
    print(f"Total captures: {len(manifest)}")


if __name__ == "__main__":
    main()
