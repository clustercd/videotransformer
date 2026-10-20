# VideoTransformer: usage examples

[Back to the README](../README.md)

## Convert a local clip

1. Install FFmpeg and start the dashboard using the README instructions.
2. Open `http://127.0.0.1:5000` on the same computer as the server.
3. Use the conversion controls to select a disposable test clip and choose an output format.
4. Submit the task and inspect its status and logs in the queue.
5. Check the output in a media player before using it downstream.

Native file pickers act on the server computer. Output locations depend on the
selected operation and settings; inspect them before processing a large batch.

## Download and organize a small collection

Start with one supported URL for media you own or have permission to use.
Submit the download, wait for completion, then inspect the local library.
Once that works, try a small batch. Source availability and download support can
change, so check task logs if a source rejects a request.

Optional BLIP analysis requires the additional dependencies described in the
README and may download model weights on first use. Preview the descriptions
before accepting file-name changes; frame captions can be inaccurate.

## Inspect the dashboard API

This standard-library example reads metadata only; it does not download or
modify media. Start the dashboard before running it.

```python
import json
from urllib.request import urlopen

base_url = "http://127.0.0.1:5000"
for endpoint in ("/api/stats", "/api/queue"):
    with urlopen(base_url + endpoint, timeout=10) as response:
        print(endpoint, json.dumps(json.load(response), indent=2))
```

API output and logs may contain local paths. Do not publish them without
review. See [privacy](PRIVACY.md) for local data and settings handling.
