# Wikipedia Interest Skill

A standalone Agent Skill for analyzing Wikipedia pageview trends across topics, language editions, and time periods.

The skill uses Wikimedia pageview data to help answer questions such as:

- Is interest in a topic growing or declining?
- How does the trend differ across Wikipedia language editions?
- How reliable is the observed trend?
- Which language editions may be worth researching further?
- Can the result be shared as a chart, JSON file, or one-page PDF?

Some concepts do not have exact equivalents in all target-language Wikipedia editions.

In those cases, the skill returns `needs_review` instead of silently choosing a loosely related article. Explicit proxy articles can be supplied when appropriate and must be disclosed as assumptions.

## Features

- topic-to-article resolution across Wikipedia language editions;
- monthly Wikimedia pageview retrieval;
- year-over-year growth;
- trend direction;
- volatility analysis;
- spike detection;
- heuristic confidence;
- indexed and absolute charts;
- JSON output;
- one-page PDF reports;
- explicit handling of ambiguous or missing article mappings;
- explicit source-article selection for ambiguous concepts;
- explicit target-language proxy overrides;
- local caching for repeated queries;
- experimental short-term forecast in structured output.

## Requirements

- Python 3.11+
- Internet access
- Wikimedia API access

Install dependencies from the project root:

```bash
pip install -e .
```

For development and tests:

```bash
pip install -e ".[dev]"
```

## Basic usage

Analyze one topic:

```bash
python scripts/analyze.py \
  --topic "astronomy" \
  --languages uk \
  --months 24
```

The `--months` option uses the latest complete calendar months and excludes the current incomplete month.

For example, if the current month is September 2026:

```text
--months 24
```

uses:

```text
Sep 2024 to Aug 2026
```

## Generate JSON output

```bash
python scripts/analyze.py \
  --topic "astronomy" \
  --languages uk \
  --months 24 \
  --output output/astronomy-analysis.json
```

The JSON output contains:

- topic;
- resolved article information;
- language;
- exact analysis dates;
- monthly time series;
- calculated metrics;
- trend;
- volatility;
- detected spikes;
- heuristic confidence;
- confidence reasons;
- experimental forecast;
- report-ready summary.

## Generate a chart

```bash
python scripts/analyze.py \
  --topic "astronomy" \
  --languages uk \
  --months 24 \
  --chart output/astronomy.png \
  --chart-mode normalized
```

Chart modes:

- `absolute` — raw monthly pageviews;
- `normalized` — indexed trend where the first non-zero month equals 100.

The normalized chart is useful for comparing relative trend shapes.

It is not normalization by population, Wikipedia audience size, language population, or market size.

## Generate a one-page PDF report

```bash
python scripts/analyze.py \
  --topic "astronomy" \
  --languages uk \
  --months 24 \
  --report output/astronomy-report.pdf \
  --output output/astronomy-analysis.json
```

The report includes:

- topic;
- analysis period;
- language/article mapping;
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
- generation date;
- Wikimedia source.

The report is designed to remain compact and shareable on one page.

## Cross-language comparison

Example:

```bash
python scripts/analyze.py \
  --topic "intermittent fasting" \
  --languages pl cs \
  --months 24
```

The skill first attempts to resolve a common source concept and then follows Wikipedia interlanguage links.

If a target-language Wikipedia edition has no exact equivalent, the result may return:

```text
needs_review
```

The skill does not automatically replace the missing article with the first loosely related local search result.

This behavior is intentional because some concepts do not have exact equivalents in all target-language Wikipedia editions.

## Explicit source article

If the user's wording is ambiguous or resolves to the wrong English Wikipedia concept, specify the intended canonical source article.

Example:

```bash
python scripts/analyze.py \
  --topic "learning English" \
  --source-article "English as a second or foreign language" \
  --languages uk pl cs \
  --months 24
```

Use `--source-article` to clarify the source concept.

It should not be used merely to force interlanguage matches.

## Explicit article proxies

If exact equivalents do not exist, explicit proxy articles can be supplied per target language.

Example:

```bash
python scripts/analyze.py \
  --topic "learning English" \
  --languages uk pl cs \
  --months 24 \
  --article-override "uk=Англійська мова" \
  --article-override "pl=Język angielski" \
  --article-override "cs=Angličtina" \
  --chart output/learning-english.png \
  --chart-mode normalized \
  --report output/learning-english-report.pdf \
  --output output/learning-english-analysis.json
```

These article mappings are proxies for broader interest in English.

They do not isolate language-learning intent.

Proxy mappings are assumptions and should always be disclosed in interpretation.

## Manual date range

Use explicit start and end dates when a fixed historical period is required.

```bash
python scripts/analyze.py \
  --topic "machine learning" \
  --languages uk cs \
  --start 20240101 \
  --end 20251231
```

Prefer complete calendar months for trend analysis.

The raw JSON preserves exact request boundaries.

The PDF presents monthly periods in human-readable form, such as:

```text
Jan 2024 to Dec 2025
```

## Metrics

The current analysis includes:

- total pageviews;
- average monthly pageviews;
- first-month views;
- latest-month views;
- first-to-last percentage change;
- year-over-year growth;
- standard deviation;
- coefficient of variation;
- linear trend slope;
- normalized trend;
- trend label;
- major spike count;
- spike months;
- heuristic confidence;
- confidence reasons.

Trend labels are:

```text
growing
flat
declining
```

Confidence labels are:

```text
high
medium
low
```

Confidence is a transparent heuristic.

It is not a statistical confidence interval.

## Confidence

Confidence considers:

- available history;
- monthly volatility;
- major traffic spikes;
- consistency between year-over-year change and long-term trend direction.

Example:

```text
Confidence: low
Reason: Monthly traffic is highly volatile.
```

The purpose is to communicate signal reliability rather than only report a trend direction.

## Experimental forecast

Structured output includes a short experimental linear forecast.

It is intentionally not used as primary evidence in the PDF report.

The forecast:

- is directional only;
- is not used to calculate confidence;
- should not be interpreted as a prediction of product demand;
- may perform poorly when traffic is seasonal or affected by spikes.

## Caching

Wikimedia responses are cached locally.

Caching helps:

- reduce repeated API requests;
- speed up related queries;
- make iterative research cheaper;
- support repeated agent workflows.

The current cache is intended for small research and development workflows.

Production use would benefit from explicit cache expiry or invalidation rules.

## Tests

Run the test suite with:

```bash
python -m pytest -q
```

The current metric test suite covers:

- basic metrics;
- growing trend;
- declining trend;
- flat trend;
- spike detection;
- year-over-year growth;
- short history behavior;
- empty input validation.

## End-to-end example

This command exercises article overrides, Wikimedia retrieval, metrics, indexed chart generation, JSON output, and a one-page PDF report:

```bash
python scripts/analyze.py \
  --topic "learning English" \
  --languages uk pl cs \
  --months 24 \
  --article-override "uk=Англійська мова" \
  --article-override "pl=Język angielski" \
  --article-override "cs=Angličtina" \
  --chart output/e2e-learning-english.png \
  --chart-mode normalized \
  --report output/e2e-learning-english-report.pdf \
  --output output/e2e-learning-english-analysis.json
```

Expected artifacts:

```text
output/
├── e2e-learning-english.png
├── e2e-learning-english-report.pdf
└── e2e-learning-english-analysis.json
```

## Project structure

```text
wikipedia-interest-skill/
├── SKILL.md
├── README.md
├── pyproject.toml
├── .gitignore
├── scripts/
│   ├── __init__.py
│   ├── analyze.py
│   ├── wikipedia.py
│   ├── metrics.py
│   ├── charts.py
│   ├── cache_utils.py
│   ├── forecast.py
│   ├── summary.py
│   └── report.py
├── references/
│   └── methodology.md
├── assets/
├── tests/
│   └── test_metrics.py
└── output/
```

`output/` and `.cache/` are intended to remain outside version control.

## Interpretation

Wikipedia pageviews are treated as an attention signal.

They should not be interpreted directly as:

- market size;
- product demand;
- willingness to pay;
- purchase intent;
- product-market fit;
- total language population.

Cross-language absolute pageview totals should also not be treated as directly comparable market sizes.

For cross-language research, the skill emphasizes:

- semantic article equivalence;
- trend direction;
- relative change;
- volatility;
- confidence;
- explicit assumptions.

## Design principles

The implementation favors:

- transparent calculations;
- conservative semantic resolution;
- explicit uncertainty;
- explicit proxy assumptions;
- reproducible outputs;
- reusable structured data;
- simple workflows suitable for fast, low-cost tool-capable agents.

When uncertain, the skill prefers:

```text
needs_review
```

over silently using a questionable article mapping.

## Methodology

See:

```text
references/methodology.md
```

for details on:

- article resolution;
- proxy handling;
- time windows;
- year-over-year growth;
- trend estimation;
- volatility;
- spikes;
- confidence;
- indexed charts;
- cross-language interpretation;
- experimental forecasting;
- caching;
- known limitations;
- future scaling.

## Limitations

The implementation intentionally prioritizes simplicity and explainability.

Current limitations include:

- some concepts do not have exact equivalents in all target-language Wikipedia editions;
- ambiguous source topics may require manual source clarification;
- proxy selection may require agent or user judgment;
- confidence is heuristic;
- trend estimation does not explicitly model seasonality;
- spike detection is basic;
- cross-language pageviews are not normalized for total Wikipedia edition activity;
- forecast output is experimental;
- local cache invalidation is basic;
- large workloads are processed sequentially.

These limitations are surfaced rather than hidden.

## Future improvements

Potential future improvements include:

- concurrent Wikimedia requests;
- retry and backoff logic;
- stronger cache management;
- batch topic analysis;
- robust outlier detection;
- seasonal decomposition;
- edition-level traffic normalization;
- automated semantic validation;
- confidence calibration;
- larger regression test suites;
- configurable report templates;
- multi-topic PDF reports;
- integration with additional market-interest signals.