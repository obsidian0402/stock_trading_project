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

```powershell
# (1회) 프로젝트 루트에서 명령어를 어디서든 쓸 수 있게 PATH 등록
.\scripts\install_ai_path.ps1

# 세션 흐름
ai_start              # 세션 시작 + 프롬프트 파일 생성
# (프롬프트 파일 작성 → Claude CLI로 코드 작업)
ai_finish             # diff 캡처 + 리포트 생성
ai_commit             # 검토 후 git commit
```

PATH를 등록하지 않더라도 프로젝트 루트에서 `.\ai_start` 처럼 호출할 수 있습니다.
