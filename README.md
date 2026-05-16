# 파일 검색 도구 (File Search)

macOS에서 파일 이름을 빠르게 검색할 수 있는 웹 기반 도구입니다.  
Windows의 **Everything**과 비슷하게, 전체 디스크를 미리 인덱싱해두고  
입력하는 즉시 결과를 보여줍니다.

![검색 화면](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.x-blue)

---

## 특징

- **빠른 검색** — SQLite 인덱스를 활용해 수천만 개 파일도 수십 ms 안에 검색
- **웹 UI** — 브라우저에서 `http://127.0.0.1:7070` 접속, 별도 앱 설치 불필요
- **자동 시작** — 맥이 켜지면 서버가 자동으로 실행됨 (LaunchAgent 등록)
- **자동 재인덱싱** — 인덱스가 24시간 이상 오래되면 백그라운드에서 자동 갱신
- **더블클릭으로 열기** — 검색 결과를 더블클릭하면 Finder에서 해당 파일 위치를 바로 열어줌
- **키보드 탐색** — ↑↓ 방향키로 결과 이동, Enter로 열기, Esc로 초기화

---

## 설치 방법

**Python 3가 필요합니다.** macOS Monterey(12) 이상은 기본으로 내장되어 있습니다.

터미널을 열고 아래 명령어를 붙여넣기 하세요:

```bash
git clone https://github.com/iscream2124/shworld && cd shworld && bash install.sh
```

설치 과정:
1. `~/.search/` 폴더에 서버 스크립트 저장
2. `~/.local/bin/` 에 인덱서 명령어(`search`) 설치
3. 전체 디스크 파일 인덱스 빌드 (**처음 한 번만, 수 분 소요**)
4. 맥 시작 시 자동 실행되도록 LaunchAgent 등록
5. 브라우저에서 `http://127.0.0.1:7070` 자동 오픈

---

## 사용 방법

### 웹 UI (브라우저)

```
http://127.0.0.1:7070
```

- 검색창에 파일 이름(또는 일부)을 입력하면 즉시 결과가 표시됩니다
- 결과를 **더블클릭**하면 Finder에서 해당 파일 위치를 열어줍니다
- 최대 500개 결과까지 표시 (앞쪽 일치 우선)

### 터미널 명령어

```bash
# 파일 이름으로 검색
search 키워드

# 파일만 검색 (디렉토리 제외)
search 키워드 --type f

# 디렉토리만 검색
search 키워드 --type d

# 인덱스 상태 확인 (파일 수, 마지막 스캔 시각)
search --stats

# 인덱스 수동 재빌드
search --rebuild
```

---

## 파일 구조

```
~/.search/
├── server.py     # 웹 서버 (http://127.0.0.1:7070)
├── index.db      # 파일 인덱스 (SQLite, 자동 생성)
└── server.log    # 서버 로그

~/.local/bin/
└── search        # 터미널 검색 명령어
```

---

## 자주 묻는 질문

**Q. 처음에 시간이 왜 이렇게 오래 걸리나요?**  
A. 전체 디스크(/)를 한 번 스캔해서 파일 목록을 만들기 때문입니다. 최초 1회만 기다리면 이후부터는 즉시 검색됩니다.

**Q. 맥을 재시작해도 자동으로 켜지나요?**  
A. 네, LaunchAgent에 등록되어 로그인 시 자동으로 서버가 실행됩니다.

**Q. 파일을 새로 추가했는데 검색이 안 돼요.**  
A. 인덱스는 24시간마다 자동으로 갱신됩니다. 바로 반영하려면 `search --rebuild`를 실행하세요.

**Q. 서버를 수동으로 끄고 싶어요.**  
```bash
launchctl unload ~/Library/LaunchAgents/com.user.filesearch.plist
```

**Q. 완전히 삭제하고 싶어요.**  
```bash
launchctl unload ~/Library/LaunchAgents/com.user.filesearch.plist
rm -rf ~/.search
rm ~/.local/bin/search
rm ~/Library/LaunchAgents/com.user.filesearch.plist
```

---

## 시스템 요구사항

- macOS (Monterey 12 이상 권장)
- Python 3.8 이상
