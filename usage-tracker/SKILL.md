---
name: usage-tracker
description: Show token count, message count, and estimated cost in dollars for the current session and this week. Invoke when the user asks for usage, tokens, cost, spend, "how much have I used", "how much is this session costing", "show usage stats", or types /usage. Display the stats immediately — no setup required.
---

# Usage Tracker

Shows token/message/cost stats for the current session and rolling weekly total on demand.

## When invoked

Run this exact command and show the output to the user:

```bash
HOME_SLUG=$(echo "$HOME" | sed 's|/|-|g') && \
TRANSCRIPT=$(/bin/ls -t ~/.claude/projects/${HOME_SLUG}/*.jsonl 2>/dev/null | head -1) && \
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
  ────────────────────────────────────────────────────
  Plan 5h window:    [███████████░░░░░░░░░]   56%   resets today 15:00
  Plan 7d window:    [████████░░░░░░░░░░░░]   44%   resets tomorrow 05:30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The top three lines come from local transcript parsing (exact token counts + cost).
The bottom two come from the Anthropic API via a minimal Haiku call — they show what
fraction of your **plan's rate limit** is consumed, which transcripts alone can't reveal.

Pricing defaults: Sonnet 4.6 — $3/M input, $15/M output (edit `track_usage.py` to change).
Weekly store: `~/.claude/usage_weekly.json`, resets each Monday.
Plan-limit lines are silently omitted if the Keychain token is unavailable or the API call fails.

## Optional: show % of limit

Create `~/.claude/usage_config.json` to enable progress bars:

```json
{
  "weekly_token_limit": 50000000,
  "session_token_limit": 5000000
}
```

With limits set, the weekly (and/or session) line becomes:
```
  This week:          22.7M / 50.0M    [█████████░░░░░░░░░░░]   45%   $34.35
```

Without the config file, raw token counts are shown — works for everyone with no setup.

## If the output is empty

The transcript path couldn't be found or has no assistant messages yet. Tell the user to send one more message and try again.
