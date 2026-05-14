# claude-skills

Personal Claude Code skill collection.

## Skills

| Skill | Description |
|-------|-------------|
| [usage-tracker](usage-tracker/) | Shows token/cost/message stats after every response |

## Installing a skill

```bash
curl -fsSL https://raw.githubusercontent.com/as-sher/claude-skills/main/install.sh | bash -s <skill-name>
```

Files are copied directly into `~/.claude/skills/<skill-name>/` — no repo clone to maintain, no symlinks. Run the same command again to update.
