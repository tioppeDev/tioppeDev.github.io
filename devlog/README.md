# 開発ブログ運用

ChatGPTとの開発会話を一次資料として、その日に行った開発を日単位の記事へ整理し、はてなブログへ下書き投稿する。

## 記録ルール

- 日付境界は日本時間（Asia/Tokyo）。
- 原則として **1日 = 1記事**。
- 複数日をまとめる依頼では、日付ごとに別ファイル・別記事を作る。
- 主な一次資料はChatGPTとのやり取り。会話で実際に行ったこと、判断したこと、失敗したこと、確認結果を残す。
- GitHubのcommit / PR / docsは、日付や実装結果を裏付ける補助資料として使う。
- 会話やGitHubで確認できない出来事は創作しない。
- 単なるコミット一覧ではなく「何を目指したか → 何を試したか → 何が起きたか → どう判断したか」が読める開発日記にする。
- 技術的な失敗や方針変更も省略しない。後から同じ問題を踏まないための記録として扱う。
- API投稿は常に `app:draft=yes`。自動公開しない。

## ファイル

下書きは `devlog/drafts/YYYY-MM-DD-<slug>.md` に置く。

```md
---
title: 記事タイトル
date: 2026-08-09
categories: ニポラ島日記,Unity,開発日記
---

本文
```

## ChatGPTへ依頼するときの基本形

> ChatGPTで今日行った開発を、開発ブログ用にまとめてください。日本時間の日付単位で1記事にしてください。複数日の内容がある場合は日ごとに別記事にしてください。会話を一次資料とし、必要に応じてGitHubのcommit/PRで事実確認してください。確認できないことは補完しないでください。完成した下書きを `devlog/drafts/` に追加してください。

## はてなブログへの送信

GitHub Actions `Publish Hatena Drafts` を手動実行する。

`drafts` にはファイル名だけを指定する。

1件:

```text
2026-08-09-nipora-3d.md
```

複数件:

```text
2026-08-08-nipora-3d.md,2026-08-09-nipora-3d.md
```

同じファイルを再度実行すると別の下書きとして重複投稿されるため、送信対象は明示指定する。

## GitHub Actions Secrets

Repository Settings → Secrets and variables → Actions に以下を登録する。

- `HATENA_ID`: はてなID
- `HATENA_BLOG_ID`: ブログID（例: `example.hatenablog.com`）
- `HATENA_API_KEY`: はてなブログのAPIキー

APIキーはパスワード相当の秘密情報なので、ファイルやcommitへ書かない。
