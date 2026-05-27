# stock_trading_project

한국 주식 시장 데이터를 수집/분석하기 위한 개인 프로젝트입니다.

## AI-assisted Development Log

This project uses an AI prompt-to-code tracking workflow.

AI work sessions are stored under `.ai-worklog/`.

Each session links:
- original prompt
- changed files
- git diff
- review report
- suggested commit message

자세한 사용법은 [`AI_WORKFLOW.md`](./AI_WORKFLOW.md)를 참고하세요.

### Quick start

```bash
python scripts/ai_start.py    # 세션 시작 + 프롬프트 파일 생성
# (생성된 프롬프트 파일 작성 → Claude CLI로 코드 작업)
python scripts/ai_finish.py   # diff 캡처 + 리포트 생성
python scripts/ai_commit.py   # 검토 후 commit
```
