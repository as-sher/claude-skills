# explain-prompt

Architectural profiler for LLM inference pipelines.

---

## What to profile

Unlike SQL queries, user messages are dynamic — different every call, not worth profiling individually.

The target is the long-lived infrastructure that *wraps* those messages. In production AI systems, these components accumulate cost, variance, and latency debt:

| Component | Why it matters |
|---|---|
| System instructions | The largest static block; often the least scrutinized |
| Tool definitions | Injected on every call; can exceed 2,000 tokens unnoticed |
| Agent scaffolding | Orchestration prompts that grow with each new capability |
| RAG assembly templates | Context injection patterns that determine cache eligibility |
| Memory injection | Conversation history formatting and retrieval framing |
| Output schemas | Presence or absence determines output variance |
| Workflow templates | Multi-step prompts that compound cost at each stage |

These components change infrequently, get reviewed rarely, and tend to grow monotonically. `explain-prompt` treats them as what they are: infrastructure with measurable cost, structure, and optimization properties.

---

## Why this exists

Production LLM systems accumulate prompt debt the same way codebases accumulate technical debt — silently, until it becomes expensive.

Teams running LLMs at scale routinely encounter:

- **Context inflation**: prompts grow 2-3x over six months as requirements accumulate. No one notices until p99 latency doubles and the bill spikes.
- **Output variance**: no output schema means response length varies 10x across identical request types. Downstream parsers break. Costs are unpredictable.
- **Non-cacheable prompts**: dynamic content injected into static system instructions defeats prompt caching, paying full input price on every call.
- **Few-shot bloat**: examples added incrementally until they represent 70%+ of prompt cost, with no visibility into the marginal value of each one.
- **Prompt sprawl**: the same instruction appears in three sections. 15-20% of input tokens are redundancy.

`explain-prompt` surfaces these issues before they reach production — the same way `EXPLAIN ANALYZE` surfaces index misses before they reach query SLAs.

---

## What it analyzes

| Section | Detection signal |
|---|---|
| System prompt | Instructions, persona definitions, policy blocks |
| Few-shot examples | User/Assistant pairs, JSON example arrays |
| RAG / context chunks | Injected document blocks, retrieval results |
| Output schema | JSON specs, format constraints, bounded fields |
| Chain-of-thought scaffold | `<thinking>` blocks, step-by-step instructions |
| Template variables | `{{slots}}` with fill-size impact estimates |
| File attachments | PDF, image, and code file token projections |

For each section: token count, percentage share, visual bar, cacheability assessment, and issue severity rating.

---

## Example output

```
╔══════════════════════════════════════════════════════════╗
║              PROMPT EXPLAIN                              ║
╚══════════════════════════════════════════════════════════╝

SECTION BREAKDOWN
─────────────────────────────────────────────────────────
 Section              Tokens    Share   Bar
 ─────────────────────────────────────────────────────────
 System Prompt            61    10.3%   ██░░░░░░░░░░░░░░
 Few-shot Examples       412    69.5%   ███████████░░░░░  ⚠ HIGH
 RAG Context             110    18.6%   ███░░░░░░░░░░░░░
 Template Variable         3     0.5%   ░░░░░░░░░░░░░░░░
 ─────────────────────────────────────────────────────────
 TOTAL INPUT             593   100.0%

OUTPUT ESTIMATE (p25/p50/p75)
─────────────────────────────────────────────────────────
 Task type:   Structured extraction (JSON)
 Tokens:      80 / 120 / 200
 Basis:       Few-shot output signal

COST PER CALL  (Sonnet 4.6, p50 output)
─────────────────────────────────────────────────────────
 Input: $0.001779   Output: $0.001800   Total: $0.003579

AT SCALE
─────────────────────────────────────────────────────────
 10k calls/day   $35.79/day   Standard
                 $17.90/day   Batch API
                  $8.20/day   With prompt caching

WARNINGS
─────────────────────────────────────────────────────────
 ⚠ [HIGH]   Few-shot section = 69.5% of input
             4 examples where 2 would suffice.
             Saving: $12.40/day at 10k calls.

 ⚠ [MEDIUM] System prompt not cache-eligible.
             Dynamic content mixed into static instructions.
             Separate static prefix to enable caching.

 ℹ [INFO]   No output schema detected.
             Response length variance: 8x between p25 and p75.
             Add JSON schema to bound outputs and reduce variance.
```

---

## Production example

A support automation team analyzed their 18,000-token prompt before a scaling event.

**Before**
- 18,200 input tokens per call
- System prompt contained 3 duplicated policy blocks (~2,400 tokens of redundancy)
- 8 few-shot examples accumulated over 14 months of iteration
- RAG context injected directly into static system instructions — non-cacheable
- No output schema: response length ranged from 200 to 1,800 tokens per call

**After**
- 10,500 input tokens (-42%)
- Policy blocks deduplicated, 3 examples retained (most structurally diverse)
- Static prefix isolated — prompt cache hit rate: 94%
- JSON output schema added: response length bounded at 150-220 tokens (-72% output variance)

**Operational impact at 50,000 calls/day on Sonnet 4.6**

| | Daily cost |
|---|---|
| Before | $2,457 |
| After | $387 |
| Annual delta | ~$750,000 |

The prompt was not rewritten. The architecture was fixed.

---

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/as-sher/claude-skills/main/install.sh | bash -s explain-prompt
```

Installs to `~/.claude/skills/explain-prompt/`. Run the same command to update.

---

## Usage

```
/explain-prompt <prompt text>
```

Paste any prompt — system instructions, few-shot examples, RAG context, template variables, or a full multi-turn conversation. The skill parses structural sections, profiles token distribution, estimates output variance, calculates per-model costs with batch and caching discounts, flags architectural issues by severity, and generates a corrected version for every warning.

Also triggers on: `"token breakdown"`, `"what will this cost on Claude"`, `"analyze my prompt"`, `"is my prompt efficient"`.

---

## Architecture notes

**Token estimation** uses offline heuristics: ÷4 for prose, ÷3 for code and structured data (JSON, YAML, SQL). Accuracy is within 5-10% for typical prompts — sufficient for architectural analysis and order-of-magnitude cost modeling. This is a deliberate tradeoff: offline estimation is instantaneous and requires no API credentials. For billing-precision counts, use the Anthropic token counting endpoint directly.

**Pricing data** lives in `references/pricing.md`. Update that file to reflect new model releases or rate changes without modifying skill logic.

---

## Roadmap

- **Prompt diffing**: compare two prompt versions and surface regressions — token count increases, schema coverage drops, new unbounded sections
- **Cache boundary detection**: identify the optimal static/dynamic split for maximum cache efficiency given a call pattern
- **Routing analysis**: classify prompt complexity to recommend model tier (Haiku vs Sonnet vs Opus) based on task type and output requirements
- **Schema adherence scoring**: analyze whether output format instructions are structured to produce deterministic, parseable responses
- **CI integration**: run as a pre-commit or CI check — fail builds when prompt token count exceeds defined thresholds or new unbounded sections appear
- **Multi-turn cost projection**: model full conversation cost curves across N turns, not just single-call estimates
