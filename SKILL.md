---
name: wikipedia-interest-skill
description: Analyze Wikipedia pageview trends across topics, language editions, and time periods. Use this skill when a user asks about changes in attention to a topic on Wikipedia, comparisons between language editions, trend reliability, charts, or short shareable reports such as a one-page PDF.
compatibility: Requires Python 3.11+, internet access to Wikimedia APIs, and the Python dependencies declared in pyproject.toml.
metadata:
  version: "1.0"
---

# Wikipedia Interest Skill

Use this skill to analyze interest in topics using Wikimedia pageview data.

The skill can:

- resolve topics to Wikipedia articles across language editions;
- fetch monthly Wikimedia pageview data;
- compare trends across one or more language editions;
- calculate year-over-year growth, trend direction, volatility, spikes, and heuristic confidence;
- generate absolute or indexed trend charts;
- generate structured JSON output;
- generate a one-page PDF research report;
- expose ambiguous or missing article mappings instead of silently guessing.

Wikipedia pageviews are an attention signal. They are not direct measures of market size, purchase intent, willingness to pay, or product demand.

## Main script

Run:

```bash
python scripts/analyze.py
```

## Understand the user's request

Identify:

1. Topic or concept.
2. Wikipedia language editions.
3. Time period.
4. Desired output:
   - analysis only;
   - chart;
   - JSON;
   - one-page PDF.
5. Any comparison or research objective.

Prefer the user's explicit requirements.

If no time period is given and the task is about recent trends, use the latest 24 complete calendar months.

Example:

```bash
python scripts/analyze.py \
  --topic "astronomy" \
  --languages uk \
  --months 24
```

The current incomplete month is excluded automatically.

## Article resolution

Correct topic resolution is required before comparing pageviews.

The normal resolution flow is:

1. Search English Wikipedia for the user's topic.
2. Use the resolved English article as the source concept.
3. Resolve target-language articles through Wikipedia interlanguage links.
4. If no equivalent article exists, return `needs_review` and candidate articles.
5. Do not automatically select a semantically different local article.

A `needs_review` result is preferable to silently comparing unrelated concepts.

Some concepts do not have exact equivalents in all target-language Wikipedia editions.

### Ambiguous source concepts

If the user's wording resolves to the wrong or ambiguous English article, explicitly select a canonical English source article:

```bash
python scripts/analyze.py \
  --topic "learning English" \
  --source-article "English as a second or foreign language" \
  --languages uk pl cs \
  --months 24
```

Use `--source-article` to clarify the intended concept.

Do not use it merely to force a result.

### Explicit target-language proxy

If no exact target-language equivalent exists, a proxy article may be used only when the assumption is explicit.

Use:

```bash
--article-override "LANGUAGE=ARTICLE TITLE"
```

Example:

```bash
python scripts/analyze.py \
  --topic "learning English" \
  --languages uk pl cs \
  --months 24 \
  --article-override "uk=Англійська мова" \
  --article-override "pl=Język angielski" \
  --article-override "cs=Angličtina"
```

When overrides are used, state that they are proxies and may not represent exactly the same user intent.

Never present proxy mappings as exact semantic equivalents.

## Time periods

For recent trend analysis, prefer:

```bash
--months 24
```

This uses the latest 24 complete calendar months.

For an explicit period, use:

```bash
--start YYYYMMDD --end YYYYMMDD
```

Example:

```bash
python scripts/analyze.py \
  --topic "machine learning" \
  --languages cs uk \
  --start 20240101 \
  --end 20251231
```

Use complete months when possible.

## Metrics

The analysis includes:

- total pageviews;
- average monthly pageviews;
- first and latest month;
- first-to-last change;
- year-over-year change for periods with at least 24 months;
- volatility;
- coefficient of variation;
- linear trend slope;
- normalized trend;
- trend label:
  - `growing`
  - `flat`
  - `declining`
- major spike detection;
- heuristic confidence:
  - `high`
  - `medium`
  - `low`

Treat confidence as a transparent heuristic, not a statistical confidence interval.

Confidence considers:

- available history;
- traffic volatility;
- detected spikes;
- agreement between long-term trend and year-over-year change.

When reporting confidence, explain the reasons rather than giving only the label.

## Charts

Generate a chart with:

```bash
--chart output/chart.png
```

### Absolute chart

```bash
--chart-mode absolute
```

Shows raw monthly pageviews.

Absolute traffic across different Wikipedia language editions should not be interpreted as directly comparable market size.

### Indexed chart

```bash
--chart-mode normalized
```

Each series starts at an index of 100 based on its first non-zero month.

Use indexed charts to compare relative trend shapes across language editions.

Do not describe this as normalization for Wikipedia population, language population, or market size.

## JSON output

Generate structured machine-readable output:

```bash
--output output/analysis.json
```

The JSON includes:

- topic;
- period;
- article resolution;
- metrics;
- monthly time series;
- experimental forecast;
- summary;
- status for each language.

Use JSON when another agent, script, or downstream workflow needs the full analysis.

## One-page PDF

Generate a shareable PDF with:

```bash
--report output/report.pdf
```

Example:

```bash
python scripts/analyze.py \
  --topic "astronomy" \
  --languages uk \
  --months 24 \
  --report output/astronomy-report.pdf \
  --output output/astronomy-analysis.json
```

The PDF includes:

- topic and analysis period;
- language/article mappings;
- trend;
- year-over-year change;
- average monthly views;
- latest monthly views;
- confidence;
- indexed pageview chart;
- key findings;
- confidence explanation;
- assumptions;
- research implication;
- limitations;
- generation date and Wikimedia source.

Keep the report compact and suitable for sharing.

## Interpreting results

Use Wikipedia pageviews as evidence of attention to Wikipedia content.

Do not infer directly:

- market size;
- willingness to pay;
- purchase intent;
- product-market fit;
- total language population;
- commercial demand.

Traffic can also be affected by:

- news events;
- seasonality;
- education cycles;
- temporary spikes;
- changes in article visibility or linking.

Prefer conclusions such as:

> Interest in this Wikipedia topic declined year over year, with relatively stable monthly traffic.

Avoid conclusions such as:

> This market is shrinking.

The second statement is not supported by Wikipedia pageviews alone.

## Multi-language comparisons

When comparing multiple language editions:

1. Verify semantic article equivalence first.
2. Compare trend direction and relative change.
3. Use indexed charts for trend shape.
4. Treat absolute pageview differences cautiously.
5. Explain proxy mappings or unresolved languages.
6. Use confidence to distinguish stable trends from noisy ones.

If one language cannot be resolved, continue with the resolved languages and report the unresolved edition explicitly.

## Experimental forecast

The analysis output may include a short linear projection.

Treat it as experimental and directional only.

Do not use the forecast as primary evidence.

Do not use it to calculate confidence.

Do not present it as a prediction of future demand.

Wikipedia traffic may be strongly affected by seasonality, news, and temporary spikes.

## Common edge cases

### No interlanguage article

Return `needs_review`.

Show candidate local articles.

Do not automatically choose the first search result.

### Ambiguous English topic

Use an explicit canonical English source article with `--source-article`.

### Proxy article required

Use `--article-override` and disclose the assumption.

### Large spike

Mention the spike and reduce confidence when appropriate.

Do not interpret a temporary peak as sustained growth.

### High volatility

Explain that trend reliability is limited.

### Cross-language traffic differences

Do not equate larger Wikipedia traffic with a larger commercial market.

## Recommended workflow

For a normal research request:

1. Understand topic, languages, period, and requested output.
2. Run the analysis.
3. Inspect article resolution statuses.
4. Resolve semantic ambiguity if necessary.
5. Re-run with `--source-article` or `--article-override` only when justified.
6. Review trend, YoY, volatility, spikes, and confidence.
7. Generate the requested chart or PDF.
8. Summarize findings and limitations.
9. Suggest what should be researched next if the user is making a product decision.

## Example: recent topic analysis

```bash
python scripts/analyze.py \
  --topic "astronomy" \
  --languages uk \
  --months 24 \
  --chart output/astronomy.png \
  --chart-mode normalized \
  --report output/astronomy-report.pdf \
  --output output/astronomy-analysis.json
```

## Example: cross-language comparison

```bash
python scripts/analyze.py \
  --topic "intermittent fasting" \
  --languages pl cs \
  --months 24
```

If one language returns `needs_review`, do not replace it silently with a loosely related article.

## Example: proxy-based research

```bash
python scripts/analyze.py \
  --topic "learning English" \
  --languages uk pl cs \
  --months 24 \
  --article-override "uk=Англійська мова" \
  --article-override "pl=Język angielski" \
  --article-override "cs=Angličtina" \
  --report output/learning-english-report.pdf
```

In the final interpretation, state that the language articles are proxies for broader interest in English and do not isolate language-learning intent.

## Scaling beyond basic queries

For larger research tasks:

- reuse cached API responses;
- process topics independently;
- retain structured JSON results;
- aggregate comparisons after validating article mappings;
- separate observed data from experimental forecasts;
- preserve assumptions for each proxy or unresolved topic.

For substantially larger datasets or production use, consider:

- concurrency with Wikimedia rate-limit awareness;
- persistent caching;
- retry and backoff logic;
- robust seasonal trend decomposition;
- stronger outlier detection;
- traffic normalization using broader Wikipedia edition activity;
- automated semantic validation of candidate article mappings;
- reproducible evaluation datasets.

See `references/methodology.md` for methodology details.