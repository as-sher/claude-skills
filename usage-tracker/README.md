# usage-tracker

A Claude Code skill that shows token counts, message counts, estimated cost, and live plan-limit utilisation on demand.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  This response:     92.2K in / 196    out            $ 0.034
  Session total:      4.1M in / 42.2K  out  ( 67 msgs)  $ 2.882
  This week:         12.6M in / 151.7K out  (198 msgs)  $29.765
  ────────────────────────────────────────────────────
  Plan 5h window:    [███████████░░░░░░░░░]   57%   resets today 15:00
  Plan 7d window:    [████████░░░░░░░░░░░░]   44%   resets tomorrow 05:30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The top three lines are computed from your local transcript files (exact token counts + dollar cost).  
The bottom two are fetched live from the Anthropic API — they show what fraction of your **plan's rate limit** is consumed, which transcripts alone can't tell you.

---

## Prerequisites

- **macOS** — the plan-limit lines use the macOS Keychain to read your CLI OAuth token. The transcript lines work on any OS.
- **Claude Code** installed and signed in (`claude --version` should work)
- **Python 3** — ships with macOS, verify with `python3 --version`

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/as-sher/claude-skills.git ~/claude-skills
```

### 2. Symlink the skill into Claude Code's skills directory

```bash
mkdir -p ~/.claude/skills
ln -sf ~/claude-skills/usage-tracker ~/.claude/skills/usage-tracker
```

Claude Code discovers skills from `~/.claude/skills/`. The symlink means any future `git pull` in `~/claude-skills` is picked up automatically — no re-linking needed.

### 3. Verify

Open Claude Code and type `/usage-tracker` (or ask "how much have I used?"). You should see the stats block.

---

## How the plan-limit lines work

The skill reads your Claude Code OAuth access token from the macOS Keychain (the same credential Claude Code itself uses), then fires a minimal 1-token Haiku API call and reads the `anthropic-ratelimit-unified-5h-utilization` and `anthropic-ratelimit-unified-7d-utilization` response headers.

This mirrors the approach used by the [Claude Usage Tracker](https://github.com/hamed-elfayome/Claude-Usage-Tracker) macOS app — the dedicated `oauth/usage` endpoint is disabled by Anthropic, so a throwaway API call is the only way to get these headers.

If the Keychain read fails or the API call errors for any reason, the two plan lines are silently omitted and everything else still works.

---

## Optional: token-limit progress bars

Create `~/.claude/usage_config.json` to add progress bars to the session and weekly lines:

```json
{
  "weekly_token_limit": 50000000,
  "session_token_limit": 5000000
}
```

With limits configured the weekly line becomes:

```
  This week:          22.7M / 50.0M    [█████████░░░░░░░░░░░]   45%   $34.35
```

Without the file, raw token counts are shown — the skill works out of the box with no config.

---

## Customising pricing

The default rates are Sonnet 4.6 prices. Edit the constants at the top of `scripts/track_usage.py` to match whichever model you use most:

```python
INPUT_COST_PER_M        = 3.00   # $/M input tokens
CACHE_WRITE_COST_PER_M  = 3.75   # $/M cache creation tokens
CACHE_READ_COST_PER_M   = 0.30   # $/M cache read tokens
OUTPUT_COST_PER_M       = 15.00  # $/M output tokens
```

| Model | Input | Cache write | Cache read | Output |
|---|---|---|---|---|
| Sonnet 4.6 (default) | $3 | $3.75 | $0.30 | $15 |
| Haiku 4.5 | $0.80 | $1 | $0.08 | $4 |
| Opus 4.7 | $15 | $18.75 | $1.50 | $75 |

---

## Weekly reset

Token counts roll up per-session and are stored in `~/.claude/usage_weekly.json`. The weekly total resets automatically each Monday.
