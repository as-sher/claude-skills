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

Like `EXPLAIN` in SQL, this skill makes the invisible visible — showing developers
exactly what their prompt costs before they pay it, where the waste is, and how to fix it.

---

## Trigger

User types: `/explain-prompt <prompt text or template>`

Or pastes a prompt and asks about cost, tokens, or efficiency.

---

## Step 1: Parse the Input

Identify the prompt's **structural sections**. Look for these layers (not all will be present):

| Section | Signals to detect |
|---|---|
| System Prompt | Starts with `[SYSTEM]`, `<system>`, or is labeled as instructions/persona |
| Few-shot Examples | Repeated Q/A or input/output pairs, JSON arrays of examples |
| User Message | The actual end-user query or task |
| Context / RAG chunk | Large text blocks that look like documents, search results, or retrieved data |
| Output format spec | "Respond in JSON", "Format as:", "Return only:" instructions |
| Chain-of-thought scaffold | "Think step by step", `<thinking>` blocks, reasoning prompts |
| File attachments | Any mention of uploaded files (.pdf, .txt, .md, .png, .jpg, etc.) |

If the prompt is unstructured (one big blob), treat the entire thing as a single "User Message" section and note that sectioning would improve analyzability.

---

## Step 2: Count Tokens Per Section

Use this **token estimation logic**:

### Text
- English prose: **1 token ≈ 4 characters** (or ~0.75 words)
- Code / JSON / YAML: **1 token ≈ 3 characters** (denser due to symbols)
- Formula: `token_estimate = ceil(char_count / chars_per_token)`

### Images (if attached or referenced)
Claude uses a **tile-based vision system**:
1. Image is resized so the longest side ≤ 1568px (maintaining aspect ratio)
2. Resized image is divided into **512×512 tiles**
3. Each tile = **~1,600 tokens** (base overhead + tile content)
4. Plus a **base overhead of ~85 tokens** per image regardless of size

```
tiles_wide  = ceil(width / 512)
tiles_tall  = ceil(height / 512)
total_tiles = tiles_wide × tiles_tall
image_tokens = (total_tiles × 1600) + 85
```

Common image costs:
| Resolution | Tiles | Tokens |
|---|---|---|
| 512×512 | 1 | ~1,685 |
| 1024×1024 | 4 | ~6,485 |
| 1568×1568 | 9 | ~14,485 |
| 800×600 | 2 | ~3,285 |

If image dimensions are unknown, use **3,200 tokens** as a conservative default and note the assumption.

### PDFs
- **Text-based PDF**: extract character count → apply text formula. Assume ~500 words/page → ~667 tokens/page.
- **Scanned PDF (image-based)**: treated as one image per page → apply image formula per page. Flag this explicitly — it is dramatically more expensive.
- If type unknown: assume text-based, note caveat.

### Other files
| File type | Estimation |
|---|---|
| .txt / .md | char_count / 4 |
| .json / .yaml | char_count / 3 |
| .csv | char_count / 3.5 |
| .py / .js / .ts / .sql | char_count / 3 |

---

## Step 3: Estimate Output Tokens

Use the following heuristics in priority order:

1. **Explicit instruction** — if prompt says "respond in 3 bullets", "write 200 words", "return JSON with 5 fields": parse and estimate directly
2. **Few-shot output signal** — if few-shot examples are present, average their output lengths and use as the output estimate
3. **Task-type classification**:

| Task type | Output estimate |
|---|---|
| Classification / label | 5–20 tokens |
| Extraction (structured JSON) | 20% of input size |
| Summarization | 15–25% of input size |
| Q&A / factual | 50–200 tokens |
| Code generation | 300–800 tokens |
| Open-ended generation | 400–1,200 tokens |
| Chain-of-thought reasoning | 2–4× of expected final answer |

Always report as **p25 / p50 / p75 range**, not a single number.

---

## Step 4: Calculate Costs

### Current Claude Pricing

Read `references/pricing.md` for current model rates, discount mechanisms, and image/vision pricing.
Use those rates for all cost calculations below.

**Discounts to show:**
- **Batch API**: 50% off input + output (async, 24hr SLA)
- **Prompt caching**: up to 90% off cached input (if system prompt is static)

### Cost formula per call
```
input_cost  = (input_tokens  / 1_000_000) × input_price
output_cost = (output_tokens / 1_000_000) × output_price
total_cost  = input_cost + output_cost
```

### Scale projection
Always show three volume tiers:
- 1,000 calls/day
- 10,000 calls/day  
- 100,000 calls/day

---

## Step 5: Render the EXPLAIN Output

Use this exact format — it should feel like a terminal explain plan:

```
╔══════════════════════════════════════════════════════════╗
║              PROMPT EXPLAIN                              ║
╚══════════════════════════════════════════════════════════╝

SECTION BREAKDOWN
─────────────────────────────────────────────────────────
 Section              Tokens    Share   Bar
 ─────────────────────────────────────────────────────────
 System Prompt         1,240    24.0%   ████████░░░░░░░░
 Few-shot Examples     3,800    73.6%   ████████████████  ⚠ HIGH
 User Message            120     2.3%   █░░░░░░░░░░░░░░░
 ─────────────────────────────────────────────────────────
 TOTAL INPUT           5,160   100.0%

OUTPUT ESTIMATE (p25/p50/p75)
─────────────────────────────────────────────────────────
 Task type:   Open-ended generation
 Tokens:      400 / 700 / 1,200
 Basis:       Task classification heuristic

COST PER CALL
─────────────────────────────────────────────────────────
 Model          Input Cost   Output Cost   Total/call
 Haiku 4.5      [calculated]  [calculated]  [calculated]
 Sonnet 4.6     [calculated]  [calculated]  [calculated]  ← recommended
 Opus 4.7       [calculated]  [calculated]  [calculated]

AT SCALE (Sonnet 4.6, p50 output)
─────────────────────────────────────────────────────────
 Volume         Standard      Batch API     With Caching
 1k calls/day   [calculated]  [calculated]  [calculated]
 10k calls/day  [calculated]  [calculated]  [calculated]
 100k calls/day [calculated]  [calculated]  [calculated]

WARNINGS
─────────────────────────────────────────────────────────
 ⚠ [HIGH]   Few-shot Examples = 73.6% of prompt
             3,800 tokens in examples is expensive.
             Consider: reduce to 2 examples, or move to
             a retrieval-based few-shot system.

 ℹ [INFO]   System prompt is static across calls.
             Prompt caching could save ~90% on that section.
             Estimated saving: \$X.XX/day at 10k calls.
```

Adapt the output to the actual sections found. Do not show sections that don't exist.

---

## Step 6: Flag Issues

After the plan, run these checks and flag any that apply:

| Check | Threshold | Severity |
|---|---|---|
| Single section > 60% of total | Any section | ⚠ HIGH |
| Few-shot examples > 3 | Count | ⚠ HIGH |
| Total prompt > 8,000 tokens | Total | ⚠ HIGH |
| System prompt > 2,000 tokens | Tokens | ⚠ MEDIUM |
| No output format specified | Structural | ℹ INFO |
| Static system prompt, no caching mentioned | Pattern | ℹ INFO |
| Scanned PDF detected | File type | ⚠ HIGH (vision tokens) |
| Image > 1024px on either side | Dimensions | ℹ INFO (approaching max tiles) |
| Repeated instructions in multiple sections | Semantic | ⚠ MEDIUM |
| Chain-of-thought requested, output not bounded | Pattern | ℹ INFO |

---

## Step 7: Generate Optimized Rewrite

For every ⚠ HIGH or ⚠ MEDIUM issue, produce an optimized version of that section.

### Rewrite rules:
- **Bloated system prompt**: compress to directive style. Remove hedging ("please", "make sure to", "it's important that"). Convert prose rules to numbered lists. Remove redundant repetition.
- **Too many few-shot examples**: keep the 2 most diverse, drop the rest. Note which were removed and why.
- **Redundant context**: identify sentences that restate each other. Remove the weaker one.
- **Missing output format**: add a tight JSON schema or format spec that bounds output token count.
- **Chain-of-thought unbounded**: add `<answer>` tags to separate reasoning from final answer, allowing the caller to extract just the answer.

Show the rewrite as a diff or side-by-side, with the new token count and savings clearly labeled:

```
OPTIMIZED SECTION: Few-shot Examples
─────────────────────────────────────────────────────────
 Before: 3,800 tokens (4 examples)
 After:  1,100 tokens (2 examples — kept most diverse pair)
 Saving: 2,700 tokens = [cost saving/call on Sonnet] = [cost saving/day at 10k calls]

[optimized text shown here]
```

After all rewrites, show the **updated EXPLAIN plan** with new totals so the developer can see the before/after improvement at a glance.

---

## Edge Cases

- **Template variables** like `{{user_name}}` or `{context}`: count as ~3 tokens each for the variable itself, but note that actual cost depends on what fills them. Flag variable slots and ask developer to provide typical fill sizes if they want accurate projection.
- **JSON/structured prompts** passed as raw text: detect `{"role": "system", ...}` format and parse into sections automatically.
- **Multi-turn conversations**: if the input looks like a conversation history, calculate rolling cost (each turn adds to the input of the next).
- **Opus 4.7 warning**: always note that Opus 4.7 uses a new tokenizer that can produce up to 35% more tokens than Opus 4.6 for the same input. Suggest benchmarking before migrating.

---

## Tone

Write the output like a senior engineer's performance review of a query plan — direct, specific, no fluff. Numbers first, explanation second. Every warning must include a concrete fix. Never say "consider optimizing" without showing the optimized version.
