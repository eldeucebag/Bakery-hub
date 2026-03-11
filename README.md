# Reticulum Community Server Viewer

A Flet-based application that connects to a Reticulum community server and displays received announces.

**Targets:** Linux (Desktop) and Android

## Community Server

This app connects to:
- **Hash**: `99b91c274bd7c2b926426618a3c2dbbd480cae10eadf9d53aabb873d2bbbbb71`
- **Port**: `4242`

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

- Connects to the specified Reticulum community server
- Displays received announces with source, data, and timestamp
- Connect/Disconnect toggle button
- Clear button to remove displayed announces
- Real-time status updates
- Auto-scrolls to newest announces
- Cross-platform: Linux desktop and Android mobile

## Requirements

- Python 3.8+
- Flet
- Reticulum Network Stack (RNS)

## Project Structure

```
client/
├── main.py              # Main application
├── requirements.txt     # Python dependencies
├── flet.yaml           # Flet build configuration
├── README.md           # This file
└── .github/
    └── workflows/
        └── build.yml   # GitHub Actions CI/CD
```
