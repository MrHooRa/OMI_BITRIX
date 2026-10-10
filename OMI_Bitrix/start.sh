#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import flask, tzdata, waitress, sentence_transformers, sklearn, torch' >/dev/null 2>&1; then
  .venv/bin/python -m pip install --no-index --find-links wheelhouse -r requirements-lock.txt
fi
exec .venv/bin/python serve.py
