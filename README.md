# SnapScraper.py
Downloads public Snapchat stories, highlights, and spotlights.

> **Forked from [allendema/SnapScrap.py](https://github.com/allendema/SnapScrap.py) and significantly enhanced with the help of Claude.**

## What's new in this fork
- Download **highlights** (curated story reels) and **spotlights** in addition to active stories
- **Batch mode** — scrape multiple profiles in one command or from a text file
- **Content toggles** — skip stories, highlights, or spotlights per-run with `--no-stories`, `--no-highlights`, `--no-spotlights`
- **Smart file naming** — every file is named `username__mediatype__datetime__uid.ext` so files are always organized and never overwritten incorrectly
- **Duplicate prevention** — unique IDs are derived from Snapchat's own CDN content hashes, even for split-video snaps that share a timestamp; a persistent `downloaded.txt` manifest means duplicates are avoided even after moving files out of the folder
- **Emoji-safe filenames** — emojis and non-ASCII symbols in highlight titles are automatically stripped so filenames work on all operating systems
- **Automatic retries** — failed downloads retry up to 4 times with exponential backoff

---

## Installation

```bash
git clone https://github.com/TheGitGooner/SnapScraper.py.git
cd SnapScraper.py/
pip3 install -r requirements.txt
```

**Requirements** (`requirements.txt`):
```
requests
beautifulsoup4
```

---

## Usage

```bash
# Single username
python3 SnapScraper.py USERNAME

# Multiple usernames at once
python3 SnapScraper.py USERNAME1 USERNAME2 USERNAME3

# From a text file (one username per line, # lines are ignored)
python3 SnapScraper.py --file usernames.txt

# No arguments — script will prompt you
python3 SnapScraper.py

# Stories only — fastest, great for your daily check-in run
python3 SnapScraper.py --file usernames.txt --no-highlights --no-spotlights

# Skip spotlights but grab stories + highlights
python3 SnapScraper.py --file usernames.txt --no-spotlights

# Single user, highlights only
python3 SnapScraper.py tomfrommyspace --no-stories --no-spotlights
```

### Content toggles

All three content types are downloaded by default. Use these flags to skip any you don't need:

| Flag | What it skips |
|---|---|
| `--no-stories` | Current 24-hour story snaps |
| `--no-highlights` | All highlight reels |
| `--no-spotlights` | All spotlight clips |

The script will print a summary of what it's downloading (and skipping) at the start of each run so you always know what mode you're in.

### usernames.txt example
```
# My list of profiles to scrape
tomfrommyspace
someotheruser
# anotheruser  ← commented out, will be skipped
```
## In Action
![inAction](https://github.com/TheGitGooner/SnapScraper.py/blob/main/example1Fullscrape.png)

---

## Output

Each profile gets its own folder named after the username. Files inside are named:

```
username__mediatype__YYYYMMDD_HHMMSS__uniqueid.ext
```

For example:
```
tomfrommyspace/
├── tomfrommyspace__story__20260220_153042__gvbCOJ833kDM.jpeg
├── tomfrommyspace__highlight_Hehe__20260218_204549__gulgiJJsVmDm.jpeg
├── tomfrommyspace__highlight_Gym__20260218_160545__hTFyafj9Jh6R.mp4
├── tomfrommyspace__spotlight__20260210_091233__W7_EDlXWTBiX.mp4
└── downloaded.txt
```

> **`downloaded.txt`** is the manifest — a record of every file that has been downloaded. It stays in the folder even if you move the media files out, so future scrapes won't re-download anything already captured.

**Media types in filenames:**
- `story` — active 24-hour story snaps
- `highlight_<title>` — snaps from a named highlight reel
- `spotlight` — spotlight video clips

---

## Your directory later

![Directory](https://github.com/TheGitGooner/SnapScraper.py/blob/main/example2Outputfiles.png)

---

## Notes
- Only works with **public profiles**
- Private profiles are detected and skipped automatically
- Re-running the script on the same profile safely skips files that already exist
- Spotlights are always saved as `.mp4`; stories and highlights can be `.jpeg` or `.mp4`

---

## Heads Up
Use at your own risk. Use it to archive important things, be polite, be respectful, and cause no harm.

Original script by [allendema](https://codeberg.org/allendema) (2022).  
Enhanced fork by [TheGitGooner](https://github.com/TheGitGooner).

[![License: Apache License 2.0](https://img.shields.io/github/license/TheGitGooner/SnapScraper.py)](https://github.com/TheGitGooner/SnapScraper.py/blob/main/LICENSE)
[![github commits](https://img.shields.io/github/last-commit/TheGitGooner/SnapScraper.py)](https://github.com/TheGitGooner/SnapScraper.py/commits/main)
