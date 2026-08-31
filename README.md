# Tofu Desktop Companion

A tiny interactive desktop cat companion for macOS.

Tofu lives on your desktop and provides lightweight productivity tools without turning into a full productivity dashboard. Double-click Tofu to open its compact menu.

## Features

- Focus timer
- Water tracking
- Reminders
- Talk to Tofu
- Beans and unlockable items
- Friendship progression
- Achievements
- Personal diary/history
- Time-of-day dialogue
- Occasional random events
- Draggable always-on-top desktop companion

Tofu does not punish you for ignoring it, and friendship does not decay.

## Download for macOS

For the easiest installation, open the **Releases** section of this repository and download `Tofu.zip` from the latest release.

Unzip it, drag `Tofu.app` into Applications, and open it.

Because the app is not Apple-notarized, macOS may block the first launch. If that happens, go to **System Settings → Privacy & Security → Open Anyway**.

## Run from source

Requires Python 3 and PyQt6.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python tofu.py
```

## Data and privacy

Tofu stores its local companion data on your own Mac in:

```text
~/Library/Application Support/Tofu/
```

Personal progress, diary entries, beans, friendship, and reminders are not included in this repository.

## Project structure

```text
tofu.py
assets/
  pose_a.png
  pose_b.png
  TofuIcon.png
requirements.txt
README.md
.gitignore
```

## Platform

Currently built for macOS.
