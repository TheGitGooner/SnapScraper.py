#!/usr/bin/python3
__author__ = "https://codeberg.org/allendema (enhanced)"

"""
SnapScraper - Enhanced Snapchat public story/highlight/spotlight downloader.

Usage:
    python3 SnapScraper.py USERNAME [USERNAME2 ...]
    python3 SnapScraper.py --file usernames.txt
    python3 SnapScraper.py                         # prompts for usernames
"""

from time import sleep
import time
import json
import sys
import os
import re
import argparse
from datetime import datetime, timezone

from bs4 import BeautifulSoup
import requests

# ──────────────────────────────────────────────
# ANSI colours
# ──────────────────────────────────────────────
GREEN  = "\033[1;32;40m"
RED    = "\033[31m"
YELLOW = "\033[33m"
RESET  = "\033[0m"

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) "
        "Gecko/20100101 Firefox/103.0.2"
    )
}
BASE_STORY_URL  = "https://story.snapchat.com/@"
MAX_RETRIES     = 4
RETRY_BACKOFF   = [1, 3, 7, 15]
MAX_FILENAME    = 200


# ──────────────────────────────────────────────
# Filename helpers
# ──────────────────────────────────────────────

def sanitise(text: str) -> str:
    """Strip characters unsafe in filenames."""
    return re.sub(r'[\\/:*?"<>|]', "_", str(text))


def build_filename(username: str, media_type: str, dt_str: str, uid: str, ext: str) -> str:
    """
    Format:  username__mediatype__datetime__uid.ext
    When truncating, uid is shortened first; username and datetime are never cut.
    """
    parts = [sanitise(username), sanitise(media_type), sanitise(dt_str), sanitise(uid)]
    name  = "__".join(parts) + ext
    if len(name) <= MAX_FILENAME:
        return name
    uid_budget = max(8, MAX_FILENAME - len(ext)
                     - len(sanitise(username))
                     - len(sanitise(media_type))
                     - len(sanitise(dt_str))
                     - 3)   # 3 double-underscore separators
    return "__".join([sanitise(username), sanitise(media_type),
                      sanitise(dt_str), sanitise(uid)[:uid_budget]]) + ext


def format_ts(raw) -> str:
    """Convert a unix timestamp (seconds or ms, may be a string) to YYYYMMDD_HHMMSS UTC."""
    try:
        ts = int(raw)
        if ts > 1_000_000_000_000:   # milliseconds → seconds
            ts //= 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    except Exception:
        return datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")


# ──────────────────────────────────────────────
# Network helpers
# ──────────────────────────────────────────────

def session_get(url: str, stream: bool = False):
    """GET with retry + exponential backoff. Returns Response or None."""
    for attempt, wait in enumerate(RETRY_BACKOFF, 1):
        try:
            r = requests.get(url, headers=HEADERS, stream=stream, timeout=25)
            if r.status_code == 200:
                return r
            print(f"{YELLOW}  [retry {attempt}/{MAX_RETRIES}] HTTP {r.status_code} — waiting {wait}s…{RESET}")
        except requests.RequestException as exc:
            print(f"{YELLOW}  [retry {attempt}/{MAX_RETRIES}] {exc} — waiting {wait}s…{RESET}")
        sleep(wait)
    return None


def fetch_page_json(username: str) -> dict | None:
    """Fetch story.snapchat.com/@<username> and return its __NEXT_DATA__ JSON."""
    url = BASE_STORY_URL + username
    r   = session_get(url)
    if r is None:
        print(f"{RED}  ✗  Could not reach Snapchat for '{username}'.{RESET}")
        return None
    soup = BeautifulSoup(r.content, "html.parser")
    tag  = soup.find(id="__NEXT_DATA__")
    if not tag:
        print(f"{RED}  ✗  No page data found for '{username}'. Account may not exist.{RESET}")
        return None
    try:
        return json.loads(tag.string.strip())
    except json.JSONDecodeError:
        print(f"{RED}  ✗  JSON parse error for '{username}'.{RESET}")
        return None


def download_file(url: str, filepath: str) -> bool:
    """Download url → filepath with retries. Skips if file already exists."""
    if os.path.isfile(filepath):
        print(f"  ⏭  Already exists: {os.path.basename(filepath)}")
        return True
    r = session_get(url, stream=True)
    if r is None:
        print(f"{RED}  ✗  Failed: {os.path.basename(filepath)}{RESET}")
        return False
    with open(filepath, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"  ✓  {os.path.basename(filepath)}")
    return True


def ext_for_snap(snap: dict) -> str:
    """
    snapMediaType 0 = image, 1 = video.
    Falls back to checking the URL extension.
    """
    media_type = snap.get("snapMediaType", 0)
    if media_type == 1:
        return ".mp4"
    url = (snap.get("snapUrls") or {}).get("mediaUrl", "")
    if ".mp4" in url.lower():
        return ".mp4"
    return ".jpeg"


# ──────────────────────────────────────────────
# Snap extraction helpers
# ──────────────────────────────────────────────

def uid_from_url(url: str) -> str:
    """
    Extract the unique content ID embedded in Snapchat CDN URLs.
    Pattern:  .../d/<UNIQUE_ID>.<size>.IRZXSOY?...
    The segment before the first dot is unique per snap and stable —
    e.g. "gvbCOJ833kDMOQOplVxpi" (21 chars). This means highlight snaps
    that share a timestamp but are different split-parts of one video
    will always get different filenames and never be skipped as duplicates.
    Falls back to an MD5 hash of the full URL if the pattern is not found.
    """
    m = re.search(r"/d/([^./?]+)", url)
    if m:
        return m.group(1)
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()[:16]


def get_snap_parts(snap: dict) -> tuple:
    """
    Return (media_url, uid, dt_str) from a snap dict.
    When snapId is empty (always the case for highlight snaps), we derive
    a unique ID from the CDN URL path, which contains a per-snap content hash.
    This prevents split-video parts from being mistaken for duplicates.
    """
    media_url = (snap.get("snapUrls") or {}).get("mediaUrl", "")
    snap_id   = (snap.get("snapId") or {}).get("value", "")
    raw_ts    = (snap.get("timestampInSec") or {}).get("value", 0)
    uid = snap_id if snap_id else uid_from_url(media_url)
    return media_url, str(uid)[:48], format_ts(raw_ts)


# ──────────────────────────────────────────────
# Profile check
# ──────────────────────────────────────────────

def check_public(data: dict, username: str) -> bool:
    ppi = ((data.get("props") or {})
               .get("pageProps") or {})  \
               .get("userProfile") or {}  \
               .get("publicProfileInfo") or {}

    # A robust way to walk the nested dict
    try:
        ppi = data["props"]["pageProps"]["userProfile"]["publicProfileInfo"]
    except KeyError:
        ppi = {}

    bio     = ppi.get("bio", "")
    bitmoji = ppi.get("snapcodeImageUrl", "")

    if bio or bitmoji:
        print(f"{GREEN}  Bio     : {bio}{RESET}")
        print(f"  Bitmoji : {bitmoji}")
        return True

    # Private profile fallback
    try:
        info = data["props"]["pageProps"]["userProfile"]["userInfo"]
        print(f"  Display : {info.get('displayName', '')}")
    except KeyError:
        pass
    print(f"{RED}  Profile is private or not found — skipping.{RESET}")
    return False


# ──────────────────────────────────────────────
# Stories  (24-hour active story)
# ──────────────────────────────────────────────

def download_stories(username: str, data: dict, save_dir: str):
    try:
        snap_list = data["props"]["pageProps"]["story"]["snapList"]
    except KeyError:
        print("  No active stories in the last 24 h.")
        return

    if not snap_list:
        print("  No active stories in the last 24 h.")
        return

    print(f"\n  📸  Stories ({len(snap_list)} found)")
    for snap in snap_list:
        media_url, uid, dt_str = get_snap_parts(snap)
        if not media_url:
            continue
        ext      = ext_for_snap(snap)
        filename = build_filename(username, "story", dt_str, uid, ext)
        download_file(media_url, os.path.join(save_dir, filename))
        sleep(0.25)


# ──────────────────────────────────────────────
# Highlights  (curated highlight reels)
# Key confirmed from debug JSON: props.pageProps.curatedHighlights
# Each entry:  storyTitle.value  /  highlightId.value  /  snapList[…]
# ──────────────────────────────────────────────

def download_highlights(username: str, data: dict, save_dir: str):
    try:
        highlights = data["props"]["pageProps"]["curatedHighlights"]
    except KeyError:
        highlights = []

    if not highlights:
        print("  No highlights found.")
        return

    print(f"\n  ⭐  Highlights ({len(highlights)} reels found)")

    for hl in highlights:
        # Title is nested: storyTitle -> value
        title_raw = (hl.get("storyTitle") or {}).get("value", "") or "untitled"
        title     = sanitise(title_raw[:40])

        snap_list = hl.get("snapList") or []
        if not snap_list:
            print(f"  ⚠  Highlight '{title_raw}' is empty — skipping.")
            continue

        print(f"\n     ↳ '{title_raw}' ({len(snap_list)} snaps)")

        for snap in snap_list:
            media_url, uid, dt_str = get_snap_parts(snap)
            if not media_url:
                continue
            ext      = ext_for_snap(snap)
            filename = build_filename(username, f"highlight_{title}", dt_str, uid, ext)
            download_file(media_url, os.path.join(save_dir, filename))
            sleep(0.25)


# ──────────────────────────────────────────────
# Spotlights
# Key confirmed from debug JSON: props.pageProps.spotlightHighlights
# Each entry has snapList with exactly 1 snap (snapMediaType=1 = video)
# The snap ID (the long base64 string) lives in snapId.value
# ──────────────────────────────────────────────

def download_spotlights(username: str, data: dict, save_dir: str):
    try:
        spotlights = data["props"]["pageProps"]["spotlightHighlights"]
    except KeyError:
        spotlights = []

    if not spotlights:
        print("  No spotlights found.")
        return

    print(f"\n  🔦  Spotlights ({len(spotlights)} found)")

    for sp in spotlights:
        snap_list = sp.get("snapList") or []
        for snap in snap_list:
            media_url, uid, dt_str = get_snap_parts(snap)
            if not media_url:
                continue
            ext      = ext_for_snap(snap)   # always .mp4 for spotlights
            filename = build_filename(username, "spotlight", dt_str, uid, ext)
            download_file(media_url, os.path.join(save_dir, filename))
            sleep(0.25)


# ──────────────────────────────────────────────
# Per-profile orchestration
# ──────────────────────────────────────────────

def process_profile(username: str):
    username = username.strip().lstrip("@")
    if not username:
        return

    print(f"\n{'='*60}")
    print(f"  👻  Processing: @{username}")
    print(f"{'='*60}")

    data = fetch_page_json(username)
    if data is None:
        return

    if not check_public(data, username):
        return

    save_dir = os.path.abspath(username)
    os.makedirs(save_dir, exist_ok=True)

    download_stories(username, data, save_dir)
    download_highlights(username, data, save_dir)
    download_spotlights(username, data, save_dir)

    print(f"\n  ✅  Finished @{username}  →  {save_dir}")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="SnapScraper — download public Snapchat stories, highlights & spotlights."
    )
    parser.add_argument(
        "usernames", nargs="*", metavar="USERNAME",
        help="One or more Snapchat usernames."
    )
    parser.add_argument(
        "--file", "-f", metavar="FILE",
        help="Text file with one username per line (# lines are ignored)."
    )
    return parser.parse_args()


def collect_usernames(args) -> list:
    usernames = list(args.usernames)
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                file_users = [
                    line.strip() for line in fh
                    if line.strip() and not line.startswith("#")
                ]
            usernames.extend(file_users)
        except FileNotFoundError:
            print(f"{RED}File not found: {args.file}{RESET}")
            sys.exit(1)
    if not usernames:
        raw = input("Enter username(s) separated by spaces or commas: ")
        usernames = [u.strip() for u in re.split(r"[\s,]+", raw) if u.strip()]
    return usernames


def main():
    start     = time.perf_counter()
    args      = parse_args()
    usernames = collect_usernames(args)

    if not usernames:
        print(f"{RED}No usernames provided. Exiting.{RESET}")
        sys.exit(1)

    print(f"\n{GREEN}SnapScraper — {len(usernames)} profile(s) to process{RESET}")

    for username in usernames:
        process_profile(username)

    elapsed = time.perf_counter() - start
    print(f"\n\n{'='*60}")
    print(f"  All done!  Total time: {elapsed:.1f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
