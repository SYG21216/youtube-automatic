# 쇼츠 자동 업로드 루틴 - 작업 메모

## 방식
원본 영상 없이 생성: Claude가 대본 작성 → `make.py` (Pixabay 영상 + Google TTS 나레이션 + 자막, 1080x1920)
→ `upload.py` (공개). 드라이브/whisper 단계는 폐기.

## 완료
- 채널: 봉투자취 (@봉투자취), 계정 bongtu.jachwi@gmail.com
- 환경 변수: YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN / PIXABAY_API_KEY / GOOGLE_TTS_KEY
- `make.py` → `upload.py` 비공개 테스트 성공 (2026-10-14, 테스트 영상 LXyIqUDYnXo, rqRmqOLb_xQ 삭제해도 됨)
- `upload.py --recent`: 최근 업로드 제목 (주제 중복 방지용)
- 루틴: 매일 10:57, 18:57 KST × 3개씩 = 하루 6개 (create_trigger 새 세션 방식)

## 루틴 한 번 = 이렇게
1. `python3 shorts/upload.py --recent` 로 지난 주제 확인
2. 자취 꿀팁 주제 1개로 script.json 작성. 타깃: 자취 막 시작한 20-30대, 공과금·생활비 걱정
   - `title`: 상단 고정 제목 2줄 (`\n`), 핵심어는 `*별표*` → 노란색. 예: "자취 1년차가 알려주는\n*전기세 반값* 만드는 법"
   - `scenes` 4~6개, 총 25~45초. `say`는 반말/친근한 구어체, 짧은 문장, 숫자·핵심어는 `*별표*`
   - 첫 장면 = 훅 (손해·돈 얘기로 바로 시작). 마지막 장면 = 저장/팔로우 유도 한 줄
   - `query`는 화면에 그대로 보일 구체적 영어 명사 1~3단어: "refrigerator", "light switch", "young woman phone"
   - 스타일: Pretendard 팝 자막 + 노란 강조, 2.5초 컷 전환, Chirp3-HD 음성 (make.py가 처리)
3. `python3 shorts/make.py script.json -o short.mp4`
4. yt-package 기준으로 제목 정하고 설명란 작성 → `python3 shorts/upload.py short.mp4 --title ... --desc ... --privacy public`
   설명란 형식 (upload.py가 해시태그 3개 미만이면 거부, 해시태그는 태그로도 등록됨):
   ```
   한 줄 요약 (이 영상 보면 뭘 얻는지)

   ✅ 핵심 1 (숫자/구체어)
   ✅ 핵심 2
   ✅ 핵심 3

   저장해두고 공과금 나올 때 꺼내보세요!

   #자취 #자취꿀팁 #자취생 #혼자살기 #사회초년생 #주제태그1 #주제태그2 #생활꿀팁 #shorts
   영상: Pixabay
   ```

## 배경음악
bongtu 드라이브 `쇼츠BGM` 폴더(YouTube 오디오 보관함, 저작자 표시 불필요 곡)에서 영상마다 1곡 랜덤으로 받아
인트로 25초 건너뛰고 목소리 아래(-13dB 정도)로 깔음. 곡 추가/삭제는 드라이브 폴더에서 하면 됨.
`shorts/bgm/*.mp3`가 있으면 그게 우선. 드라이브 실패 시 음악 없이 경고만 하고 진행.
