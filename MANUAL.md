# 대신봐드림 쇼츠 자동화 - 처음부터 따라 하는 설정 매뉴얼

롱폼 CC(크리에이티브 커먼즈) 영상을 1분 리뷰 쇼츠로 나눠 **매일 07:30 / 12:30 / 19:00에 3개씩 자동 업로드**하는 시스템을
처음부터 다시 만드는 방법입니다. 위에서부터 순서대로 하면 됩니다. (기준: 윈도우 PC + 크롬)

---

## 전체 그림

```
[매주 월요일] Claude 루틴이 받을 CC 영상 10개 + 다운로드 명령 한 줄을 알림으로 보냄
      ↓  (사람: 명령 한 줄 실행 → 받은 파일을 드라이브 '롱폼원본'에 끌어다 놓기, 3분)
[매일 3번] Claude 루틴이 자동으로:
   드라이브에서 원본 가져오기 → 자막 생성 → 하이라이트 장면 고르기 → 리뷰 나레이션(구글 TTS)
   → 세로 영상 제작(원본 장면 + 제목 + 자막 + 배경음악 + 1초 인트로) → 유튜브 예약 공개
```

| 구성 요소 | 하는 일 | 비용 |
|---|---|---|
| Claude Pro + Claude Code (웹) | 루틴 실행, 대본·장면 선택 | Pro 구독에 포함 |
| GitHub 저장소 `SYG21216/youtube-automatic` | 코드 보관 | 무료 |
| Google Cloud 프로젝트 | YouTube 업로드, 드라이브 읽기, TTS 음성 | 무료 한도 안 |
| Google 드라이브 | 원본 영상(`롱폼원본`), 배경음악(`쇼츠BGM`) | 무료 15GB |
| Pixabay API | (이전 방식용, 코드가 키를 요구함) | 무료 |

---

## 1단계. 구글 계정과 유튜브 채널

1. 채널용 구글 계정 준비 (지금: `bongtu.jachwi@gmail.com`)
2. **youtube.com** → 오른쪽 위 프로필 → **채널 만들기**
3. **studio.youtube.com** → 왼쪽 **맞춤설정**
   - **기본 정보**: 이름 `대신봐드림`, 설명 작성
   - **브랜딩**: 사진 = 저장소 `channel/profile.png`, 배너 = `channel/banner.png`
4. 휴대폰 인증: studio → **설정 → 채널 → 기능 사용 자격** → 중급 기능 사용(전화번호 인증). 15분 넘는 영상·맞춤 썸네일에 필요

---

## 2단계. 구글 클라우드 프로젝트 (API 키와 업로드 권한)

모두 **채널 계정(bongtu)으로 로그인한 상태**에서 합니다.

### 2-1. 프로젝트 만들기
1. **console.cloud.google.com** 접속
2. 위쪽 프로젝트 선택 상자 → **새 프로젝트** → 이름 `youtube-shorts` → 만들기
3. 위쪽에 `youtube-shorts`가 선택돼 있는지 확인

### 2-2. API 3개 켜기
왼쪽 메뉴 **API 및 서비스 → 라이브러리**에서 하나씩 검색 → **사용** 클릭
- `YouTube Data API v3`
- `Google Drive API`
- `Cloud Text-to-Speech API` ← 결제 계정 연결을 요구함 (2-3)

### 2-3. 결제 계정 + 요금 안전장치 (TTS용, 무료 한도 안에서만 씀)
1. 왼쪽 **결제** → 결제 계정 연결 (카드 등록 필요, 무료 한도 안에서는 0원)
2. **결제 → 예산 및 알림 → 예산 만들기**: 금액 `1,000원`, 알림 50% / 90% / 100%, 이메일 받기
   - 알림만 보내고 결제를 막지는 않음. 실제로 막는 건 코드의 안전장치(영상당 나레이션 700자 상한)
3. 참고: TTS 무료 한도는 월 100만 자. 하루 9개 × 700자 × 31일 ≈ 20만 자(20%)

### 2-4. TTS용 API 키
1. **API 및 서비스 → 사용자 인증 정보 → + 사용자 인증 정보 만들기 → API 키**
2. 만들어진 키 클릭 → **API 제한사항 → 키 제한 → Cloud Text-to-Speech API만 체크** → 저장
3. 키 값을 메모 → 나중에 `GOOGLE_TTS_KEY`

### 2-5. OAuth 동의 화면 (업로드·드라이브 권한용)
1. **API 및 서비스 → OAuth 동의 화면** (또는 Google 인증 플랫폼 → 브랜딩)
2. 사용자 유형 **외부** → 앱 이름 `shorts-uploader`, 지원 이메일 = 채널 계정
3. 앱 홈페이지 / 개인정보처리방침 링크: 저장소의 `docs/` 를 GitHub Pages로 공개한 주소
   (GitHub 저장소 → Settings → Pages → Branch `claude/youthful-sagan-nkebv4`, 폴더 `/docs` → Save)
4. **범위(Scopes)** 추가: `.../auth/youtube`, `.../auth/drive.readonly`
5. **대상(테스트 사용자)**에 채널 계정 이메일 추가
6. ⚠️ **게시 상태를 "프로덕션"으로**: "앱 게시" 버튼 클릭.
   **"테스트" 상태로 두면 7일마다 토큰이 만료되어 업로드가 멈춥니다.** 검증 안 된 앱 경고가 떠도 본인 계정은 사용 가능

### 2-6. OAuth 클라이언트
1. **사용자 인증 정보 → + 만들기 → OAuth 클라이언트 ID**
2. 유형 **웹 애플리케이션**, 승인된 리디렉션 URI: `https://developers.google.com/oauthplayground`
3. 만들어진 **클라이언트 ID**, **클라이언트 보안 비밀번호** 메모 → `YT_CLIENT_ID`, `YT_CLIENT_SECRET`

### 2-7. 리프레시 토큰 발급 (OAuth Playground)
1. **developers.google.com/oauthplayground** 접속
2. 오른쪽 위 **톱니바퀴** → `Use your own OAuth credentials` 체크 → 2-6의 ID / 비밀번호 입력
3. 왼쪽 아래 입력칸에 아래 두 줄을 공백으로 이어 넣고 **Authorize APIs**
   ```
   https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/drive.readonly
   ```
4. **채널 계정**으로 로그인 → "확인되지 않은 앱" 경고가 나오면 **고급 → (안전하지 않음)으로 이동** → 허용
5. **Exchange authorization code for tokens** → 나온 **Refresh token** 메모 → `YT_REFRESH_TOKEN`

---

## 3단계. Pixabay API 키
1. **pixabay.com** 가입 → **pixabay.com/api/docs** 접속 → 페이지 안의 `key` 값 메모 → `PIXABAY_API_KEY`

---

## 4단계. 구글 드라이브 폴더 2개 (채널 계정 드라이브)

1. **drive.google.com** (오른쪽 위 프로필이 채널 계정인지 확인)
2. **+ 새로 만들기 → 새 폴더** 로 두 개 만들기
   - `쇼츠BGM` : 배경음악 mp3
   - `롱폼원본` : 리뷰할 원본 영상
3. 배경음악 채우기: **studio.youtube.com → 왼쪽 오디오 보관함** → 필터 **"저작자 표시 필요 없음"** →
   밝은 곡 위주로 다운로드 → `쇼츠BGM` 에 업로드 (가사 없는 곡 권장)

---

## 5단계. Claude Code 클라우드 환경

1. **claude.ai/code** 접속 (Pro 구독)
2. GitHub 연결 후 저장소 `SYG21216/youtube-automatic` 선택
3. 세션 화면 위쪽 **환경(구름 아이콘) → Edit**
4. **Environment variables** 에 5개 입력 (값은 2~3단계에서 메모한 것)
   ```
   YT_CLIENT_ID=...
   YT_CLIENT_SECRET=...
   YT_REFRESH_TOKEN=...
   GOOGLE_TTS_KEY=...
   PIXABAY_API_KEY=...
   ```
5. **Network access → Allowed domains** 에 아래 추가 ("Allow package managers"는 체크 유지)
   ```
   googleapis.com
   *.googleapis.com
   pixabay.com
   *.pixabay.com
   raw.githubusercontent.com
   youtube.com
   *.youtube.com
   *.googlevideo.com
   *.ytimg.com
   huggingface.co
   *.huggingface.co
   *.hf.co
   ```
   (자세한 화면 설명: https://code.claude.com/docs/en/cloud-environments#network-access)
6. 저장

---

## 6단계. 동작 확인 (Claude에게 시키기)

claude.ai/code 에서 새 세션을 열고 아래를 그대로 붙여 넣습니다.
```
SYG21216/youtube-automatic 의 claude/youthful-sagan-nkebv4 브랜치에서
1) python3 shorts/upload.py --recent 가 되는지
2) python3 shorts/source.py list 가 되는지
3) python3 shorts/source.py suggest 가 되는지
확인하고 결과를 알려줘.
```
에러가 나면 맨 아래 **문제 해결** 표를 보세요.

---

## 7단계. 루틴 2개 만들기 (Claude에게 시키기)

새 세션에서 아래를 붙여 넣으면 Claude가 루틴을 만듭니다.

### 7-1. 쇼츠 제작 루틴 (매일 3번)
```
루틴을 만들어줘. 이름 "대신봐드림 쇼츠", 매일 한국시간 06:40, 11:40, 17:40 (cron: CRON_TZ=Asia/Seoul 40 6,11,17 * * *),
실행할 때마다 새 세션, 끝나면 휴대폰 알림. 루틴 프롬프트는 아래 그대로:

대신봐드림 유튜브 채널에 롱폼 CC 영상 리뷰 쇼츠 3개를 만들어 예약 공개로 업로드해줘.
0. 공개 시각: `TZ=Asia/Seoul date` 로 지금 한국 시간을 보고 07:30 / 12:30 / 19:00 중 지금 이후 가장 가까운 시각을 PUBLISH_AT 으로 (예: 2026-10-15T07:30:00+09:00). 3개 모두 같은 시각.
1. 저장소 SYG21216/youtube-automatic 이 작업 폴더에 없으면 add_repo(owner SYG21216, repo youtube-automatic)로 추가해 clone. 그 안에서 `git fetch origin claude/youthful-sagan-nkebv4 && git checkout claude/youthful-sagan-nkebv4` 후 shorts/PLAN.md 를 읽고 "루틴 한 번" 절차를 그대로 따른다.
2. 쇼츠 3개를 만든다. 원본 하나에서 서로 다른 장면으로 여러 개 만들어도 되고(원본당 최대 3개), 원본이 모자라면 만들 수 있는 만큼만.
   - license 가 creativeCommon 이 아니거나 업로더가 저작권자로 보이지 않는 원본은 쓰지 않는다.
   - 각 쇼츠: script 작성 → make.py → upload.py --publish-at PUBLISH_AT (설명란에 원본 youtu.be 링크·채널명·CC BY 표기 필수).
   - 한 개가 실패해도 나머지는 계속.
3. 쓸 원본이 하나도 없으면 아무것도 올리지 말고 "롱폼원본 폴더에 새 영상이 필요해요" 한 줄만 보고.
4. 공개 예정 시각과 업로드된 URL·제목·사용한 원본을 개당 한 줄로 보고. 실패나 경고가 있으면 원인 한 줄. 커밋/푸시는 하지 않는다.
```

### 7-2. 주간 원본 추천 루틴 (매주 월요일)
```
루틴을 만들어줘. 이름 "대신봐드림 주간 원본 추천", 매주 월요일 한국시간 08:47 (cron: CRON_TZ=Asia/Seoul 47 8 * * 1),
실행할 때마다 새 세션, 끝나면 휴대폰 알림. 루틴 프롬프트는 아래 그대로:

대신봐드림 유튜브 채널(롱폼 CC 영상을 1분 리뷰 쇼츠로 만드는 채널)을 위해, 이번 주에 사용자가 받아서 드라이브에 넣을 원본 영상 10개를 추천해줘. 채널 주인이 직접 요청한 작업이고, 아래 저장소 스크립트 실행(읽기 전용 조회)을 허용했어.
1. 저장소 SYG21216/youtube-automatic 이 없으면 add_repo 또는 git clone 한 뒤 `git fetch origin claude/youthful-sagan-nkebv4 && git checkout claude/youthful-sagan-nkebv4`. shorts/PLAN.md 를 읽는다.
2. `cd shorts && python3 source.py suggest` 를 실행한다 (CC 후보 조회만, 업로드·수정 없음).
3. 3분 이상 롱폼, 업로더가 실제 저작권자(공식 소속사·방송사·본인 채널)인 것만. 재업로드·아카이브 편집 다큐·치이카와·치어리더·룩북 제외. K-POP·연예 위주로 섞어 10개.
4. 형식: `1. [분야] 제목 - 채널 (길이, 조회수) https://youtu.be/ID` 10줄, 그다음 한 줄 다운로드 명령
   `yt-dlp -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]" --write-subs --sub-langs ko --convert-subs srt -P "%USERPROFILE%\Downloads\롱폼원본" <링크들>`
   마지막 줄: "받은 파일을 bongtu 드라이브 '롱폼원본' 폴더에 넣어 주세요."
코드 수정·커밋·업로드는 하지 않는다.
```

루틴 목록 확인·끄기·켜기: claude.ai/code → 왼쪽 **Routines**

---

## 8단계. 매주 할 일 (사람, 약 3분)

### 처음 한 번: 다운로드 프로그램 설치
1. **윈도우 키** → `cmd` → **명령 프롬프트**
2. `winget install yt-dlp` 입력 → 엔터 (물으면 `Y`). ffmpeg도 같이 설치됨
3. 창을 닫고 다시 열기

### 매주 월요일
1. 알림으로 온 **다운로드 명령 한 줄**을 명령 프롬프트에 붙여넣고 엔터
2. **파일 탐색기 → 다운로드 → 롱폼원본** 폴더의 파일(.mp4, .srt)을 전부 선택
3. 드라이브 **`롱폼원본`** 폴더 화면으로 끌어다 놓기. **파일 이름은 바꾸지 않기** (끝의 `[영문숫자]`로 원본을 찾음)
4. 다 쓴 원본은 드라이브에서 지워도 됨 (`source.py list` 에서 `done` 표시)

---

## 9단계. 알아둘 규칙과 한도

| 항목 | 내용 |
|---|---|
| 저작권 | 업로더 본인이 CC로 올린 영상만. 설명란에 원작자·링크·CC BY 자동 표기. 원본 소리는 빼고(음원 신고 방지) 나레이션 + 배경음악만 |
| 쓰지 않는 영상 | 영화·드라마·음방·뮤비 재업로드, 치이카와, 치어리더, 룩북 |
| YouTube 업로드 | 하루 100개 한도 (지금 9개) |
| Claude Pro 루틴 | 하루 5회 실행 한도 (지금 3회 + 월요일 1회). 수동 실행도 횟수에 포함 |
| 구글 TTS | 월 100만 자 무료. 영상당 700자 넘으면 코드가 거부 |
| 클라우드 → YouTube 직접 다운로드 | 봇 차단으로 불가. 그래서 사람이 받아서 드라이브에 넣는 구조 |

---

## 문제 해결

| 증상 / 알림 내용 | 원인 | 해결 |
|---|---|---|
| `invalid_grant` / 토큰 오류 | 리프레시 토큰 만료 (동의 화면이 "테스트" 상태면 7일) | 2-5 ⑥ 프로덕션 게시 → 2-7 다시 발급 → 5단계 `YT_REFRESH_TOKEN` 교체 |
| "롱폼원본 폴더에 새 영상이 필요해요" | 원본을 다 씀 | 8단계 |
| `youtube id not found - skip` | 파일 이름이 바뀌어 원본을 못 찾음 | 파일 이름에 `[유튜브ID]` 붙이기 |
| 자막 생성 실패 | `*.hf.co` 네트워크 미허용 | 5단계 ⑤ 확인 (자막 없이도 장면만 보고 진행은 됨) |
| `quotaExceeded` | YouTube 하루 한도 초과 | 다음 날 자동 회복 |
| 배경음악 없음 경고 | `쇼츠BGM` 폴더가 비었거나 이름이 다름 | 4단계 |
| 루틴이 안 돎 | Pro 하루 5회 한도 / 루틴 꺼짐 | claude.ai/code → Routines 에서 상태 확인 |
| 403 / 연결 거부 | 네트워크 허용 목록 누락 | 5단계 ⑤ 에 해당 주소 추가 |

---

## 저장소 파일 지도

| 파일 | 역할 |
|---|---|
| `shorts/PLAN.md` | 루틴이 매번 읽는 작업 지침 (대본 규칙, 설명란 형식) |
| `shorts/source.py` | 드라이브 원본 목록·가져오기, 라이선스 확인, 자막 생성, 장면 시트, 주간 추천 후보 |
| `shorts/make.py` | 쇼츠 제작 (원본 장면 + TTS + 자막 + BGM + 인트로) |
| `shorts/upload.py` | 유튜브 업로드·예약 공개, 최근 업로드 조회, 드라이브 접근 |
| `shorts/intro.mp4` | 1초 인트로 |
| `channel/brand.py` | 프로필·배너·인트로 다시 만들기 (`python3 channel/brand.py`) |
| `docs/` | OAuth 동의 화면용 홈페이지·개인정보처리방침 |
