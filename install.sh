#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "File Search 설치 중..."

# 1. 디렉토리 생성
mkdir -p ~/.search ~/.local/bin ~/Library/LaunchAgents

# 2. 스크립트 복사
cp "$SCRIPT_DIR/server.py" ~/.search/server.py
cp "$SCRIPT_DIR/search"    ~/.local/bin/search
chmod +x ~/.local/bin/search

# 3. LaunchAgent plist 생성 (경로를 현재 사용자 홈에 맞게 동적 생성)
cat > ~/Library/LaunchAgents/com.user.filesearch.plist << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.filesearch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$HOME/.search/server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/.search/server.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/.search/server.log</string>
</dict>
</plist>
PLIST

# 4. 초기 파일 인덱스 빌드 (전체 디스크 스캔 — 수 분 소요)
echo "파일 인덱스 빌드 중... (처음에는 몇 분 걸릴 수 있어요)"
python3 ~/.local/bin/search --rebuild

# 5. 서버 자동 시작 등록
launchctl unload ~/Library/LaunchAgents/com.user.filesearch.plist 2>/dev/null || true
launchctl load  ~/Library/LaunchAgents/com.user.filesearch.plist

echo ""
echo "설치 완료!"
echo "→ http://127.0.0.1:7070"
open http://127.0.0.1:7070
