#!/usr/bin/env python3
"""8x agent capture hook for Claude Code.

Events: prompt (UserPromptSubmit), response (Stop), delegate (PreToolUse on Agent),
subagent (SubagentStop). Appends to .agent-logs/YYYY-MM-DD_HH-MM-SS_<session-id>.md.
"""
import glob, json, os, re, sys, time
from datetime import datetime, timezone

AUTHOR = "Deepjyoti-Sarmah"
TOOL = "claude-code"
PROJECT = "higgsfield-rebuild"
DEFAULT_MODEL = "claude-opus-5"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def read_transcript(path):
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return rows


def is_human_prompt(r):
    if r.get("type") != "user" or r.get("isSidechain") or r.get("isMeta"):
        return False
    c = (r.get("message") or {}).get("content")
    if isinstance(c, str):
        return True
    if isinstance(c, list):
        return not any(b.get("type") == "tool_result" for b in c if isinstance(b, dict))
    return False


def last_model(rows):
    for r in reversed(rows):
        m = (r.get("message") or {}).get("model")
        if r.get("type") == "assistant" and m and m != "<synthetic>":
            return m
    return DEFAULT_MODEL


def final_response(rows, include_sidechain=False):
    """Text the model emitted after its last tool call in the latest turn."""
    start = 0
    for i in range(len(rows) - 1, -1, -1):
        if is_human_prompt(rows[i]):
            start = i + 1
            break
    turn = [r for r in rows[start:] if r.get("type") == "assistant"
            and (include_sidechain or not r.get("isSidechain"))]
    tail, all_text = [], []
    for r in turn:
        for b in (r.get("message") or {}).get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                tail = []
            elif b.get("type") == "text" and b.get("text", "").strip():
                tail.append(b["text"])
                all_text.append(b["text"])
    # `tail` is empty both when the turn ended on a tool call and when the
    # closing text hasn't been flushed yet, so the fallback is returned
    # separately and only used once polling gives up.
    return "\n\n".join(tail), "\n\n".join(all_text[-1:]), last_model(turn or rows)


def poll_final_response(transcript, include_sidechain=False):
    text, fallback, model = "", "", DEFAULT_MODEL
    for _ in range(20):
        text, fallback, model = final_response(read_transcript(transcript), include_sidechain)
        if text:
            break
        time.sleep(0.25)
    return text, fallback, model


def log_path(log_dir, session_id):
    existing = sorted(glob.glob(os.path.join(log_dir, f"*_{session_id}.md")))
    if existing:
        return existing[0]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(log_dir, f"{stamp}_{session_id}.md")


def write_entry(path, session_id, kind, body, model, tool=TOOL):
    short = session_id[:8]
    ts = now_iso()
    content = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            content = f.read()
    m = re.match(r"^---\n.*?\n---\n", content, re.S)
    rest = content[m.end():] if m else ""
    if not rest:
        rest = (f"\n# Session Log - {ts[:10]}\n\n"
                f"Session: `{short}` | Project: `{PROJECT}` | Author: `{AUTHOR}`\n\n---\n")

    prompts = re.findall(r"\[LOG_ENTRY type=PROMPT num=(\d+) ", rest)
    num = max(len(prompts) + (1 if kind == "PROMPT" else 0), 1)
    rest += (f"\n[LOG_ENTRY type={kind} num={num} session={short}]\n"
             f"timestamp: {ts}\nmodel: {model}\n\n{body.rstrip()}\n\n")

    prompt_times = re.findall(r"\[LOG_ENTRY type=PROMPT num=\d+ [^\]]*\]\ntimestamp: (\S+)", rest)
    models = list(dict.fromkeys(re.findall(r"^model: (\S+)$", rest, re.M)))
    header = ("---\n"
              f"session_id: {session_id}\n"
              f"date: {(prompt_times[0] if prompt_times else ts)[:10]}\n"
              f"author: {AUTHOR}\n"
              f"model: {', '.join(models) or model}\n"
              f"tool: {tool}\n"
              f"project: {PROJECT}\n"
              f"total_exchanges: {len(prompt_times)}\n"
              f"first_prompt_time: {prompt_times[0] if prompt_times else ''}\n"
              f"last_prompt_time: {prompt_times[-1] if prompt_times else ''}\n"
              "---\n")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(header + rest)
    os.replace(tmp, path)


def capture_delegation(path, session_id, data):
    tool_input = data.get("tool_input") or {}
    body = (f"agent_type: {tool_input.get('subagent_type', 'general-purpose')}\n"
            f"description: {tool_input.get('description', '')}\n\n{tool_input.get('prompt', '')}")
    model = tool_input.get("model") or last_model(read_transcript(data.get("transcript_path", "")))
    write_entry(path, session_id, "DELEGATE", body, model)


def capture_subagent_output(path, session_id, data):
    text, fallback = "", ""
    agent_transcript = data.get("agent_transcript_path", "")
    model = last_model(read_transcript(agent_transcript)) if agent_transcript else DEFAULT_MODEL
    msg = data.get("last_assistant_message")
    if isinstance(msg, str) and msg.strip():
        text = msg
    elif agent_transcript:
        text, fallback, model = poll_final_response(agent_transcript, include_sidechain=True)
    body = f"agent_type: {data.get('agent_type', 'unknown')}\n\n{text or fallback or '(no text captured)'}"
    write_entry(path, session_id, "SUBAGENT_RESPONSE", body, model)


def capture_response(path, session_id, data):
    text, fallback, model = poll_final_response(data.get("transcript_path", ""))
    msg = data.get("last_assistant_message")
    if not text and isinstance(msg, str):
        text = msg
    write_entry(path, session_id, "RESPONSE", text or fallback or "(no text response captured)", model)


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    data = json.load(sys.stdin)
    session_id = data.get("session_id") or "unknown"
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    log_dir = os.environ.get("AGENT_LOG_DIR") or os.path.join(root, ".agent-logs")
    os.makedirs(log_dir, exist_ok=True)
    path = log_path(log_dir, session_id)

    if event == "prompt":
        model = last_model(read_transcript(data.get("transcript_path", "")))
        write_entry(path, session_id, "PROMPT", data.get("prompt", ""), model)
    elif event == "response":
        capture_response(path, session_id, data)
    elif event == "delegate":
        capture_delegation(path, session_id, data)
    elif event == "subagent":
        capture_subagent_output(path, session_id, data)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never break the agent loop
        print(f"capture hook error: {e}", file=sys.stderr)
    sys.exit(0)
