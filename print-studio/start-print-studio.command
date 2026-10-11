#!/bin/zsh
# Double-click on a Mac to start the Print Studio. On other systems run: npm run dev
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v npm >/dev/null 2>&1; then
  echo 'Node.js 22.13 or later is needed to start the Print Studio. Install it from https://nodejs.org and try again.'
  read '?Press Return to close.'
  exit 1
fi
if [ ! -d node_modules ]; then
  echo 'Installing the application dependencies...'
  npm ci || exit 1
fi
python3 scripts/build_photos.py --if-missing
echo 'Open the Local address shown below. Keep this window open while using the Print Studio.'
npm run dev -- --host 127.0.0.1
