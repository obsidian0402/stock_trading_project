"""Record goal/prompt into the latest session's prompt .md file.

Usage:
  python scripts/ai_record.py --goal "..." --prompt "..."
  python scripts/ai_record.py --goal-file goal.txt --prompt-file prompt.txt
  python scripts/ai_record.py --from-stdin   # 아래 형식으로 stdin 입력
      [목표]
      ...여러 줄...
      [프롬프트]
      ...여러 줄...

옵션:
  --session SESSION_ID   특정 세션을 대상으로 (기본: 가장 최근 세션)
  --append               기존 내용을 지우지 않고 뒤에 이어붙임
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Windows 콘솔에서도 한글이 깨지지 않도록 표준 입출력 UTF-8로 강제
for _stream_name in ("stdin", "stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKLOG_DIR = PROJECT_ROOT / ".ai-worklog"
SESSIONS_DIR = WORKLOG_DIR / "sessions"
PROMPTS_DIR = WORKLOG_DIR / "prompts"


def find_latest_session() -> Path | None:
    if not SESSIONS_DIR.exists():
        return None
    candidates = sorted(SESSIONS_DIR.glob("*.json"))
    return candidates[-1] if candidates else None


def find_session(session_id: str | None) -> Path | None:
    if session_id:
        path = SESSIONS_DIR / f"{session_id}.json"
        return path if path.exists() else None
    return find_latest_session()


def parse_stdin_blocks(text: str) -> tuple[str, str]:
    """Parse `[목표] ... [프롬프트] ...` blocks from a stdin payload."""
    goal_match = re.search(r"\[목표\]\s*\n?(.*?)(?=\[프롬프트\]|\Z)", text, re.DOTALL)
    prompt_match = re.search(r"\[프롬프트\]\s*\n?(.*)", text, re.DOTALL)
    goal = goal_match.group(1).strip() if goal_match else ""
    prompt = prompt_match.group(1).strip() if prompt_match else ""
    return goal, prompt


def replace_section(md_text: str, section_title: str, new_content: str, append: bool) -> str:
    """Replace (or append to) the body of `## {section_title}` in a markdown file."""
    pattern = re.compile(
        rf"(##\s+{re.escape(section_title)}\s*\n)(.*?)(?=\n##\s|\Z)",
        re.DOTALL,
    )
    match = pattern.search(md_text)
    new_body = new_content.rstrip() + "\n"
    if match:
        if append:
            existing = match.group(2).rstrip()
            combined = f"{existing}\n\n{new_content.rstrip()}\n" if existing else new_body
            return md_text[: match.start(2)] + combined + md_text[match.end(2):]
        return md_text[: match.start(2)] + new_body + md_text[match.end(2):]
    return md_text.rstrip() + f"\n\n## {section_title}\n{new_body}"


def read_optional_file(path: str | None) -> str | None:
    if not path:
        return None
    return Path(path).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Record goal/prompt into the latest session prompt file.")
    parser.add_argument("--goal", help="작업 목표 문자열")
    parser.add_argument("--prompt", help="Claude 프롬프트 문자열")
    parser.add_argument("--goal-file", help="목표를 담은 파일")
    parser.add_argument("--prompt-file", help="프롬프트를 담은 파일")
    parser.add_argument("--from-stdin", action="store_true", help="stdin에서 [목표]/[프롬프트] 블록 파싱")
    parser.add_argument("--session", help="대상 세션 ID (기본: 가장 최근)")
    parser.add_argument("--append", action="store_true", help="섹션 내용 덮어쓰지 않고 이어붙이기")
    args = parser.parse_args()

    session_file = find_session(args.session)
    if session_file is None:
        print("Error: 세션을 찾을 수 없습니다. 먼저 `python scripts/ai_start.py`를 실행하세요.")
        return 1

    metadata = json.loads(session_file.read_text(encoding="utf-8"))
    session_id = metadata["session_id"]
    prompt_md = PROMPTS_DIR / f"{session_id}.md"
    if not prompt_md.exists():
        print(f"Error: 프롬프트 파일이 없습니다: {prompt_md}")
        return 1

    goal = args.goal
    prompt = args.prompt

    if args.from_stdin:
        stdin_text = sys.stdin.read()
        s_goal, s_prompt = parse_stdin_blocks(stdin_text)
        goal = goal or s_goal or None
        prompt = prompt or s_prompt or None

    file_goal = read_optional_file(args.goal_file)
    file_prompt = read_optional_file(args.prompt_file)
    if file_goal is not None:
        goal = file_goal
    if file_prompt is not None:
        prompt = file_prompt

    if not goal and not prompt:
        print("Error: --goal/--prompt, --goal-file/--prompt-file, --from-stdin 중 하나는 필요합니다.")
        return 1

    md_text = prompt_md.read_text(encoding="utf-8")
    if goal:
        md_text = replace_section(md_text, "Goal", goal, append=args.append)
    if prompt:
        md_text = replace_section(md_text, "Prompt", prompt, append=args.append)
    prompt_md.write_text(md_text, encoding="utf-8")

    metadata["status"] = "prompt_recorded"
    session_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Recorded into: {prompt_md}")
    if goal:
        first_line = goal.splitlines()[0][:60]
        print(f"  Goal   : {first_line}{'...' if len(goal) > 60 else ''}")
    if prompt:
        first_line = prompt.splitlines()[0][:60]
        print(f"  Prompt : {first_line}{'...' if len(prompt) > 60 else ''}")
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
