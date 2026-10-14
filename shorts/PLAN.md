# 쇼츠 자동 업로드 루틴 - 작업 메모

## 완료
- 채널: 봉투자취 (@봉투자취), 계정 bongtu.jachwi@gmail.com
- 환경 변수 YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN 저장됨
- `shorts/upload.py` 로 비공개 테스트 업로드 성공 (2026-10-14, https://youtube.com/shorts/DuhTbzQ7mYg - 삭제해도 됨)
- 동의 화면용 페이지: docs/ (GitHub Pages, 브랜치 claude/sleepy-dirac-e49dax /docs)

## 남은 일
1. 사용자가 OAuth Playground에서 토큰 재발급 (scope: youtube + drive.readonly) 후 YT_REFRESH_TOKEN 교체
2. 드라이브 `쇼츠원본` 폴더에 원본 영상 업로드 (사용자)
3. 파이프라인: 드라이브에서 새 원본 다운로드 → 자막(whisper) → yt-shorts 로 구간 5개 선정
   → ffmpeg 9:16 컷 + 자막 → yt-package 로 제목 → upload.py (비공개) → 사용한 구간 기록
4. 매일 1회 루틴 등록 (create_trigger, 새 세션 방식). 원본이 바닥나면 업로드 건너뛰고 알림
