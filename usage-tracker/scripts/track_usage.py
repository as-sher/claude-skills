#!/usr/bin/env python3
"""
Claude Code usage tracker — Stop hook script.
Reads the session transcript, computes per-message + session + weekly stats, prints summary.
"""

import json
import sys
from pathlib import Path
from datetime import date, datetime, timedelta

WEEKLY_STORE      = Path.home() / ".claude" / "usage_weekly.json"
INPUT_COST_PER_M  = 3.00   # Sonnet 4.6 — edit to match your model
OUTPUT_COST_PER_M = 15.00


def read_transcript(path):
    """Parse JSONL transcript; return list of {input, output} dicts per assistant turn."""
    messages = []
    try:
        with open(path) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("type") == "assistant" and "message" in data:
                        u = data["message"].get("usage", {})
                        messages.append({
                            "input":  u.get("input_tokens", 0),
                            "output": u.get("output_tokens", 0),
                        })
                except Exception:
                    pass
    except Exception:
        pass
    return messages


def calc_cost(inp, out):
    return inp * INPUT_COST_PER_M / 1_000_000 + out * OUTPUT_COST_PER_M / 1_000_000


def fmt(n):
    """Compact token formatter: 1234 → 1.2K, 1500000 → 1.5M."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def week_monday():
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()


def load_weekly():
    try:
        data = json.loads(WEEKLY_STORE.read_text())
        if data.get("week_start") == week_monday():
            return data
    except Exception:
        pass
    return {"week_start": week_monday(), "sessions": {}}


def save_weekly(data):
    try:
        WEEKLY_STORE.parent.mkdir(parents=True, exist_ok=True)
        WEEKLY_STORE.write_text(json.dumps(data))
    except Exception:
        pass


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        return

    session_id      = payload.get("session_id", "unknown")
    transcript_path = payload.get("transcript_path", "")
    if not transcript_path:
        return

    messages = read_transcript(transcript_path)
    if not messages:
        return

    # Per-last-message stats
    last     = messages[-1]
    msg_in   = last["input"]
    msg_out  = last["output"]
    msg_cost = calc_cost(msg_in, msg_out)

    # Session totals — recomputed from full transcript each time (no drift)
    sess_in   = sum(m["input"]  for m in messages)
    sess_out  = sum(m["output"] for m in messages)
    sess_msgs = len(messages)
    sess_cost = calc_cost(sess_in, sess_out)

    # Weekly totals — store per-session so overwriting this session's entry is idempotent
    weekly = load_weekly()
    weekly["sessions"][session_id] = {
        "input":    sess_in,
        "output":   sess_out,
        "messages": sess_msgs,
        "updated":  datetime.now().isoformat(timespec="seconds"),
    }
    save_weekly(weekly)

    week_in   = sum(s["input"]    for s in weekly["sessions"].values())
    week_out  = sum(s["output"]   for s in weekly["sessions"].values())
    week_msgs = sum(s["messages"] for s in weekly["sessions"].values())
    week_cost = calc_cost(week_in, week_out)

    bar = "━" * 54
    print(f"\n{bar}")
    print(f"  {'This response:':<18} {fmt(msg_in):>5} in / {fmt(msg_out):<6} out            ${msg_cost:>6.3f}")
    print(f"  {'Session total:':<18} {fmt(sess_in):>5} in / {fmt(sess_out):<6} out  ({sess_msgs:>3} msgs)  ${sess_cost:>6.3f}")
    print(f"  {'This week:':<18} {fmt(week_in):>5} in / {fmt(week_out):<6} out  ({week_msgs:>3} msgs)  ${week_cost:>6.3f}")
    print(f"{bar}\n")


if __name__ == "__main__":
    main()
