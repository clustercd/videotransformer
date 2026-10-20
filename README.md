# VideoTransformer

A local video download, conversion and organization toolkit with a Flask dashboard.
Download from supported sources, convert media with FFmpeg, browse local videos,
and optionally describe frames with BLIP or export organized videos to Andrew.

## Quick start

Requirements: Python 3.10 or newer and FFmpeg on `PATH`. The Windows launchers
create a local `videotrans` virtual environment; this directory is not source code.

```powershell
.\INSTALL.bat
.\START.bat
```

Open [the dashboard](http://127.0.0.1:5000). It binds to loopback and is intended
for one local user. It has no account system or production deployment setup.
File and folder pickers open native dialogs on the machine running the app.

Manual setup, including Linux and macOS:

```sh
python -m venv .venv
# Activate .venv with the command appropriate to your shell.
python -m pip install -r requirements-web.txt
python web/app.py
```

The dashboard loads CSS, icons and Socket.IO from public CDNs. These assets and
downloads require network access. Conversions use the locally installed FFmpeg.

## Features

| Feature | Behavior |
| --- | --- |
| Downloads | Individual URLs, batches, channels/playlists, Facebook, Pexels and Wikimedia |
| Library | Browse local media with filename search and folder filters |
| Conversion | Audio/video formats, WAV extraction and short GIF clips |
| Queue | One background worker, task status and local activity logs |
| Optional analysis | BLIP frame captions, with preview or filename updates |
| Organization | Keyword categories and an optional Andrew export |

Source access and licensing vary. A search result or downloader filter does not
guarantee permission to download or redistribute a video. Review each source's
terms and attribution requirements. No downloaded media is included here.

## Configuration

| Setting | Purpose |
| --- | --- |
| `PIXABAY_API_KEY` | Optional key for `python -m src.download_educational` |
| `PEXELS_API_KEY` | Your Pexels key; needed only for Pexels downloads |
| `VIDEOTRANSFORMER_DATA_DIR` | Media and private state; defaults to `data/` |
| `VIDEOTRANSFORMER_LOGS_DIR` | Activity logs; defaults to `logs/` |
| `VIDEOTRANSFORMER_SECRET_KEY` | Optional stable Flask secret; otherwise generated per process |
| `ANDREW_HOME` | Optional Andrew export root; defaults to `~/Andrew` |

Set variables in your shell before starting. `.env.example` documents the names;
the application does not automatically load `.env` files.

Pexels can also read `private_settings.json` under the configured data root:

```json
{"pexels_api_key": "YOUR_PEXELS_API_KEY"}
```

That file is private and ignored by Git. The dashboard accepts a key for the
current process without returning it in configuration responses. A blank field
keeps the current key. Dashboard changes do not persist after restart.

## Optional analysis

```sh
python -m pip install -r requirements.txt
python -m src.video_analyzer_light
```

This installs the larger PyTorch, Transformers and OpenCV stack. The first BLIP
run downloads model weights; later inference can use cached weights. Model
analysis and renaming are optional and are not run during dashboard startup.
Review a preview before renaming your files.

## Windows commands

| Command | Purpose |
| --- | --- |
| `START.bat`, `RUN_WEB.bat` | Start the local dashboard |
| `INSTALL.bat` | Install dashboard dependencies |
| `CONVERT_WMV.bat` | Convert WMV files without overwriting existing outputs |
| `RUN_LIGHT.bat` | Run the optional BLIP analyzer |
| `TEST_QUICK.bat` | Analyze up to five local videos; requires AI dependencies |
| `ORGANIZE.bat` | Copy videos into keyword categories |
| `COPIER_VERS_ANDREW.bat` | Copy organized MP4 files and write an Andrew index |
| `ORGANISER_ANDREW.bat` | Build the optional Andrew hierarchy |
| `CLEANUP.bat` | Preview cache cleanup; never deletes documentation or media |
| `DOWNLOAD_YOUTUBE.bat` | Run preset educational YouTube searches |
| `DOWNLOAD_WIKIMEDIA.bat`, `DOWNLOAD_TARGETED.bat` | Run Wikimedia search presets |
| `DOWNLOAD_PEXELS_TARGETED.bat` | Run Pexels search presets |
| `DOWNLOAD_ECOLE.bat`, `DOWNLOAD_FRANCAIS.bat` | Run French educational search presets |
| `DOWNLOAD_CEST_PAS_SORCIER.bat`, `DOWNLOAD_IL_ETAIT_UNE_FOIS.bat` | Run topic-based French educational searches |

Use the dashboard for an individual URL. Legacy command filenames, category IDs
and French search phrases are retained for compatibility and French-language
content discovery; the interface and documentation are in English.

Andrew integration is optional. Export commands copy files and can replace their
generated indexes; review the destination before running them.

## Development and release checks

```sh
python -m unittest discover -s tests -v
python scripts/audit_public.py
python scripts/audit_git_history.py
```

See [privacy and publication](docs/PRIVACY.md) and [validation](docs/VALIDATION.md).
Local media, cookies, downloaded URLs, logs, environments and personal settings
are excluded from Git. Do not publish a raw copy of an installed working folder.

## License

No project-wide license file has been established. The previous README's MIT
statement was not accompanied by a license file. A maintainer must choose the
license before describing this project as open-source software. Dependencies,
models and downloaded media retain their own terms.
