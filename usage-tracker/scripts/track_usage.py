#!/usr/bin/env python3
"""
Claude Code usage tracker — Stop hook script.
Reads the session transcript, computes per-message + session + weekly stats, prints summary.
Also fetches live plan-limit utilisation from the Anthropic API via the CLI OAuth token.
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import date, datetime, timedelta, timezone

WEEKLY_STORE            = Path.home() / ".claude" / "usage_weekly.json"
CONFIG_FILE             = Path.home() / ".claude" / "usage_config.json"
INPUT_COST_PER_M        = 3.00   # Sonnet 4.6 regular input
CACHE_WRITE_COST_PER_M  = 3.75   # Sonnet 4.6 cache creation
CACHE_READ_COST_PER_M   = 0.30   # Sonnet 4.6 cache read (10x cheaper)
OUTPUT_COST_PER_M       = 15.00


def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}


def progress_bar(used, total, width=20):
    pct = min(used / total, 1.0)
    filled = int(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    return bar, pct


def read_transcript(path):
    """Parse JSONL transcript; return list of {input, output} dicts per assistant turn."""
    messages = []
    try:
        with open(path) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get("message", {})
                    if msg.get("role") == "assistant":
                        u = msg.get("usage", {})
                        messages.append({
                            "input":       u.get("input_tokens", 0),
                            "cache_write": u.get("cache_creation_input_tokens", 0),
                            "cache_read":  u.get("cache_read_input_tokens", 0),
                            "output":      u.get("output_tokens", 0),
                        })
                except Exception:
                    pass
    except Exception:
        pass
    return messages


def calc_cost(inp, cache_write, cache_read, out):
    return (
        inp        * INPUT_COST_PER_M       / 1_000_000
        + cache_write * CACHE_WRITE_COST_PER_M / 1_000_000
        + cache_read  * CACHE_READ_COST_PER_M  / 1_000_000
        + out      * OUTPUT_COST_PER_M      / 1_000_000
    )


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


def get_oauth_token():
    """Read the Claude Code OAuth access token from the macOS Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password",
             "-s", "Claude Code-credentials",
             "-a", os.environ.get("USER", ""),
             "-w"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            creds = json.loads(result.stdout.strip())
            return creds.get("claudeAiOauth", {}).get("accessToken")
    except Exception:
        pass
    return None


def fetch_plan_utilization(token):
    """
    Fire a minimal 1-token Haiku message and read the rate-limit headers.
    Returns dict with session_pct, weekly_pct, session_reset, weekly_reset
    or None if the request fails.

    This mirrors how Claude Usage Tracker fetches plan-limit data when only
    a CLI OAuth token is available — the dedicated oauth/usage endpoint is
    disabled, so a throwaway API call is the only way to get these headers.
    """
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "hi"}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload, method="POST",
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("anthropic-beta", "oauth-2025-04-20")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            h = resp.headers
            return {
                "session_pct":   float(h.get("anthropic-ratelimit-unified-5h-utilization", 0)) * 100,
                "weekly_pct":    float(h.get("anthropic-ratelimit-unified-7d-utilization", 0)) * 100,
                "session_reset": int(h.get("anthropic-ratelimit-unified-5h-reset", 0)),
                "weekly_reset":  int(h.get("anthropic-ratelimit-unified-7d-reset", 0)),
            }
    except Exception:
        return None


def fmt_reset(ts):
    """Format a Unix timestamp as a human-readable reset time in local time."""
    if not ts:
        return ""
    dt = datetime.fromtimestamp(ts)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("today %H:%M")
    if dt.date() == (now + timedelta(days=1)).date():
        return dt.strftime("tomorrow %H:%M")
    return dt.strftime("%a %H:%M")


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
    last          = messages[-1]
    msg_in        = last["input"]
    msg_cw        = last["cache_write"]
    msg_cr        = last["cache_read"]
    msg_out       = last["output"]
    msg_total_in  = msg_in + msg_cw + msg_cr
    msg_cost      = calc_cost(msg_in, msg_cw, msg_cr, msg_out)

    # Session totals — recomputed from full transcript each time (no drift)
    sess_in   = sum(m["input"]       for m in messages)
    sess_cw   = sum(m["cache_write"] for m in messages)
    sess_cr   = sum(m["cache_read"]  for m in messages)
    sess_out  = sum(m["output"]      for m in messages)
    sess_msgs = len(messages)
    sess_cost = calc_cost(sess_in, sess_cw, sess_cr, sess_out)
    sess_total_in = sess_in + sess_cw + sess_cr

    # Weekly totals — store per-session so overwriting this session's entry is idempotent
    weekly = load_weekly()
    weekly["sessions"][session_id] = {
        "input":       sess_in,
        "cache_write": sess_cw,
        "cache_read":  sess_cr,
        "output":      sess_out,
        "messages":    sess_msgs,
        "updated":     datetime.now().isoformat(timespec="seconds"),
    }
    save_weekly(weekly)

    week_in   = sum(s["input"]                  for s in weekly["sessions"].values())
    week_cw   = sum(s.get("cache_write", 0)     for s in weekly["sessions"].values())
    week_cr   = sum(s.get("cache_read", 0)      for s in weekly["sessions"].values())
    week_out  = sum(s["output"]                 for s in weekly["sessions"].values())
    week_msgs = sum(s["messages"]               for s in weekly["sessions"].values())
    week_cost = calc_cost(week_in, week_cw, week_cr, week_out)
    week_total_in = week_in + week_cw + week_cr

    config            = load_config()
    weekly_limit      = config.get("weekly_token_limit")
    session_limit     = config.get("session_token_limit")

    def limit_line(label, total_in, out, msgs, cost, limit):
        if limit:
            bar_str, pct = progress_bar(total_in, limit)
            return (f"  {label:<18} {fmt(total_in):>6} / {fmt(limit):<7}"
                    f"  [{bar_str}]  {pct*100:>3.0f}%   ${cost:>6.3f}")
        return (f"  {label:<18} {fmt(total_in):>5} in / {fmt(out):<6} out"
                f"  ({msgs:>3} msgs)  ${cost:>6.3f}")

    # Fetch live plan-limit utilisation from the API
    plan_lines = []
    token = get_oauth_token()
    if token:
        plan = fetch_plan_utilization(token)
        if plan:
            bar5, _ = progress_bar(plan["session_pct"], 100)
            bar7, _ = progress_bar(plan["weekly_pct"],  100)
            r5 = fmt_reset(plan["session_reset"])
            r7 = fmt_reset(plan["weekly_reset"])
            plan_lines = [
                "  " + "─" * 52,
                f"  {'Plan 5h window:':<18} [{bar5}]  {plan['session_pct']:>3.0f}%   resets {r5}",
                f"  {'Plan 7d window:':<18} [{bar7}]  {plan['weekly_pct']:>3.0f}%   resets {r7}",
            ]

    sep = "━" * 54
    text = "\n".join([
        "",
        sep,
        f"  {'This response:':<18} {fmt(msg_total_in):>5} in / {fmt(msg_out):<6} out            ${msg_cost:>6.3f}",
        limit_line("Session total:", sess_total_in, sess_out, sess_msgs, sess_cost, session_limit),
        limit_line("This week:",     week_total_in, week_out, week_msgs, week_cost, weekly_limit),
        *plan_lines,
        sep,
        "",
    ])
    print(text)


if __name__ == "__main__":
    main()
