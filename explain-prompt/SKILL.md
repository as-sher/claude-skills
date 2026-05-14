---
name: explain-prompt
description: >
  Analyze any prompt like a database EXPLAIN plan — breaking down token counts
  by section, estimating cost across Claude model tiers, profiling attached files
  and images, and suggesting optimized rewrites for bloated sections.
  
  ALWAYS trigger when the user types /explain-prompt followed by any text, 
  template, or file reference. Also trigger for phrases like "how many tokens 
  is this prompt", "what will this cost on Claude", "analyze my prompt", 
  "prompt cost estimate", "token breakdown", or "is my prompt efficient".
---

# Prompt EXPLAIN Skill

## Step 1: Parse Sections

Identify which of these layers exist in the prompt:

| Section | Detection |
|---|---|
| System Prompt | `[SYSTEM]`, `<system>`, or persona/instructions text |
| Few-shot Examples | Repeated User/Assistant pairs or JSON example arrays |
| User Message | The actual end-user query |
| Context / RAG | Injected document blocks or retrieval results |
| Output format spec | JSON schema, "Return only:", "Format as:" |
| CoT scaffold | "Think step by step", `<thinking>` blocks |
| File attachments | `.pdf`, `.txt`, `.md`, `.png`, `.jpg` references |
| Template variables | `{{slots}}` or `{placeholders}` |

If unstructured (one blob), treat as a single User Message and note that sectioning would improve cache eligibility and analyzability.

## Step 2: Count Tokens

**Text:** prose ÷ 4, code/JSON/YAML ÷ 3 chars per token.

**Images:** resize longest side to ≤1568px, divide into 512×512 tiles.
`tokens = ceil(w/512) × ceil(h/512) × 1600 + 85`
Unknown dimensions: use 3,200 tokens as default.

**PDFs:** text-based: ~667 tokens/page. Scanned (image-based): apply image formula per page — flag explicitly, dramatically more expensive.

**Other files:** `.txt/.md` ÷ 4, `.json/.yaml` ÷ 3, `.csv` ÷ 3.5, `.py/.js/.ts/.sql` ÷ 3.

## Step 3: Estimate Output Tokens

Priority order:
1. Explicit length instruction ("respond in 3 bullets", "return JSON with 5 fields") → parse directly
2. Few-shot output signal → average example output lengths
3. Task-type heuristic:

| Task type | Output estimate |
|---|---|
| Classification / label | 5–20 tokens |
| Structured JSON extraction | 20% of input |
| Summarization | 15–25% of input |
| Q&A / factual | 50–200 tokens |
| Code generation | 300–800 tokens |
| Open-ended generation | 400–1,200 tokens |
| Chain-of-thought | 2–4× expected final answer |

Always report as **p25 / p50 / p75**, not a single number.

## Step 4: Calculate Costs

Pricing (May 2026):

| Model | Input $/MTok | Output $/MTok |
|---|---|---|
| Haiku 4.5 | 1.00 | 5.00 |
| Sonnet 4.6 | 3.00 | 15.00 |
| Opus 4.7 | 5.00 | 25.00 |

Discounts: Batch API 50% off both. Prompt caching 90% off cached input (write cost: 1.25× normal input rate).

Formula: `cost = (input_tokens/1M × input_rate) + (output_tokens/1M × output_rate)`

Show three scale tiers: 1k / 10k / 100k calls/day.

## Step 5: Render Output

Render a terminal-style EXPLAIN plan with these blocks (omit blocks that don't apply):

**SECTION BREAKDOWN** — table: Section | Tokens | Share% | bar (16 chars, █ filled ░ empty) | flag if issue

**OUTPUT ESTIMATE** — Task type, p25/p50/p75 tokens, basis

**COST PER CALL** — all three models, input cost, output cost, total. Mark recommended model with ←

**AT SCALE** — Sonnet 4.6 at 1k/10k/100k/day: Standard | Batch API | With Caching

**VARIABLE SLOTS** — if template variables exist: name, fill-size unknown, projected cost at p50 fill

**WARNINGS** — severity-flagged issues (see Step 6)

## Step 6: Flag Issues

| Check | Threshold | Severity |
|---|---|---|
| Any section > 60% of total | — | ⚠ HIGH |
| Few-shot examples > 3 | count | ⚠ HIGH |
| Total input > 8,000 tokens | — | ⚠ HIGH |
| System prompt > 2,000 tokens | — | ⚠ MEDIUM |
| Dynamic content in static system prompt | pattern | ⚠ MEDIUM |
| Repeated instructions across sections | semantic | ⚠ MEDIUM |
| No output format specified | structural | ℹ INFO |
| Static system prompt, no caching | pattern | ℹ INFO |
| CoT requested, output not bounded | pattern | ℹ INFO |
| Scanned PDF | file type | ⚠ HIGH |
| Image > 1024px either side | dimensions | ℹ INFO |

## Step 7: Optimized Rewrite

For every ⚠ HIGH or ⚠ MEDIUM issue, produce a corrected version of that section with:
- before/after token count and % saved
- dollar saving per call and per day at 10k calls
- the rewritten text inline

Rewrite rules:
- **Bloated system prompt**: remove hedging ("please", "make sure to", "it's important that"), convert to numbered directives, deduplicate repeated instructions
- **Too many few-shot examples**: keep the 2 most structurally diverse, drop the rest
- **No output format**: add a tight JSON schema or length constraint that bounds output tokens
- **Non-cacheable system prompt**: split into a static prefix (cacheable) and a dynamic suffix
- **CoT unbounded**: add `<answer>` tags to separate reasoning from final answer

After all rewrites, show an updated EXPLAIN plan so the before/after improvement is visible at a glance.

## Edge Cases

- **Template variables** `{{x}}`: count as ~3 tokens each; note actual cost depends on fill. Ask for typical fill size if precise projection needed.
- **JSON/structured prompts**: detect `{"role": "system", ...}` format and parse into sections automatically.
- **Multi-turn conversations**: calculate rolling cost — each turn's input includes all prior turns.
- **Opus 4.7**: always note its new tokenizer produces ~35% more tokens than Opus 4.6 for identical input. Suggest benchmarking before migrating at scale.

## Tone

Write like a senior engineer reviewing a query plan: numbers first, explanation second, every warning includes a concrete fix.
