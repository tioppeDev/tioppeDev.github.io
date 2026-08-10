#!/usr/bin/env python3
"""Markdown development logs to Hatena Blog drafts via AtomPub.

Draft format:
---
title: 記事タイトル
date: 2026-08-09
categories: ニポラ島日記,Unity,開発日記
---
本文...
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape


def env(name: str) -> str:
    """Read a required secret/config value and trim accidental whitespace."""
    return os.environ[name].strip()


def auth_header(hatena_id: str, api_key: str) -> str:
    token = base64.b64encode(f"{hatena_id}:{api_key}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def parse_draft(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: YAML風front matterがありません")
    _, header, body = text.split("---\n", 2)
    meta: dict[str, str] = {}
    for line in header.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"{path}: front matterの行を解釈できません: {line}")
        meta[key.strip()] = value.strip()
    if not meta.get("title"):
        raise ValueError(f"{path}: title がありません")
    if not meta.get("date"):
        raise ValueError(f"{path}: date がありません")
    return meta, body.strip() + "\n"


def build_atom(meta: dict[str, str], body: str, hatena_id: str) -> bytes:
    categories = [x.strip() for x in meta.get("categories", "").split(",") if x.strip()]
    date = meta["date"]
    updated = datetime.fromisoformat(f"{date}T12:00:00+09:00").isoformat()
    category_xml = "\n".join(f'  <category term="{escape(c)}" />' for c in categories)
    xml = f'''<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
  <title>{escape(meta["title"])}</title>
  <author><name>{escape(hatena_id)}</name></author>
  <content type="text/plain">{escape(body)}</content>
  <updated>{updated}</updated>
{category_xml}
  <app:control>
    <app:draft>yes</app:draft>
    <app:preview>no</app:preview>
  </app:control>
</entry>
'''
    return xml.encode("utf-8")


def verify_auth(hatena_id: str, blog_id: str, api_key: str) -> None:
    """Verify credentials against the AtomPub service document before posting."""
    endpoint = f"https://blog.hatena.ne.jp/{hatena_id}/{blog_id}/atom"
    req = urllib.request.Request(
        endpoint,
        method="GET",
        headers={
            "Authorization": auth_header(hatena_id, api_key),
            "User-Agent": "tioppe-devlog-publisher/1.1",
        },
    )
    print(f"auth check endpoint: {endpoint}")
    print(f"hatena id length: {len(hatena_id)}, blog id length: {len(blog_id)}, api key length: {len(api_key)}")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response.read(1)
            print(f"auth check: HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Hatena auth check HTTP {exc.code}: {detail}") from exc


def publish(path: Path, hatena_id: str, blog_id: str, api_key: str) -> None:
    endpoint = f"https://blog.hatena.ne.jp/{hatena_id}/{blog_id}/atom/entry"
    meta, body = parse_draft(path)
    payload = build_atom(meta, body, hatena_id)
    req = urllib.request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={
            "Authorization": auth_header(hatena_id, api_key),
            "Content-Type": "application/atom+xml; charset=utf-8",
            "User-Agent": "tioppe-devlog-publisher/1.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Hatena API HTTP {exc.code}: {detail}") from exc

    root = ET.fromstring(response_body)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    edit = root.find("atom:link[@rel='edit']", ns)
    alternate = root.find("atom:link[@rel='alternate']", ns)
    print(f"draft created: {meta['title']}")
    if edit is not None:
        print(f"edit: {edit.attrib.get('href', '')}")
    if alternate is not None:
        print(f"url: {alternate.attrib.get('href', '')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path, help="投稿するMarkdownファイル")
    args = parser.parse_args()
    required = ("HATENA_ID", "HATENA_BLOG_ID", "HATENA_API_KEY")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("missing environment variables: " + ", ".join(missing), file=sys.stderr)
        return 2

    hatena_id = env("HATENA_ID")
    blog_id = env("HATENA_BLOG_ID")
    api_key = env("HATENA_API_KEY")
    verify_auth(hatena_id, blog_id, api_key)
    for path in args.files:
        publish(path, hatena_id, blog_id, api_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
