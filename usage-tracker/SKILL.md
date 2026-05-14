---
name: usage-tracker
description: Show token count, message count, and estimated cost in dollars for the current session and this week. Invoke when the user asks for usage, tokens, cost, spend, "how much have I used", "how much is this session costing", "show usage stats", or types /usage. Display the stats immediately — no setup required.
---

# Usage Tracker

Shows token/message/cost stats for the current session and rolling weekly total on demand.

## When invoked

Run this exact command and show the output to the user:

```bash
TRANSCRIPT=$(ls -t ~/.claude/projects/-Users-ashutoshsrivastava/*.jsonl 2>/dev/null | head -1) && \
echo "{\"session_id\":\"current\",\"transcript_path\":\"$TRANSCRIPT\"}" | \
python3 ~/.claude/skills/usage-tracker/scripts/track_usage.py
```

Then display the output block verbatim in your response.

## What the output looks like

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  This response:      1.2K in / 567    out            $ 0.018
  Session total:      8.4K in / 2.1K   out  ( 12 msgs)  $ 0.057
  This week:           45K in / 8.9K   out  ( 48 msgs)  $ 0.269
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Pricing defaults: Sonnet 4.6 — $3/M input, $15/M output (edit `track_usage.py` to change).
Weekly store: `~/.claude/usage_weekly.json`, resets each Monday.

## If the output is empty

The transcript path couldn't be found or has no assistant messages yet. Tell the user to send one more message and try again.
