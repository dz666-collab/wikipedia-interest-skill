---
name: wikipedia-interest-analysis
description: Analyze Wikipedia pageview trends across topics, languages, and time periods to support B2C product discovery.
---

# Wikipedia Interest Analysis

Use this skill when a user wants to understand how interest in a topic changes over time in one or more Wikipedia language editions.

## Inputs

Determine:

- topic
- Wikipedia language codes
- time period
- comparison or decision criteria, if explicitly provided

Do not assume Wikipedia pageviews represent willingness to pay.

## Workflow

1. Resolve the user's topic to the corresponding Wikipedia article in each requested language.
2. Fetch pageview data.
3. Analyze the time series.
4. Compare requested languages or periods.
5. Explain assumptions, data quality, and limitations.
6. Generate charts or a report when requested.

## Basic analysis

Run:

```bash
python scripts/analyze.py --topic "<topic>" --languages <codes> --months <n>