# i18n Updater

Detect missing translations, extract new strings, and update catalogs.

## Usage

```
/i18n-updater
```

## Steps

1. **Extract messages**: Run `make babel-extract` to regenerate `translations/messages.pot`
2. **Compare with existing catalogs**:
   - Read `translations/en/LC_MESSAGES/messages.po`
   - Identify new msgid entries that have empty msgstr
   - Identify obsolete entries (marked `#~ msgid`)
3. **Translate new entries**:
   - For each new msgid (French text), write the English msgstr
   - Keep `%(variable)s` placeholders intact
   - Match the tone: buttons are short ("Restart", "Next"), descriptions are natural
4. **Update catalogs**: Run `make babel-update` to merge new strings into existing .po files
5. **Compile**: Run `make babel-compile` to generate .mo files
6. **Verify**: Run `make test` to ensure nothing is broken

## Scan for unwrapped strings

Also scan templates and Python files for French text not wrapped in `_()` or `_l()`:
- Templates: look for French text outside `{{ _('...') }}`
- Python mode descriptions: check all `description` properties use `_l()`
- Route flash messages or log messages visible to users

## Reference files

- Babel config: `babel.cfg`
- POT template: `translations/messages.pot`
- EN catalog: `translations/en/LC_MESSAGES/messages.po`
- FR catalog: `translations/fr/LC_MESSAGES/messages.po`
