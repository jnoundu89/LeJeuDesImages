---
name: update-translations
description: Extract new i18n strings, translate to EN, compile catalogs
---

# Update Translations

1. Run `make babel-extract` to regenerate `translations/messages.pot`
2. Run `make babel-update` to merge into existing .po files
3. Read `translations/en/LC_MESSAGES/messages.po`
4. Find entries with empty `msgstr ""` and fill in English translations
5. Run `make babel-compile` to generate .mo files
6. Run `make test` to verify

Keep translations natural and concise. Preserve `%(variable)s` placeholders exactly.
