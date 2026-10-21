"VideoTransformer web dashboard for downloads, conversion and organization."
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request, Response, send_from_directory
from flask_socketio import SocketIO, emit
import threading
import queue
import json
import time
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import urllib.error
import urllib.request
import webbrowser
import secrets
from src.settings import DATA_DIR, LOGS_DIR, get_pexels_key

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('VIDEOTRANSFORMER_SECRET_KEY') or secrets.token_hex(32)
socketio = SocketIO(app)

# Paths
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Task queue and global state
task_queue = queue.Queue()
current_task = None
task_history = []
is_processing = False

# Settings
config = {
    'pexels_api_key': get_pexels_key(),
    'download_dir': str(DATA_DIR / 'downloaded'),
    'organized_dir': str(DATA_DIR / 'organized'),
    'max_file_size_mb': 30,
    'videos_per_query': 3
}

# Sources requiring browser impersonation
IMPERSONATE_SITES = [
    'dailymotion.com',
    'twitter.com',
    'x.com',
    'instagram.com',
    'tiktok.com',
    'bilibili.com',
    'nicovideo.jp',
]

def needs_impersonation(url):
    "Check whether the source needs browser impersonation."
    url_lower = url.lower()
    return any(site in url_lower for site in IMPERSONATE_SITES)

def get_ytdlp_path():
    "Run yt-dlp with the current Python interpreter."
    import sys
    python_exe = sys.executable

    # Use the current interpreter to run yt-dlp reliably
    return [python_exe, '-m', 'yt_dlp']

def normalize_pasted_url(url):
    "Accept a URL pasted as a Markdown link."
    import re
    url = (url or '').strip()
    match = re.fullmatch(r'\[([^\]]+)\]\((https?://[^\s)]+)\)', url)
    return match.group(2) if match else url

def log_message(message, level='info'):
    "Send a WebSocket log entry and save it locally."
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {'time': timestamp, 'level': level, 'message': message}
    socketio.emit('log', log_entry)

    # Save the log entry locally
    log_file = LOGS_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{level.upper()}] {message}\n")

def get_video_stats():
    "Collect local video counts and sizes."
    stats = {
        'total': 0,
        'by_category': {},
        'by_source': {},
        'total_size_mb': 0
    }

    extensions = ['.mp4', '.avi', '.wmv', '.webm', '.mkv', '.mpg', '.mov', '.ogv']

    for ext in extensions:
        for video in DATA_DIR.glob(f"**/*{ext}"):
            stats['total'] += 1
            try:
                stats['total_size_mb'] += video.stat().st_size / (1024 * 1024)
            except:
                pass

            # Use the parent folder as the category
            parent = video.parent.name
            if parent != 'data':
                stats['by_category'][parent] = stats['by_category'].get(parent, 0) + 1

    stats['total_size_mb'] = round(stats['total_size_mb'], 2)
    return stats

def get_queue_status():
    "Return the current queue state."
    return {
        'queue_size': task_queue.qsize(),
        'is_processing': is_processing,
        'current_task': current_task,
        'history': task_history[-10:]
    }

# Worker thread
def task_worker():
    global current_task, is_processing
    while True:
        try:
            task = task_queue.get(timeout=1)
            is_processing = True
            current_task = task

            log_message(f"🚀 Starting: {task['name']}", 'info')
            socketio.emit('task_started', task)

            try:
                result = execute_task(task)
                task['status'] = 'completed'
                task['result'] = result
                log_message(f"✅ Completed: {task['name']}", 'success')
            except Exception as e:
                task['status'] = 'error'
                task['error'] = str(e)
                log_message(f"❌ Error: {task['name']} - {e}", 'error')

            task['completed_at'] = datetime.now().isoformat()
            task_history.append(task)
            socketio.emit('task_completed', task)

            current_task = None
            is_processing = False
            task_queue.task_done()

        except queue.Empty:
            continue

def execute_task(task):
    "Dispatch a queued task."
    task_type = task.get('type')

    if task_type == 'download_direct':
        return run_download_direct(task.get('params', {}))
    elif task_type == 'download_batch':
        return run_download_batch(task.get('params', {}))
    elif task_type == 'download_channel':
        return run_download_channel(task.get('params', {}))
    elif task_type == 'download_facebook':
        return run_download_facebook(task.get('params', {}))
    elif task_type == 'download_youtube':
        return run_download_youtube(task.get('params', {}))
    elif task_type == 'download_pexels':
        return run_download_pexels(task.get('params', {}))
    elif task_type == 'download_wikimedia':
        return run_download_wikimedia(task.get('params', {}))
    elif task_type == 'analyze':
        return run_analyze(task.get('params', {}))
    elif task_type == 'organize':
        return run_organize(task.get('params', {}))
    elif task_type == 'organize_media_library':
        return run_organize_media_library(task.get('params', {}))
    elif task_type == 'convert_to_wav':
        return run_convert_to_wav(task.get('params', {}))
    elif task_type == 'convert_file':
        return run_convert_file(task.get('params', {}))
    else:
        raise ValueError(f"Unknown task type: {task_type}")


def _sanitize_filename(name):
    "Remove characters that are invalid in Windows filenames."
    import re
    # Replace fullwidth Unicode characters with ASCII equivalents
    replacements = {
        '\uff1a': '-',   # ： (fullwidth colon)
        '\uff5c': '-',   # ｜ (fullwidth pipe)
        '\uff1f': '',    # ？ (fullwidth question mark)
        '\uff0a': '',    # ＊ (fullwidth asterisk)
        '\uff02': '',    # ＂ (fullwidth quotation)
        '\uff1c': '',    # ＜
        '\uff1e': '',    # ＞
        '\u2018': "'",   # '
        '\u2019': "'",   # '
        '\u201c': '',    # "
        '\u201d': '',    # "
        '\u2026': '...',  # …
    }
    for char, repl in replacements.items():
        name = name.replace(char, repl)
    # Remove characters forbidden in Windows filenames
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    # Normalize repeated spaces and hyphens
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'-{2,}', '-', name)
    # Limit the filename to 200 characters
    if len(name) > 200:
        name = name[:200]
    return name


def run_convert_file(params):
    "Convert a file or folder with FFmpeg."
    mode = params.get('mode', 'file')      # 'file' | 'folder'
    source = params.get('source', '')
    fmt = params.get('format', 'mp3')
    out_mode = params.get('out_mode', 'same')   # same | subfolder | custom
    out_custom = params.get('out_custom', '')
    overwrite = params.get('overwrite', False)

    if not source:
        raise ValueError("Source required")

    source_path = Path(source)
    if not source_path.exists():
        raise ValueError(f"Source not found: {source}")

    # Collect input files
    media_exts = ['.mp4', '.webm', '.mkv', '.avi', '.ogv', '.mov', '.wmv', '.mpg',
                  '.mp3', '.m4a', '.ogg', '.flac', '.aac', '.opus', '.wav']
    if mode == 'file':
        if source_path.suffix.lower() not in media_exts:
            raise ValueError(f"Unsupported extension: {source_path.suffix}")
        files = [source_path]
        parent = source_path.parent
    else:
        files = [f for ext in media_exts for f in source_path.glob(f'*{ext}')]
        parent = source_path

    if not files:
        log_message(f"⚠️ No media files found", 'warning')
        return {'converted': 0, 'skipped': 0, 'errors': 0}

    # Use a subfolder when the source and output formats match
    if out_mode == 'same':
        # Avoid overwriting source files with matching extensions
        same_ext_conflict = any(f.suffix.lower() == f'.{fmt}' for f in files)
        if same_ext_conflict:
            out_dir = parent / 'converted'
            log_message(f"⚠️ Source and target formats match (.{fmt}) → output redirected to /converted", 'warning')
        else:
            out_dir = parent
    elif out_mode == 'subfolder':
        out_dir = parent / 'converted'
    elif out_mode == 'custom' and out_custom:
        out_dir = Path(out_custom)
    else:
        out_dir = parent
    out_dir.mkdir(parents=True, exist_ok=True)

    log_message(f"🔄 Conversion → .{fmt}: {len(files)} file(s)")
    log_message(f"   Output: {out_dir}")

    # Choose FFmpeg parameters for the output format
    audio_fmts = ['mp3', 'aac', 'ogg', 'm4a', 'opus']
    video_fmts = ['mp4', 'webm', 'mkv', 'avi', 'mov']
    overwrite_flag = '-y' if overwrite else '-n'

    converted = skipped = errors = 0

    for i, src_file in enumerate(files, 1):
        # Sanitize the output filename
        clean_stem = _sanitize_filename(src_file.stem)
        if not clean_stem:
            clean_stem = f'video_{i:03d}'
        out_file = out_dir / (clean_stem + '.' + fmt)

        # Add a suffix if the output path matches the source
        try:
            if out_file.resolve() == src_file.resolve():
                out_file = out_dir / (clean_stem + '_conv.' + fmt)
        except Exception:
            pass

        if out_file.exists() and not overwrite:
            log_message(f"   [{i}/{len(files)}] ⏭️  {src_file.name[:60]} (already converted)")
            skipped += 1
            continue

        log_message(f"   [{i}/{len(files)}] 🔄 {src_file.name[:70]}...")

        cmd = ['ffmpeg', overwrite_flag, '-i', str(src_file)]

        if fmt in audio_fmts:
            bitrate = params.get('bitrate', '192k')
            channels = params.get('channels', '2')
            if fmt == 'mp3':
                cmd += ['-vn', '-acodec', 'libmp3lame', '-ab', bitrate, '-ac', str(channels)]
            elif fmt == 'aac':
                cmd += ['-vn', '-acodec', 'aac', '-b:a', bitrate, '-ac', str(channels)]
            elif fmt == 'ogg':
                cmd += ['-vn', '-acodec', 'libvorbis', '-b:a', bitrate, '-ac', str(channels)]
            elif fmt == 'm4a':
                cmd += ['-vn', '-acodec', 'aac', '-b:a', bitrate, '-ac', str(channels)]
            elif fmt == 'opus':
                cmd += ['-vn', '-acodec', 'libopus', '-b:a', bitrate, '-ac', str(channels)]

        elif fmt == 'wav':
            sr = params.get('sample_rate', 44100)
            ch = params.get('channels', '2')
            cmd += ['-vn', '-acodec', 'pcm_s16le', '-ar', str(sr), '-ac', str(ch)]

        elif fmt == 'flac':
            cmd += ['-vn', '-acodec', 'flac']

        elif fmt == 'gif':
            start = params.get('gif_start', 0)
            duration = params.get('gif_duration', 5)
            fps = params.get('gif_fps', 15)
            # Generate an optimized palette
            palette_file = out_dir / f'_palette_{src_file.stem}.png'
            palette_cmd = ['ffmpeg', '-y', '-ss', str(start), '-t', str(duration),
                           '-i', str(src_file),
                           '-vf', f'fps={fps},scale=640:-1:flags=lanczos,palettegen',
                           str(palette_file)]
            subprocess.run(palette_cmd, capture_output=True, timeout=120)
            cmd = ['ffmpeg', overwrite_flag,
                   '-ss', str(start), '-t', str(duration), '-i', str(src_file),
                   '-i', str(palette_file),
                   '-filter_complex', f'fps={fps},scale=640:-1:flags=lanczos[x];[x][1:v]paletteuse']

        elif fmt in video_fmts:
            resolution = params.get('resolution', '')
            crf = params.get('crf', '23')
            if fmt == 'mp4':
                tv_compat = params.get('tv_compatible', False)
                vf = f'scale=-2:{resolution}' if resolution else ''
                if tv_compat:
                    cmd += ['-vcodec', 'libx264', '-profile:v', 'main', '-level', '4.0',
                            '-pix_fmt', 'yuv420p', '-crf', crf, '-preset', 'fast',
                            '-movflags', '+faststart',
                            '-acodec', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2']
                    if not vf:
                        vf = 'scale=trunc(iw/2)*2:trunc(ih/2)*2'
                    else:
                        vf += ',scale=trunc(iw/2)*2:trunc(ih/2)*2'
                else:
                    cmd += ['-vcodec', 'libx264', '-crf', crf, '-preset', 'fast',
                            '-acodec', 'aac', '-b:a', '128k']
                if vf:
                    cmd += ['-vf', vf]
            elif fmt == 'webm':
                vf = f'scale=-2:{resolution}' if resolution else ''
                cmd += ['-vcodec', 'libvpx-vp9', '-crf', crf, '-b:v', '0',
                        '-acodec', 'libopus', '-b:a', '128k']
                if vf:
                    cmd += ['-vf', vf]
            else:
                # Copy streams when possible for MKV, AVI and MOV
                cmd += ['-vcodec', 'copy', '-acodec', 'copy']

        cmd.append(str(out_file))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0 and out_file.exists():
                size_mb = out_file.stat().st_size / (1024 * 1024)
                log_message(f"      ✅ {out_file.name} ({size_mb:.1f} MB)")
                converted += 1
                # Remove the temporary GIF palette
                if fmt == 'gif':
                    palette_file = out_dir / f'_palette_{src_file.stem}.png'
                    if palette_file.exists():
                        palette_file.unlink()
            else:
                err = (result.stderr or 'erreur inconnue')[-200:]
                log_message(f"      ❌ {err[:120]}", 'error')
                errors += 1
        except FileNotFoundError:
            log_message("❌ ffmpeg not found; add it to PATH", 'error')
            raise ValueError("ffmpeg not found on PATH")
        except subprocess.TimeoutExpired:
            log_message(f"      ⏱️  Timeout: {src_file.name}", 'error')
            errors += 1
        except Exception as e:
            log_message(f"      ❌ {e}", 'error')
            errors += 1

    log_message(f"✅ Completed — {converted} converted, {skipped} skipped, {errors} errors")
    return {'converted': converted, 'skipped': skipped, 'errors': errors, 'output_dir': str(out_dir)}


def run_download_direct(params):
    "Download one URL with yt-dlp."
    url = normalize_pasted_url(params.get('url', ''))
    referer = params.get('referer', '')
    filename = params.get('filename', '')
    destination = params.get('destination', 'direct')
    cookies = params.get('cookies', '')  # chrome, firefox, edge, brave, file

    if not url:
        raise ValueError("URL required")

    # Find yt-dlp
    ytdlp = get_ytdlp_path()

    # Create the destination directory
    dest_dir = DATA_DIR / destination
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Detect the referer when it is not specified
    if not referer:
        if 'uqload' in url.lower():
            referer = 'https://uqload.bz/'
        elif 'vidcloud' in url.lower():
            referer = 'https://vidcloud.co/'
        elif 'streamtape' in url.lower():
            referer = 'https://streamtape.com/'
        elif 'doodstream' in url.lower() or 'dood' in url.lower():
            referer = 'https://doodstream.com/'
        elif 'mixdrop' in url.lower():
            referer = 'https://mixdrop.co/'

    log_message(f"📥 Direct download: {url[:60]}...")
    if referer:
        log_message(f"   Referer: {referer}")

    # Build the yt-dlp command
    cmd = ytdlp.copy()

    # Browser impersonation for sources that require it
    if needs_impersonation(url):
        cmd.extend(['--impersonate', 'chrome'])
        log_message("   🎭 Impersonation: chrome")
    else:
        # Use a standard user agent for other sources
        cmd.extend(['--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'])

    # Optional browser cookies
    if cookies == 'file':
        cookies_file = DATA_DIR / 'cookies.txt'
        if cookies_file.exists():
            cmd.extend(['--cookies', str(cookies_file)])
            log_message("   🍪 Using cookies.txt")
        else:
            log_message("   ⚠️ cookies.txt not found in the data folder", 'warning')
    elif cookies in ['chrome', 'firefox', 'edge', 'brave']:
        cmd.extend(['--cookies-from-browser', cookies])
        log_message(f"   🍪 Cookies from {cookies}")

    if referer:
        cmd.extend(['--referer', referer])

    # Output filename
    if filename:
        output_template = str(dest_dir / f"{filename}.%(ext)s")
    else:
        output_template = str(dest_dir / "%(title).100s_%(id)s.%(ext)s")

    cmd.extend([
        '-o', output_template,
        '--no-playlist',
        '--progress',
        url
    ])

    try:
        log_message(f"   Command: yt-dlp {url[:50]}...")

        # Stream progress with an inactivity timeout rather than a total duration limit
        import select
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        last_activity = time.time()
        inactivity_timeout = 600  # Ten minutes without output triggers a timeout
        last_progress_log = 0

        while True:
            line = None
            try:
                # Read with a short timeout
                import threading as _thr
                result_line = [None]
                def _read():
                    result_line[0] = proc.stdout.readline()
                reader = _thr.Thread(target=_read, daemon=True)
                reader.start()
                reader.join(timeout=30)
                line = result_line[0]
            except Exception:
                pass

            if line is None and proc.poll() is not None:
                break

            if line:
                last_activity = time.time()
                line = line.strip()
                # Throttle yt-dlp progress messages
                now = time.time()
                if line and ('[download]' in line or 'Downloading' in line):
                    if now - last_progress_log > 15:  # Log at most once every 15 seconds
                        # Extract the percentage when available
                        log_message(f"   📊 {line[:120]}")
                        last_progress_log = now
                elif line and 'error' in line.lower():
                    log_message(f"   ⚠️ {line[:150]}", 'warning')
            elif proc.poll() is not None:
                break
            else:
                # Check for inactivity
                if time.time() - last_activity > inactivity_timeout:
                    proc.kill()
                    log_message(f"⏱️ Timeout: no activity for {inactivity_timeout//60} min", 'error')
                    raise Exception(f"Inactivity timeout ({inactivity_timeout//60} min)")

        proc.wait()

        if proc.returncode == 0:
            log_message(f"✅ Download completed!")
            recent_files = sorted(dest_dir.glob('*'), key=lambda x: x.stat().st_mtime, reverse=True)
            if recent_files:
                downloaded_file = recent_files[0]
                size_mb = downloaded_file.stat().st_size / (1024 * 1024)
                log_message(f"   File: {downloaded_file.name} ({size_mb:.1f} MB)")
            return {'status': 'success', 'destination': str(dest_dir)}
        else:
            log_message(f"❌ yt-dlp exit code: {proc.returncode}", 'error')
            raise Exception(f"yt-dlp failed (code {proc.returncode})")

    except Exception as e:
        log_message(f"❌ Error: {e}", 'error')
        raise


def run_download_batch(params):
    "Download a batch of URLs."
    urls = params.get('urls', [])
    referer = params.get('referer', '')
    destination = params.get('destination', 'direct')
    cookies = params.get('cookies', '')

    if not urls:
        raise ValueError("No URLs supplied")

    log_message(f"📥 Batch download: {len(urls)} videos")

    success = 0
    failed = 0

    for i, url in enumerate(urls, 1):
        url = url.strip()
        if not url:
            continue

        log_message(f"[{i}/{len(urls)}] {url[:50]}...")

        try:
            run_download_direct({
                'url': url,
                'referer': referer,
                'filename': '',  # Auto
                'destination': destination,
                'cookies': cookies
            })
            success += 1
        except Exception as e:
            log_message(f"   ❌ Failed: {e}", 'error')
            failed += 1

        # Pause between downloads
        if i < len(urls):
            time.sleep(2)

    log_message(f"📊 Batch completed: {success} succeeded, {failed} failed")
    return {'success': success, 'failed': failed}


def run_download_facebook(params):
    "Download accessible videos from supplied Facebook URLs."
    urls = params.get('urls', [])
    if isinstance(urls, str):
        urls = urls.splitlines()
    urls = [normalize_pasted_url(url.strip()) for url in urls if url.strip()]
    if not urls:
        raise ValueError("Add at least one Facebook URL")
    if any('facebook.com' not in url.lower() for url in urls):
        raise ValueError("All URLs must point to Facebook")

    max_videos = int(params.get('max_videos') or 0)
    cookies = params.get('cookies', '')
    destination = params.get('destination', 'facebook')
    dest_dir = DATA_DIR / destination
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive = DATA_DIR / 'facebook_downloaded_archive.txt'
    successes = 0
    errors = []

    for url in urls:
        log_message(f"📘 Facebook: {url}")
        cmd = get_ytdlp_path() + ['--yes-playlist',
            '-o', str(dest_dir / '%(uploader)s_%(title).100s_%(id)s.%(ext)s'),
            '--no-overwrites', '--download-archive', str(archive),
            '--retries', '3', '--fragment-retries', '3', '--ignore-errors', '--progress']
        if max_videos > 0:
            cmd.extend(['--playlist-end', str(max_videos)])
        if cookies in ['chrome', 'firefox', 'edge', 'brave']:
            cmd.extend(['--cookies-from-browser', cookies])
        elif cookies == 'file':
            cookies_file = DATA_DIR / 'cookies.txt'
            if not cookies_file.exists():
                raise ValueError("cookies.txt not found in the data folder")
            cmd.extend(['--cookies', str(cookies_file)])
        cmd.append(url)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1)
        for line in proc.stdout:
            line = line.strip()
            if line and ('[download]' in line or 'ERROR:' in line or 'WARNING:' in line):
                log_message(f"   {line[:180]}", 'warning' if 'ERROR:' in line else 'info')
        proc.wait()
        if proc.returncode == 0:
            successes += 1
        else:
            errors.append(url)
            log_message(f"❌ Failed Facebook ({proc.returncode}): {url}", 'error')

    if errors and not successes:
        raise Exception("yt-dlp could not extract any supplied Facebook URLs")
    return {'status': 'success', 'urls': len(urls), 'failed': errors, 'destination': str(dest_dir)}


def run_download_channel(params):
    "Download a YouTube channel, search or playlist with filters."
    channel_url = params.get('channel_url', '')
    max_duration = params.get('max_duration', 300)  # Default: five minutes
    max_videos = params.get('max_videos', 20)
    quality = params.get('quality', '480')
    destination = params.get('destination', 'youtube')
    language = params.get('language', '')  # fr, en, es, de, etc.
    shorts_only = params.get('shorts_only', False)
    no_shorts = params.get('no_shorts', True)

    if not channel_url:
        raise ValueError("URL required")

    # Find yt-dlp
    ytdlp = get_ytdlp_path()

    # Create the destination directory
    dest_dir = DATA_DIR / destination
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Identify the URL type
    is_search = 'search_query' in channel_url or '/results?' in channel_url
    is_playlist = 'playlist?list=' in channel_url
    is_channel = '@' in channel_url or '/channel/' in channel_url or '/c/' in channel_url or '/user/' in channel_url

    if is_search:
        log_message(f"🔍 YouTube search download: {channel_url[:60]}...")
    elif is_playlist:
        log_message(f"📝 YouTube playlist download: {channel_url[:60]}...")
    else:
        log_message(f"📺 Channel download: {channel_url}")
        # Append /videos only to channel URLs
        if is_channel and '/videos' not in channel_url:
            if channel_url.endswith('/'):
                channel_url = channel_url + 'videos'
            else:
                channel_url = channel_url + '/videos'

    # Add the requested language to search queries
    if language and is_search:
        lang_names = {'fr': 'français', 'en': 'english', 'es': 'español', 'de': 'deutsch'}
        lang_word = lang_names.get(language, language)

        if 'search_query=' in channel_url:
            channel_url = channel_url.replace('search_query=', f'search_query={lang_word}+')

        log_message(f"   🌐 Language filter: {language.upper()} (added '{lang_word}' to the search)")

    log_message(f"   Filters: duration ≤{max_duration//60}min, max {max_videos} videos")

    # Build the duration filter
    if shorts_only:
        duration_filter = 'duration <= 60'
        log_message("   Mode: Shorts only (<60s)")
    elif no_shorts:
        duration_filter = f'duration > 60 & duration <= {max_duration}'
        log_message(f"   Mode: Regular videos (60s-{max_duration//60}min)")
    else:
        duration_filter = f'duration <= {max_duration}'

    # Select video quality
    if quality == 'best':
        format_spec = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else:
        format_spec = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best[height<={quality}]'

    # Build the yt-dlp command
    cmd = ytdlp.copy()

    # Enable impersonation when needed
    if needs_impersonation(channel_url):
        cmd.extend(['--impersonate', 'chrome'])
        log_message("   🎭 Impersonation: chrome")

    # Add YouTube language options
    if language:
        cmd.extend(['--extractor-args', f'youtube:lang={language}'])
        geo_map = {'fr': 'FR', 'en': 'US', 'es': 'ES', 'de': 'DE'}
        if language in geo_map:
            cmd.extend(['--geo-bypass-country', geo_map[language]])

    cmd.extend([
        '--match-filter', duration_filter,
        '--playlist-end', str(max_videos),
        '-f', format_spec,
        '-o', str(dest_dir / '%(uploader)s_%(title).80s_%(id)s.%(ext)s'),
        '--no-overwrites',
        '--download-archive', str(DATA_DIR / 'downloaded_archive.txt'),
        '--retries', '10',
        '--fragment-retries', '10',
        '--retry-sleep', '5',
        '--ignore-errors',
        '--no-warnings',
        '--progress',
        '--console-title',
        channel_url
    ])

    log_message(f"   Command: yt-dlp --match-filter '{duration_filter}' --playlist-end {max_videos} ...")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        downloaded = 0
        skipped = 0
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                if '[download]' in line and 'Destination' in line:
                    filename = line.split('Destination:')[-1].strip()
                    log_message(f"   📥 {Path(filename).name[:60]}...")
                elif '[download] 100%' in line:
                    downloaded += 1
                    log_message(f"   ✅ Downloaded ({downloaded})")
                elif 'has already been recorded' in line or 'in archive' in line:
                    skipped += 1
                    if skipped <= 5 or skipped % 50 == 0:
                        log_message(f"   ⏭️ Already downloaded ({skipped} skipped)")
                elif 'Downloading video' in line or 'Downloading item' in line:
                    log_message(f"   🔄 {line}")
                elif 'ERROR' in line or ('error' in line.lower() and 'Got error' not in line):
                    log_message(f"   ⚠️ {line[:80]}", 'warning')
                elif 'Got error' in line:
                    if 'HTTP' in line or 'Connection' in line:
                        log_message(f"   🔄 Network error; retrying...", 'warning')

        process.wait()

        summary = f"{downloaded} downloaded"
        if skipped > 0:
            summary += f", {skipped} skipped (already archived)"

        if process.returncode == 0:
            log_message(f"✅ Completed! {summary} in {destination}/")
        else:
            log_message(f"⚠️ Completed with warnings. {summary}")

        return {'downloaded': downloaded, 'skipped': skipped, 'destination': str(dest_dir)}

    except Exception as e:
        log_message(f"❌ Error: {e}", 'error')
        raise


def run_download_youtube(params):
    "Run educational YouTube searches with yt-dlp."
    categories = params.get('categories', ['science'])
    videos_per_cat = params.get('videos_per_category', 5)

    ytdlp = get_ytdlp_path()

    downloaded = 0

    queries = {
        'science': ['science experiment french', 'chimie expérience', 'physique démonstration'],
        'nature': ['nature documentary french', 'animaux sauvages', 'forêt française'],
        'espace': ['espace documentaire', 'planètes système solaire', 'NASA français'],
        'geographie': ['tour eiffel visite', 'monuments france', 'villes france'],
        'histoire': ['histoire france documentaire', 'moyen age', 'révolution française']
    }

    for cat in categories:
        cat_queries = queries.get(cat, [cat])
        cat_dir = Path(config['download_dir']) / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        for query in cat_queries[:2]:
            log_message(f"📥 YouTube search: {query}")

            cmd = ytdlp.copy()
            cmd.extend([
                f'ytsearch{videos_per_cat}:{query}',
                '--max-filesize', '20M',
                '--max-downloads', str(videos_per_cat),
                '--match-filter', 'duration < 180',
                '-o', str(cat_dir / f'{cat}_%(title).50s_%(id)s.%(ext)s'),
                '--format', 'best[height<=480]',
                '--no-playlist',
                '--quiet',
                '--no-warnings'
            ])

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    downloaded += videos_per_cat
                    log_message(f"  ✅ Downloaded ~{videos_per_cat} videos")
                else:
                    log_message(f"  ⚠️ Warning: {result.stderr[:100]}", 'warning')
            except subprocess.TimeoutExpired:
                log_message(f"  ⏱️ Timeout for: {query}", 'warning')
            except Exception as e:
                log_message(f"  ❌ Error: {e}", 'error')

            time.sleep(2)

    return {'downloaded': downloaded}


def run_download_pexels(params):
    "Download videos from Pexels."
    import requests

    api_key = config.get('pexels_api_key')
    if not api_key or api_key == 'VOTRE_CLE_API_ICI':
        raise ValueError("Pexels API key not configured")

    categories = params.get('categories', ['science'])
    keywords = params.get('keywords', [])
    downloaded = 0

    for cat in categories:
        log_message(f"📥 Pexels - Category: {cat}")

        cat_keywords = keywords if keywords else [cat]
        cat_dir = Path(config['download_dir']) / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        for keyword in cat_keywords:
            log_message(f"  🔍 Search: {keyword}")

            try:
                url = "https://api.pexels.com/videos/search"
                headers = {"Authorization": api_key}
                params_req = {
                    "query": keyword,
                    "per_page": params.get('per_page', 3),
                    "size": "medium"
                }

                response = requests.get(url, headers=headers, params=params_req, timeout=10)
                response.raise_for_status()
                data = response.json()

                videos = data.get('videos', [])
                log_message(f"  → Found: {len(videos)} videos")

                for video in videos[:params.get('max_videos', 3)]:
                    video_files = video.get('video_files', [])
                    if video_files:
                        video_url = None
                        for vf in video_files:
                            if vf.get('quality') == 'hd' and vf.get('width', 0) <= 1280:
                                video_url = vf['link']
                                break
                        if not video_url:
                            video_url = video_files[0]['link']

                        video_id = video['id']
                        filename = f"{cat}_{keyword.replace(' ', '_')}_{video_id}.mp4"
                        filepath = cat_dir / filename

                        if not filepath.exists():
                            log_message(f"  📥 {filename}")
                            vid_response = requests.get(video_url, stream=True, timeout=60)
                            with open(filepath, 'wb') as f:
                                for chunk in vid_response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            downloaded += 1
                        else:
                            log_message(f"  ⏭️ Exists: {filename}")

                time.sleep(1)

            except Exception as e:
                log_message(f"  ❌ Error: {e}", 'error')

    return {'downloaded': downloaded}


def run_download_wikimedia(params):
    "Download videos from Wikimedia Commons."
    import requests

    keywords = params.get('keywords', ['nature', 'science'])
    downloaded = 0

    download_dir = Path(config['download_dir']) / 'wikimedia'
    download_dir.mkdir(parents=True, exist_ok=True)

    for keyword in keywords:
        log_message(f"📥 Wikimedia - Search: {keyword}")

        try:
            url = "https://commons.wikimedia.org/w/api.php"
            params_req = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': f'{keyword} filetype:video',
                'srnamespace': 6,
                'srlimit': params.get('limit', 3)
            }

            response = requests.get(url, params=params_req, timeout=10)
            data = response.json()

            results = data.get('query', {}).get('search', [])
            log_message(f"  → Found: {len(results)} results")

            for item in results:
                title = item['title'].replace('File:', '')
                if any(ext in title.lower() for ext in ['.webm', '.ogv', '.mp4']):
                    url_params = {
                        'action': 'query',
                        'format': 'json',
                        'titles': f'File:{title}',
                        'prop': 'imageinfo',
                        'iiprop': 'url'
                    }

                    url_response = requests.get(url, params=url_params, timeout=10)
                    url_data = url_response.json()

                    pages = url_data.get('query', {}).get('pages', {})
                    for page in pages.values():
                        imageinfo = page.get('imageinfo', [])
                        if imageinfo:
                            video_url = imageinfo[0].get('url')
                            if video_url:
                                filename = title.replace(' ', '_')[:80]
                                filepath = download_dir / filename

                                if not filepath.exists():
                                    log_message(f"  📥 {filename[:50]}...")
                                    vid_response = requests.get(video_url, stream=True, timeout=60)

                                    size = int(vid_response.headers.get('content-length', 0))
                                    if size > 50 * 1024 * 1024:
                                        log_message(f"    ⏭️ Too large ({size // 1024 // 1024}MB)")
                                        continue

                                    with open(filepath, 'wb') as f:
                                        for chunk in vid_response.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    downloaded += 1

                time.sleep(1.5)

        except Exception as e:
            log_message(f"  ❌ Error: {e}", 'error')

    return {'downloaded': downloaded}


def run_analyze(params):
    "Describe video frames with BLIP."
    log_message("🤖 Loading the BLIP model...")

    try:
        import torch
        from PIL import Image
        import cv2
        from transformers import BlipProcessor, BlipForConditionalGeneration

        device = "cuda" if torch.cuda.is_available() else "cpu"
        log_message(f"  Device: {device}")

        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        model.to(device)

        log_message("✅ Model loaded")

        source = params.get('source_dir', 'data')
        if source == 'downloaded':
            source_dir = DATA_DIR / 'downloaded'
        elif source == 'wikimedia':
            source_dir = DATA_DIR / 'wikimedia'
        else:
            source_dir = DATA_DIR

        extensions = ['.mp4', '.avi', '.wmv', '.webm', '.mkv']

        videos = []
        for ext in extensions:
            videos.extend(source_dir.glob(f"*{ext}"))
            videos.extend(source_dir.glob(f"**/*{ext}"))

        videos = list(set(videos))
        log_message(f"📹 {len(videos)} videos to analyze")

        analyzed = 0
        results = []

        for video_path in videos[:20]:
            log_message(f"  🎬 {video_path.name[:50]}")

            cap = cv2.VideoCapture(str(video_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
                ret, frame = cap.read()

                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    pil_image.thumbnail((384, 384), Image.Resampling.LANCZOS)

                    inputs = processor(pil_image, return_tensors="pt").to(device)
                    out = model.generate(**inputs, max_length=20)
                    caption = processor.decode(out[0], skip_special_tokens=True)

                    log_message(f"    → {caption}")
                    results.append({'file': video_path.name, 'caption': caption})
                    analyzed += 1

            cap.release()

        results_file = DATA_DIR / 'analysis_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return {'analyzed': analyzed, 'results_file': str(results_file)}

    except ImportError as e:
        raise ValueError(f"Missing dependencies: {e}. Install: pip install torch transformers pillow opencv-python")


def run_organize(params):
    "Copy videos into keyword categories."
    import shutil

    log_message("📁 Organizing videos...")

    organized_dir = Path(config['organized_dir'])
    organized_dir.mkdir(parents=True, exist_ok=True)

    categories = {
        'animaux': ['cat', 'dog', 'bird', 'animal', 'fish', 'horse', 'lion', 'elephant', 'whale', 'rabbit'],
        'nature': ['tree', 'forest', 'mountain', 'ocean', 'flower', 'waterfall', 'river', 'beach', 'sunset'],
        'espace': ['space', 'planet', 'moon', 'star', 'rocket', 'astronaut', 'galaxy', 'mars', 'saturn'],
        'science': ['experiment', 'microscope', 'chemistry', 'physics', 'laboratory', 'dna', 'cell'],
        'transport': ['car', 'train', 'plane', 'boat', 'ship', 'helicopter', 'bicycle', 'motorcycle'],
        'sports': ['soccer', 'football', 'basketball', 'swimming', 'running', 'tennis', 'golf'],
        'histoire': ['ancient', 'medieval', 'war', 'monument', 'castle', 'pyramid', 'museum'],
        'geographie': ['city', 'building', 'tower', 'bridge', 'landmark', 'eiffel', 'statue']
    }

    for cat in list(categories.keys()) + ['autre']:
        (organized_dir / cat).mkdir(exist_ok=True)

    extensions = ['.mp4', '.avi', '.wmv', '.webm', '.mkv', '.ogv']
    videos = []
    for ext in extensions:
        videos.extend(DATA_DIR.glob(f"*{ext}"))
        videos.extend((DATA_DIR / 'downloaded').glob(f"**/*{ext}"))
        videos.extend((DATA_DIR / 'wikimedia').glob(f"*{ext}"))

    videos = list(set(videos))
    organized = 0

    for video in videos:
        stem_lower = video.stem.lower()

        target_cat = 'autre'
        for cat, keywords in categories.items():
            if any(kw in stem_lower for kw in keywords):
                target_cat = cat
                break

        dest = organized_dir / target_cat / video.name
        if not dest.exists():
            shutil.copy2(video, dest)
            log_message(f"  {target_cat}: {video.name[:50]}")
            organized += 1

    log_message(f"✅ {organized} videos organized")
    return {'organized': organized}


def run_convert_to_wav(params):
    "Extract audio to WAV files with FFmpeg."
    folder = params.get('folder', '')
    output_mode = params.get('output_mode', 'subfolder')  # subfolder | same | custom
    output_custom = params.get('output_custom', '')
    sample_rate = params.get('sample_rate', 44100)
    channels = params.get('channels', 2)
    overwrite = params.get('overwrite', False)

    if not folder:
        raise ValueError("Source folder required")

    source_dir = Path(folder)
    if not source_dir.exists():
        raise ValueError(f"Folder not found: {folder}")

    if output_mode == 'subfolder':
        out_dir = source_dir / 'wav'
    elif output_mode == 'custom' and output_custom:
        out_dir = Path(output_custom)
    else:
        out_dir = source_dir

    out_dir.mkdir(parents=True, exist_ok=True)

    extensions = ['.mp4', '.webm', '.mkv', '.avi', '.ogv', '.mov', '.wmv', '.mpg',
                  '.mp3', '.m4a', '.ogg', '.flac', '.aac', '.opus']
    videos = []
    for ext in extensions:
        videos.extend(source_dir.glob(f'*{ext}'))

    if not videos:
        log_message(f"⚠️ No media files found in {source_dir.name}", 'warning')
        return {'converted': 0, 'skipped': 0, 'errors': 0}

    ch_label = 'Mono' if channels == 1 else 'Stereo'
    log_message(f"🎵 Conversion WAV: {len(videos)} files — {sample_rate}Hz {ch_label}")
    log_message(f"   Source : {source_dir}")
    log_message(f"   Output : {out_dir}")

    converted = skipped = errors = 0

    for i, video_path in enumerate(videos, 1):
        out_path = out_dir / (video_path.stem + '.wav')

        if out_path.exists() and not overwrite:
            log_message(f"   [{i}/{len(videos)}] ⏭️  {video_path.name}")
            skipped += 1
            continue

        log_message(f"   [{i}/{len(videos)}] 🔄 {video_path.name[:70]}...")

        flag = '-y' if overwrite else '-n'
        cmd = [
            'ffmpeg', flag,
            '-i', str(video_path),
            '-ar', str(sample_rate),
            '-ac', str(channels),
            '-acodec', 'pcm_s16le',
            str(out_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0 and out_path.exists():
                size_mb = out_path.stat().st_size / (1024 * 1024)
                log_message(f"      ✅ {out_path.name} ({size_mb:.1f} MB)")
                converted += 1
            else:
                err = (result.stderr or 'erreur inconnue')[-200:]
                log_message(f"      ❌ {err[:120]}", 'error')
                errors += 1
        except FileNotFoundError:
            log_message("❌ ffmpeg not found; add it to PATH", 'error')
            raise ValueError("ffmpeg not found on PATH")
        except subprocess.TimeoutExpired:
            log_message(f"      ⏱️  Timeout: {video_path.name}", 'error')
            errors += 1
        except Exception as e:
            log_message(f"      ❌ {e}", 'error')
            errors += 1

    log_message(f"✅ Completed — {converted} converted, {skipped} skipped, {errors} errors")
    return {'converted': converted, 'skipped': skipped, 'errors': errors,
            'output_dir': str(out_dir)}


def run_organize_media_library(params):
    "Run the optional MediaLibrary hierarchy export."
    log_message("📚 Organizing the MediaLibrary hierarchy...")

    script_path = SRC_DIR / 'organiser_media_library.py'
    if script_path.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, timeout=300,
                input='oui\n'
            )
            log_message(f"✅ MediaLibrary organization completed")
            return {'status': 'completed', 'output': result.stdout[-500:] if result.stdout else ''}
        except Exception as e:
            log_message(f"❌ Error: {e}", 'error')
            raise
    else:
        raise FileNotFoundError(f"Script not found: {script_path}")


# ============ FLASK ROUTES ============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/videos')
def videos_page():
    return render_template('videos.html')

@app.route('/api/stats')
def api_stats():
    return jsonify(get_video_stats())

@app.route('/api/queue')
def api_queue():
    return jsonify(get_queue_status())

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'Expected a JSON object.'}), 400
        key = data.get('pexels_api_key')
        if key is not None and not isinstance(key, str):
            return jsonify({'error': 'The API key must be text.'}), 400
        try:
            max_size = int(data.get('max_file_size_mb', config['max_file_size_mb']))
        except (TypeError, ValueError):
            return jsonify({'error': 'File size must be a positive integer.'}), 400
        if max_size <= 0:
            return jsonify({'error': 'File size must be a positive integer.'}), 400
        if key and key.strip():
            config['pexels_api_key'] = key.strip()
        config['max_file_size_mb'] = max_size
    public_config = {key: value for key, value in config.items() if key != 'pexels_api_key'}
    public_config['pexels_configured'] = bool(config['pexels_api_key'])
    if request.method == 'POST':
        return jsonify({'status': 'ok', 'config': public_config})
    return jsonify(public_config)

@app.route('/api/task', methods=['POST'])
def api_add_task():
    data = request.json
    task = {
        'id': datetime.now().strftime('%Y%m%d%H%M%S%f'),
        'type': data.get('type'),
        'name': data.get('name', data.get('type')),
        'params': data.get('params', {}),
        'status': 'queued',
        'created_at': datetime.now().isoformat()
    }
    task_queue.put(task)
    log_message(f"📋 Task added: {task['name']}")
    return jsonify({'status': 'ok', 'task': task})

@app.route('/api/videos')
def api_videos():
    "List local videos."
    videos = []
    extensions = ['.mp4', '.avi', '.wmv', '.webm', '.mkv', '.ogv']

    for ext in extensions:
        for video in DATA_DIR.glob(f"**/*{ext}"):
            try:
                videos.append({
                    'name': video.name,
                    'path': str(video.relative_to(DATA_DIR)),
                    'full_path': str(video),
                    'size_mb': round(video.stat().st_size / (1024 * 1024), 2),
                    'folder': video.parent.name
                })
            except:
                pass

    videos.sort(key=lambda x: (x['folder'], x['name']))
    return jsonify(videos[:200])

@app.route('/api/categories')
def api_categories():
    categories = {
        'download': ['science', 'nature', 'espace', 'animaux', 'geographie', 'transport', 'sports', 'histoire'],
        'organize': ['animaux', 'nature', 'espace', 'science', 'transport', 'sports', 'histoire', 'geographie', 'autre']
    }
    return jsonify(categories)

@app.route('/api/folders')
def api_folders():
    "List folders with video counts and sizes."
    folders = {}
    extensions = ['.mp4', '.avi', '.wmv', '.webm', '.mkv', '.ogv']

    for ext in extensions:
        for video in DATA_DIR.glob(f"**/*{ext}"):
            folder = video.parent.name
            if folder not in folders:
                folders[folder] = {'count': 0, 'size_mb': 0}
            folders[folder]['count'] += 1
            try:
                folders[folder]['size_mb'] += video.stat().st_size / (1024 * 1024)
            except:
                pass

    for f in folders:
        folders[f]['size_mb'] = round(folders[f]['size_mb'], 2)

    return jsonify(folders)

@app.route('/api/browse-file')
def api_browse_file():
    "Open a native file picker on the server machine."
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        filetypes = [
            ('Fichiers media', '*.mp4 *.mkv *.avi *.webm *.mov *.wmv *.mpg *.ogv *.mp3 *.wav *.m4a *.ogg *.flac *.aac *.opus'),
            ('Videos', '*.mp4 *.mkv *.avi *.webm *.mov *.wmv *.mpg *.ogv'),
            ('Audio', '*.mp3 *.wav *.m4a *.ogg *.flac *.aac *.opus'),
            ('All files', '*.*')
        ]
        file = filedialog.askopenfilename(title="Choisir un fichier media", filetypes=filetypes)
        root.destroy()
        if file:
            file = str(Path(file))
            return jsonify({'status': 'ok', 'file': file})
        return jsonify({'status': 'cancelled'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/browse-folder')
def api_browse_folder():
    "Open a native folder picker on the server machine."
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        folder = filedialog.askdirectory(title="Choisir un dossier")
        root.destroy()
        if folder:
            # Normalize Windows path separators
            folder = str(Path(folder))
            return jsonify({'status': 'ok', 'folder': folder})
        return jsonify({'status': 'cancelled'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/data-subfolders')
def api_data_subfolders():
    "List media folders under the configured data directory."
    extensions = ['.mp4', '.webm', '.mkv', '.avi', '.ogv', '.mov', '.wmv', '.mpg']
    folders = []
    if DATA_DIR.exists():
        for item in sorted(DATA_DIR.iterdir()):
            if item.is_dir():
                count = sum(1 for ext in extensions for _ in item.glob(f'*{ext}'))
                folders.append({'name': item.name, 'path': str(item), 'count': count})
    return jsonify(folders)


@app.route('/api/open-folder')
def api_open_folder():
    "Open the data directory in the native file explorer."
    import os
    try:
        os.startfile(str(DATA_DIR))
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/video/<path:filepath>')
def serve_video(filepath):
    "Serve a file from the private media directory."
    return send_from_directory(DATA_DIR, filepath)


# ============ WEBSOCKET ============

@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'ok'})
    emit('queue_update', get_queue_status())

@socketio.on('get_logs')
def handle_get_logs():
    log_file = LOGS_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-50:]
            for line in lines:
                emit('log', {'message': line.strip(), 'level': 'info'})


# ============ MAIN ============

if __name__ == '__main__':
    worker_thread = threading.Thread(target=task_worker, daemon=True)
    worker_thread.start()
    print("=" * 60)
    print("🎬 VIDEOTRANSFORMER - Web interface")
    print("=" * 60)
    print()
    print(f"📁 Folder data: {DATA_DIR}")
    print(f"📝 Logs: {LOGS_DIR}")
    print()
    print("🌐 Access: http://127.0.0.1:5000")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    def open_browser_when_ready():
        url = 'http://127.0.0.1:5000'
        for _ in range(60):
            try:
                with urllib.request.urlopen(url, timeout=1):
                    webbrowser.open(url)
                    return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.5)
        print("[!] Interface unavailable. Open http://127.0.0.1:5000 manually.")

    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)
