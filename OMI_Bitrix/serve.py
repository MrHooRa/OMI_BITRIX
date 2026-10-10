"""Local/Windows WSGI entry point; no package downloads at runtime."""
import os
from waitress import serve
from app import app, start_background_sync

if __name__ == "__main__":
    if os.environ.get("OMI_AUTO_SYNC", "1") == "1":
        start_background_sync()
    serve(app, host=os.environ.get("HOST", "127.0.0.1"),
          port=int(os.environ.get("PORT", "5055")), threads=8,
          max_request_body_size=2 * 1024 * 1024)
