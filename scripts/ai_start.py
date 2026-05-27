"""AI work session starter.

Creates a new session ID, prompt template, and session metadata JSON.
Run from project root: `python scripts/ai_start.py`
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

GIT_USER_EMAIL = "tjrcksgnl@gmail.com"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKLOG_DIR = PROJECT_ROOT / ".ai-worklog"
PROMPTS_DIR = WORKLOG_DIR / "prompts"
SESSIONS_DIR = WORKLOG_DIR / "sessions"
DIFFS_DIR = WORKLOG_DIR / "diffs"
REPORTS_DIR = WORKLOG_DIR / "reports"

PROMPT_TEMPLATE = """# AI Work Session

## Session ID
{session_id}

## Title
{title}

## Git User
{git_user}

## Goal
작업 목표를 여기에 작성하세요.

## Prompt
Claude에게 입력한 프롬프트를 여기에 붙여넣으세요.

## Expected Files
- 예상 수정 파일을 작성하세요.

## Notes
- 참고사항을 작성하세요.
"""


def slugify(text: str) -> str:
    """Convert any title into a filesystem-safe slug."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    return text or "session"


def ensure_dirs() -> None:
    for d in (PROMPTS_DIR, SESSIONS_DIR, DIFFS_DIR, REPORTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def is_git_repo() -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except FileNotFoundError:
        return False


def has_uncommitted_changes() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def prompt_input(message: str) -> str:
    try:
        return input(message)
    except EOFError:
        return ""


def main() -> int:
    ensure_dirs()

    if is_git_repo():
        if has_uncommitted_changes():
            print("Warning: Uncommitted changes exist. AI diff might include them.")
            answer = prompt_input("Continue? (y/n): ").strip().lower()
            if answer not in ("y", "yes"):
                print("Aborted by user.")
                return 1
    else:
        print("Info: Not a git repository. Diff tracking will be unavailable until `git init` is run.")

    title = prompt_input("작업 제목(Title)을 입력하세요: ").strip()
    if not title:
        print("Error: 제목이 비어 있습니다. 다시 실행해 주세요.")
        return 1

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    slug = slugify(title)
    session_id = f"{timestamp}_{slug}"

    prompt_file = PROMPTS_DIR / f"{session_id}.md"
    session_file = SESSIONS_DIR / f"{session_id}.json"
    diff_file = DIFFS_DIR / f"{session_id}.diff"
    report_file = REPORTS_DIR / f"{session_id}.md"

    prompt_file.write_text(
        PROMPT_TEMPLATE.format(
            session_id=session_id,
            title=title,
            git_user=GIT_USER_EMAIL,
        ),
        encoding="utf-8",
    )

    metadata = {
        "session_id": session_id,
        "title": title,
        "git_user_email": GIT_USER_EMAIL,
        "created_at": now.isoformat(timespec="seconds"),
        "prompt_file": str(prompt_file.relative_to(PROJECT_ROOT).as_posix()),
        "diff_file": str(diff_file.relative_to(PROJECT_ROOT).as_posix()),
        "report_file": str(report_file.relative_to(PROJECT_ROOT).as_posix()),
        "status": "started",
    }
    session_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print(f"AI 작업 세션이 생성되었습니다.")
    print("=" * 60)
    print(f"Session ID  : {session_id}")
    print(f"Prompt file : {prompt_file}")
    print(f"Session JSON: {session_file}")
    print()
    print("다음 단계:")
    print(f"  1) {prompt_file.name} 파일에 Claude에게 보낼 프롬프트를 작성하세요.")
    print("  2) Claude CLI로 실제 코드 작업을 진행하세요.")
    print("  3) 작업이 끝나면 `python scripts/ai_finish.py`를 실행하세요.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n사용자가 취소했습니다.")
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"오류가 발생했습니다: {exc}")
        print("초보자 안내: 위 오류 메시지를 그대로 복사해서 검색하거나 도움을 요청하세요.")
        sys.exit(1)
