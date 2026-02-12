#!/usr/bin/env python3
"""
Batch upload Polycam orbit videos to YouTube.
Reads captures from src/data/polycam.json, uploads each .mp4,
and updates the JSON with YouTube video IDs.

Prerequisites:
  1. Enable YouTube Data API v3 in Google Cloud Console
  2. Create OAuth 2.0 Desktop credentials
  3. Save client_secret.json to priv/client_secret.json

Usage:
  source .venv/bin/activate
  python scripts/upload-to-youtube.py
"""

import json
import os
import sys
import time
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "src" / "data" / "polycam.json"
VIDEO_DIR = ROOT / "public" / "polycam"
CLIENT_SECRET = ROOT / "priv" / "client_secret.json"
TOKEN_FILE = ROOT / "priv" / "yt_token.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service():
    """Authenticate and return a YouTube API service."""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                print(f"ERROR: {CLIENT_SECRET} not found.")
                print("Download OAuth credentials from Google Cloud Console")
                print("and save as priv/client_secret.json")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET), SCOPES
            )
            creds = flow.run_local_server(port=8080)

        TOKEN_FILE.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, video_path: Path, title: str, description: str) -> str:
    """Upload a single video and return the YouTube video ID."""
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["polycam", "3d scan", "photogrammetry", "orbit"],
            "categoryId": "28",  # Science & Technology
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  uploading... {pct}%", end="\r")

    video_id = response["id"]
    print(f"  ✓ https://youtu.be/{video_id}")
    return video_id


def main():
    # Load captures
    with open(DATA_FILE) as f:
        captures = json.load(f)

    print(f"Found {len(captures)} captures")

    # Check which ones already have YouTube IDs
    to_upload = [c for c in captures if not c.get("youtubeId")]
    already = len(captures) - len(to_upload)
    if already:
        print(f"  {already} already uploaded, {len(to_upload)} remaining")

    if not to_upload:
        print("All videos already uploaded!")
        return

    # Check video files exist
    for c in to_upload:
        video_path = VIDEO_DIR / f"{c['id']}.mp4"
        if not video_path.exists():
            print(f"WARNING: {video_path} not found, will skip {c['name']}")

    # Authenticate
    print("\nAuthenticating with YouTube...")
    youtube = get_authenticated_service()
    print("Authenticated!\n")

    # Upload each video
    for i, c in enumerate(to_upload):
        video_path = VIDEO_DIR / f"{c['id']}.mp4"
        if not video_path.exists():
            print(f"[{i+1}/{len(to_upload)}] SKIP {c['name']} (no file)")
            continue

        title = f"{c['name']} - 3D Scan Orbit"
        description = (
            f"3D scan of {c['name']} captured with Polycam.\n"
            f"View on Polycam: https://poly.cam/capture/{c['id']}\n"
            f"More at: https://felipegalind0.io"
        )

        print(f"[{i+1}/{len(to_upload)}] {c['name']}")
        try:
            video_id = upload_video(youtube, video_path, title, description)
            c["youtubeId"] = video_id

            # Save after each upload (in case of crash)
            with open(DATA_FILE, "w") as f:
                json.dump(captures, f, indent=2)

            # Rate limit: YouTube API has a quota
            if i < len(to_upload) - 1:
                time.sleep(2)

        except Exception as e:
            print(f"  ERROR: {e}")
            # Save progress so far
            with open(DATA_FILE, "w") as f:
                json.dump(captures, f, indent=2)
            continue

    print(f"\nDone! {DATA_FILE} updated with YouTube IDs.")


if __name__ == "__main__":
    main()
