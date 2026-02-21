# SnapScraper.py
Downloads public Snapchat stories, highlights, and spotlights.

> **Forked from [allendema/SnapScrap.py](https://github.com/allendema/SnapScrap.py) and significantly enhanced with the help of Claude.**

## What's new in this fork
- Download **highlights** (curated story reels) and **spotlights** in addition to active stories
- **Batch mode** — scrape multiple profiles in one command or from a text file
- **Smart file naming** — every file is named `username__mediatype__datetime__uid.ext` so files are always organized and never overwritten incorrectly
- **Duplicate prevention** — unique IDs are derived from Snapchat's own CDN content hashes, even for split-video snaps that share a timestamp
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
```

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
├── tomfrommyspace__story__20260220_153042__gvbCOJ833kDMOQOplVxpi.jpeg
├── tomfrommyspace__highlight_Hehe__20260218_204549__gulgiJJsVmDmWgc48yZFA.jpeg
├── tomfrommyspace__highlight_Gym__20260218_160545__hTFyafj9Jh6RZan62594H.mp4
└── tomfrommyspace__spotlight__20260210_091233__W7_EDlXWTBiXAEEniNoMP.mp4
```

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
