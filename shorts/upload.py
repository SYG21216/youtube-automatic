#!/usr/bin/env python3
"""upload.py - upload one video to YouTube with only the stdlib.

    python3 upload.py video.mp4 --title "..." [--desc "..."] [--privacy private|unlisted|public]

Reads YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN from the environment.
A vertical video under 3 minutes is treated as a Short by YouTube automatically.
"""
import argparse, json, os, sys, urllib.parse, urllib.request

def access_token():
    body = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen("https://oauth2.googleapis.com/token", body) as r:
        return json.load(r)["access_token"]

def upload(path, title, desc, privacy):
    tok = access_token()
    meta = {"snippet": {"title": title[:100], "description": desc, "categoryId": "26",
                        "defaultLanguage": "ko", "defaultAudioLanguage": "ko"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/*", "X-Upload-Content-Length": str(os.path.getsize(path))})
    with urllib.request.urlopen(req) as r:
        loc = r.headers["Location"]
    # ponytail: single PUT, no chunk resume - fine for Shorts (<100MB); add chunking if uploads time out
    with open(path, "rb") as f:
        put = urllib.request.Request(loc, data=f.read(), method="PUT",
                                     headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/*"})
        with urllib.request.urlopen(put) as r:
            return json.load(r)["id"]

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("video"); p.add_argument("--title", required=True)
    p.add_argument("--desc", default=""); p.add_argument("--privacy", default="private")
    a = p.parse_args()
    missing = [k for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(k)]
    if missing: sys.exit(f"missing env: {', '.join(missing)}")
    vid = upload(a.video, a.title, a.desc, a.privacy)
    print(f"https://youtube.com/shorts/{vid}")
