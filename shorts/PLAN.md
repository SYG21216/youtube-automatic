# 쇼츠 자동 업로드 루틴 - 작업 메모

## 방식
원본 영상 없이 생성: Claude가 대본 작성 → `make.py` (Pixabay 영상 + Google TTS 나레이션 + 자막, 1080x1920)
→ `upload.py` (비공개). 드라이브/whisper 단계는 폐기.

## 완료
- 채널: 봉투자취 (@봉투자취), 계정 bongtu.jachwi@gmail.com
- 환경 변수: YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN / PIXABAY_API_KEY / GOOGLE_TTS_KEY
- `make.py` → `upload.py` 비공개 테스트 성공 (2026-10-14, https://youtube.com/shorts/LXyIqUDYnXo - 삭제해도 됨)
- `upload.py --recent`: 최근 업로드 제목 (주제 중복 방지용)
- 매일 루틴 등록 (create_trigger, 새 세션 방식, 18시 전후 KST)

## 루틴 한 번 = 이렇게
1. `python3 shorts/upload.py --recent` 로 지난 주제 확인
2. 자취 꿀팁 주제 1개, 장면 4~6개, 총 25~45초 대본을 script.json으로 작성
   (query는 화면에 그대로 보일 구체적 영어 명사: "refrigerator", "light switch")
3. `python3 shorts/make.py script.json -o short.mp4`
4. yt-package 기준으로 제목 → `python3 shorts/upload.py short.mp4 --title ... --desc "...\n\n영상: Pixabay"`
