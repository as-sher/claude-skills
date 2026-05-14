# claude-skills

Personal Claude Code skill collection.

## Skills

| Skill | Description |
|-------|-------------|
| [usage-tracker](usage-tracker/) | Shows token/cost/message stats after every response |

## Installing a skill

Skills are discovered from `~/.claude/skills/`. Symlink from this repo so changes here are picked up automatically:

```bash
ln -sf ~/claude-skills/<skill-name> ~/.claude/skills/<skill-name>
```

Then invoke the skill in Claude Code to complete any one-time setup (e.g. hook configuration).
