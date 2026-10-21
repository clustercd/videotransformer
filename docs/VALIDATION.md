# Release validation — 20 October 2026

- Twenty isolated regression tests pass.
- All project Python files and both embedded JavaScript programs pass syntax checks.
- Real FFmpeg conversion passes on synthetic audio; input and existing output files are preserved.
- Browser checks pass for the English dashboard, conversion panel and empty library on an isolated local server.
- The Windows cleanup launcher runs in preview mode and preserves media and documentation.
- The source privacy audit passes with an external private reference list.

The publication checks cover Python syntax, embedded dashboard JavaScript,
English templates and documentation, isolated Flask routes, private configuration
handling, cache cleanup boundaries, source exclusions and Git object auditing.
Tests use synthetic temporary directories and mock external downloads. They do
not read or modify the installed media collection or browser cookies.

```sh
python -m pip install -r requirements-web.txt
python -m unittest discover -s tests -v
python scripts/audit_public.py
python scripts/audit_git_history.py
```

Live downloads, private account sessions, MediaLibrary export and BLIP model inference
require separate user-specific acceptance testing. Provider availability and
media licenses are not certified by these checks. No real download, media
rename or MediaLibrary export is performed as part of publication validation.
