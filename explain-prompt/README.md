# explain-prompt

A Claude Code skill that analyzes any prompt like a database `EXPLAIN` plan — breaking down token counts by section, estimating cost across model tiers, and generating an optimized rewrite for every issue found.

```
╔══════════════════════════════════════════════════════════╗
║              PROMPT EXPLAIN                              ║
╚══════════════════════════════════════════════════════════╝

SECTION BREAKDOWN
─────────────────────────────────────────────────────────
 Section              Tokens    Share   Bar
 ─────────────────────────────────────────────────────────
 System Prompt            61   100.0%   ████████████████
 ─────────────────────────────────────────────────────────
 TOTAL INPUT              61   100.0%

OUTPUT ESTIMATE (p25/p50/p75)
─────────────────────────────────────────────────────────
 Task type:   Code review + security analysis
 Tokens:      200 / 500 / 800

COST PER CALL  (61 input + p50 500 output tokens)
─────────────────────────────────────────────────────────
 Model        Input Cost    Output Cost   Total/call
 Haiku 4.5    $0.000061     $0.002500     $0.002561
 Sonnet 4.6   $0.000183     $0.007500     $0.007683  ← recommended
 Opus 4.7     $0.000305     $0.012500     $0.012805

AT SCALE (Sonnet 4.6, p50 output)
─────────────────────────────────────────────────────────
 Volume          Standard     Batch API
 1k calls/day    $7.68/day    $3.84/day
 10k calls/day   $76.83/day   $38.42/day
 100k calls/day  $768/day     $384/day

WARNINGS
─────────────────────────────────────────────────────────
 ⚠ [MEDIUM] Hedging language wastes tokens: "Always be thorough",
             "Make sure to follow", "It's important that you"
             Fix: convert to numbered directives (see rewrite below)

 ℹ [INFO]   No output format specified — responses can balloon
             to 1,500+ tokens. Fix: add JSON schema, saves ~$52/day
             at 10k calls.
```

---

## What it analyzes

| Section | Detection |
|---|---|
| System Prompt | `[SYSTEM]`, `<system>`, or instructions/persona text |
| Few-shot Examples | Repeated User/Assistant pairs, JSON example arrays |
| User Message | The actual end-user query |
| Context / RAG chunk | Large injected document or search result blocks |
| Output format spec | "Return JSON", "Format as:", schema definitions |
| Chain-of-thought scaffold | "Think step by step", `<thinking>` blocks |
| File attachments | `.pdf`, `.txt`, `.md`, `.png`, `.jpg` references |
| Template variables | `{{user_name}}`, `{context}` slots with fill-size warnings |

For each section: token count, % share, visual bar, and severity flag if over threshold.

---

## Prerequisites

- **Claude Code** installed (`claude --version` should work)
- No API key required — token counting uses character-ratio heuristics (÷4 for prose, ÷3 for code/JSON)

---

## Installation

One command — no cloned repo to maintain, no symlinks:

```bash
curl -fsSL https://raw.githubusercontent.com/as-sher/claude-skills/main/install.sh | bash -s explain-prompt
```

This uses git sparse-checkout to copy only the `explain-prompt` files into `~/.claude/skills/explain-prompt/` and nothing else.

To update to the latest version, run the same command again.

---

## Usage

### Slash command
```
/explain-prompt <your full prompt text>
```

Paste your entire prompt — system instructions, few-shot examples, template variables, everything — as the argument.

### Natural language triggers
The skill also fires automatically when you say:
- "how many tokens is this prompt"
- "what will this cost on Claude"
- "analyze my prompt"
- "prompt cost estimate"
- "token breakdown"
- "is my prompt efficient"

---

## Examples

**System prompt only:**
```
/explain-prompt You are a helpful customer support agent. Always be polite and professional.
```

**Full prompt with few-shot + template variable:**
```
/explain-prompt [SYSTEM] You are a code reviewer.

User: Review this function
def login(user, pw): db.execute(f"SELECT * FROM users WHERE u='{user}'")
Assistant: {"severity":"CRITICAL","issue":"SQL injection","fix":"use parameterized queries"}

{{code_to_review}}
```

**Multi-turn conversation history:**
```
/explain-prompt User: What is prompt caching?
Assistant: Prompt caching stores repeated context...
User: How much does it save?
```

---

## What the optimized rewrite looks like

For every `⚠ HIGH` or `⚠ MEDIUM` issue, the skill produces a concrete rewrite:

```
OPTIMIZED SECTION: System Prompt
─────────────────────────────────────────────────────────
 Before: 61 tokens — soft prose, no output bound

 After:  42 tokens (-31%) + output bounded to JSON

 You are a security-focused code reviewer for a fintech company.
 For every review:
 1. Identify vulnerabilities (OWASP top 10)
 2. Provide fixes with code examples
 Return JSON: {"severity":"HIGH|MED|LOW","issue":"...","fix":"...","owasp":"..."}

 Input saving:  19 tokens = $0.000057/call = $0.57/day at 10k calls
 Output saving: ~350 tokens (500→150, JSON bounds response)
               = $0.00525/call = $52.50/day at 10k calls
```

---

## Pricing reference

Current rates are in `references/pricing.md` — edit that file to update prices without touching the skill logic.

| Model | Input | Output | Notes |
|---|---|---|---|
| Haiku 4.5 | $1.00/MTok | $5.00/MTok | High-volume, routing |
| Sonnet 4.6 | $3.00/MTok | $15.00/MTok | Production default |
| Opus 4.7 | $5.00/MTok | $25.00/MTok | New tokenizer: +35% token inflation vs 4.6 |

Batch API: 50% off. Prompt caching: 90% off cached input.
