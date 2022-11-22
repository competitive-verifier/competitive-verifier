---
---

# 競プロライブラリに自動で verify をしてくれる CI を簡単に設定できる Web ページ

- [English Version](installer.html)
- [日本語バージョン](installer.ja.html)

## 設定手順
1. **GitHub Actions テンプレート** を埋める。
1. <a id="create-action" target="_blank">作成画面</a> を開き、 **GitHub Actions テンプレート** の内容をコピペする
1. 下の方にある緑の `Commit new file` ボタンを押す

## おまけの手順
1.  `README.md` に <input type="text" readonly id="badge-verify-raw"> と書き足す (バッジ <a id="badge-verify-link" target="_blank"><img id="badge-verify-img"></a> が貼られる)
1.  `README.md` に <input type="text" readonly id="badge-pages-raw"> と書き足す (バッジ <a id="badge-pages-link" target="_blank"><img id="badge-pages-img"></a> が貼られる)

## GitHub Actions テンプレート
{%- include installer.template.html -%}
