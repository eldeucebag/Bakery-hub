# Reticulum Community Hub Browser

A Flet-based application that connects to the Community Hub via Reticulum Network Stack (RNS) and displays micron pages.

**Targets:** Linux (Desktop) and Android

## Community Hub

This app connects to:
- **Yggdrasil Address**: `56c4f7b24c4d6e0380871c06533352666da9312d7bc9fa3b0bfeaeb4a49465e1`
- **RNS Destination Hash**: `f97f412b9ef6d1c2330ca5ee28ee9e31`
- **Page Path**: `/page/index.mu`

## Installation

### Linux (Desktop)

```bash
pip install -r requirements.txt
python main.py
```

### Android

Build the APK:

```bash
pip install flet[build]
flet build android --release
```

The APK will be in `dist/` directory. Install on your Android device.

## Building

### Linux AppImage

```bash
flet build linux --release
```

### Android APK

```bash
flet build android --release
```

## CI/CD with GitHub Actions

This repo includes GitHub Actions workflows that automatically build for both Linux and Android on every push.

**Free tier limits:**
- Public repos: 2,000 minutes/month
- Builds run on GitHub's hosted runners

## Features

- Connects to the Community Hub via RNS over Yggdrasil
- Loads and displays nomadnet-compatible micron pages
- Simple micron markup rendering (headings, links, bullets)
- Connect/Disconnect toggle button
- Refresh button to reload pages
- Real-time status updates
- Cross-platform: Linux desktop and Android mobile

## Requirements

- Python 3.11+
- Flet
- Reticulum Network Stack (rnspure)
- Yggdrasil network connection (for reaching the hub)

## Project Structure

```
client/
├── main.py              # Main application
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration
├── README.md           # This file
└── .github/
    └── workflows/
        └── build.yml   # GitHub Actions CI/CD
```

## How It Works

1. The app initializes the Reticulum Network Stack
2. Requests a path to the hub's RNS destination
3. Establishes an encrypted RNS Link to the hub
4. Requests the index page (`/page/index.mu`) via RNS request/response
5. Renders the micron markup content in the UI
