---
redirect_from:
- /installer.en.html
---

# Tool to set up automated verification CI by GitHub Actions

- <a class="lang-link" data-path="installer.html" href="installer.html">English Version</a>
- <a class="lang-link" data-path="installer.ja.html" href="installer.ja.html">日本語バージョン</a>

## To set up automated verification
1. Fill configs of **GitHub Actions template**.
1. Open <a id="create-action" target="_blank">New action</a> page and paste **GitHub Actions template**.
1. Open <a id="settings-pages" target="_blank">GitHub Pages settings</a> and change `Source` setting to **GitHub Actions**.
1. Click the green `Commit new file` button.

## Additonal
1.  (Additional) Add <input type="text" readonly id="badge-verify-raw"> to `README.md` (The badge <a id="badge-verify-link" target="_blank"><img id="badge-verify-img"></a> will be added)
1.  (Additional) Add <input type="text" readonly id="badge-pages-raw"> to `README.md` (The badge <a id="badge-pages-link" target="_blank"><img id="badge-pages-img"></a> will be added)

## GitHub Actions template
{%- include installer.template.html -%}
