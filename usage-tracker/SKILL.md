---
name: usage-tracker
description: Set up automatic token/cost/message usage display after every Claude Code response. Shows per-message tokens, session totals, and weekly rolling stats with estimated cost in dollars. Trigger when user asks to "track usage", "show usage stats", "set up usage tracking", "monitor tokens", "how much is this session costing", or wants to see token counts or costs per prompt. Also use when user wants awareness of their Claude Code spend.
---

# Usage Tracker

Installs a Stop hook that prints a compact usage summary after every response.

## What gets shown

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  This response:  1.2K in / 567 out                $0.018
  Session total:  8.4K in / 2.1K out  (12 msgs)   $0.057
  This week:       45K in / 8.9K out  (48 msgs)   $0.269
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Data source: the session transcript JSONL Claude Code maintains at `transcript_path` in the hook payload.
Weekly store: `~/.claude/usage_weekly.json` — resets each Monday.
Pricing: Sonnet 4.6 defaults ($3/M input, $15/M output). Edit `track_usage.py` to change rates.

## Setup (follow when invoked)

1. **Check if already installed** — look in `~/.claude/settings.json` for a Stop hook pointing to `track_usage.py`. If found, tell the user it's already set up.

2. **Symlink the skill** so Claude Code discovers it:
   ```bash
   ln -sf ~/claude-skills/usage-tracker ~/.claude/skills/usage-tracker
   ```

3. **Add the Stop hook** to `~/.claude/settings.json` under the `hooks` key:
   ```json
   "Stop": [{
     "matcher": "",
     "hooks": [{
       "type": "command",
       "command": "python3 ~/.claude/skills/usage-tracker/scripts/track_usage.py"
     }]
   }]
   ```
   Merge carefully — preserve any existing hooks.

4. **Confirm** — tell the user usage will now display after every response, and that the weekly store resets each Monday.

## Uninstalling

Remove the Stop hook entry from `settings.json` and delete the symlink:
```bash
rm ~/.claude/skills/usage-tracker
```
