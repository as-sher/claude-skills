# Claude Pricing Reference
Last verified: May 2026

## Current Generation Models

| Model | Input $/MTok | Output $/MTok | Context | Notes |
|---|---|---|---|---|
| Haiku 4.5 | $1.00 | $5.00 | 200K | Fastest, cheapest |
| Sonnet 4.6 | $3.00 | $15.00 | 1M | Best price/quality |
| Opus 4.6 | $5.00 | $25.00 | 1M | Flagship |
| Opus 4.7 | $5.00 | $25.00 | 1M | New tokenizer: +35% token inflation vs 4.6 |

## Discount Mechanisms

| Mechanism | Discount | Condition |
|---|---|---|
| Batch API | 50% off input + output | Async, 24hr SLA, not real-time |
| Prompt caching (5 min) | 90% off cached input | Repeated system prompt / context |
| Prompt caching (1 hr) | 90% off cached input | 2× base write cost |

## Effective Rates With Discounts (Sonnet 4.6)

| Scenario | Input $/MTok | Output $/MTok |
|---|---|---|
| Standard | $3.00 | $15.00 |
| Batch only | $1.50 | $7.50 |
| Caching (cached portion) | $0.30 | $15.00 |
| Batch + caching | $0.15 | $7.50 |

## Vision / Image Pricing

Images are billed as input tokens using a tile-based system:
- Each 512×512 tile = ~1,600 tokens
- Base image overhead = ~85 tokens
- Max resolution: 1568px on longest side (auto-resized)

Quick reference:
| Image size | Tokens | Sonnet cost |
|---|---|---|
| 512×512 | ~1,685 | $0.005 |
| 800×600 | ~3,285 | $0.010 |
| 1024×768 | ~4,885 | $0.015 |
| 1024×1024 | ~6,485 | $0.019 |
| 1568×1568 | ~14,485 | $0.043 |

## Tokenizer Notes

- Claude Haiku/Sonnet 4.x: standard tokenizer, ~4 chars/token for English
- Opus 4.7: new tokenizer, may generate up to 35% more tokens for same input
  → a 1,000 token prompt on Opus 4.6 may cost 1,350 tokens on Opus 4.7
  → per-token price is unchanged, but effective cost per request rises
  → always benchmark Opus 4.7 on real workloads before migrating

## Legacy Models (for reference)

| Model | Input $/MTok | Output $/MTok |
|---|---|---|
| Claude 3 Haiku | $0.25 | $1.25 |
| Claude 3 Sonnet | $3.00 | $15.00 |
| Claude 3 Opus | $15.00 | $75.00 |
| Opus 4.1 | $15.00 | $75.00 |
