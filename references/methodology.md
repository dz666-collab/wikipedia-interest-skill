# Methodology

This document explains the analytical choices used by the Wikipedia Interest Skill.

## Data source

The skill uses Wikimedia pageview data from the Wikimedia Analytics API.

Monthly pageviews are fetched per article and per Wikipedia language edition.

The default analysis uses `all-access` and `user` traffic.

Wikipedia pageviews are treated as a signal of attention to Wikipedia content.

They should not be interpreted as direct evidence of:

- market size;
- purchase intent;
- willingness to pay;
- product demand;
- commercial opportunity.

## Topic and article resolution

The most important prerequisite is semantic comparability.

The normal resolution process is:

1. Resolve the user's topic to an English Wikipedia article.
2. Treat that article as the source concept.
3. Resolve target-language equivalents using Wikipedia interlanguage links.
4. If an equivalent article cannot be found, return `needs_review`.
5. Show local candidates for human or agent review.

The skill intentionally avoids automatically selecting the first local search result.

A loosely related article can create misleading cross-language comparisons.

Some concepts do not have exact equivalents in all target-language Wikipedia editions.

This is a normal property of multilingual Wikipedia and must be treated as a semantic limitation rather than silently corrected by choosing a loosely related page.

## Explicit source article

If the user's wording is ambiguous or resolves to the wrong English Wikipedia concept, an explicit canonical source article can be supplied.

Example:

```bash
--source-article "English as a second or foreign language"
```

This is used to clarify the intended concept before target-language resolution.

The source article should be chosen because it represents the user's intended concept, not merely because it produces more interlanguage matches.

## Explicit article proxies

Some concepts do not have exact equivalents in all target-language Wikipedia editions.

In those cases, an explicit target-language article can be supplied using:

```bash
--article-override "LANGUAGE=ARTICLE TITLE"
```

Overrides must be treated as explicit assumptions.

A proxy article should never be presented as an exact semantic equivalent unless it actually is one.

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

In this example, the selected language articles are proxies for broader interest in English.

They do not isolate the intent of learning English.

That distinction should be disclosed in interpretation and in any generated report.

## Resolution status

A language result may be returned as:

```text
resolved
```

or:

```text
needs_review
```

A `needs_review` state is intentional.

It means that the skill could not confirm an equivalent target-language article through interlanguage links.

The skill may return local search candidates to support review.

Candidate pages are not automatically treated as equivalent.

This prevents incorrect cross-language comparisons caused by superficial keyword matches.

## Time periods

For recent trend analysis, the recommended default is the latest 24 complete calendar months.

The current incomplete month is excluded.

A 24-month window provides:

- two complete 12-month periods;
- year-over-year comparison;
- enough history to estimate broad trend direction;
- a useful balance between recency and stability.

For reproducibility, explicit `--start` and `--end` dates can also be supplied.

Example:

```bash
--start 20240101 --end 20251231
```

When monthly pageview data is used, complete calendar months are preferred.

The user-facing PDF displays periods at month precision, for example:

```text
Sep 2024 to Aug 2026
```

rather than implying unnecessary day-level analytical precision.

The raw JSON retains the exact API request boundaries for reproducibility.

## Core metrics

### Total views

Sum of pageviews across the analysis period.

This provides overall traffic volume for the selected article and period.

### Average monthly views

Mean monthly pageviews across the selected period.

This is useful for understanding the approximate traffic scale within one Wikipedia edition.

Absolute values across different language editions should be interpreted cautiously.

### Latest monthly views

Pageviews in the latest complete month.

This provides recent context alongside longer-period metrics.

It should not be interpreted alone because one month may be affected by seasonality or temporary events.

### First-to-last change

The percentage change from the first observed month to the latest observed month.

Formula:

```text
(latest_month_views - first_month_views)
----------------------------------------- × 100
           first_month_views
```

This metric is descriptive but can be highly sensitive to unusual first or last months.

It should not be used alone as the main growth measure.

### Year-over-year growth

For at least 24 months of data, the skill compares:

- the previous 12 complete months;
- the latest 12 complete months.

Formula:

```text
(latest_12_month_views - previous_12_month_views)
------------------------------------------------- × 100
             previous_12_month_views
```

This reduces sensitivity to one individual month and is preferred over first-to-last change for broad recent growth comparisons.

A positive value indicates that the latest 12-month period received more pageviews than the preceding 12-month period.

A negative value indicates fewer pageviews.

## Trend direction

The skill fits a simple linear trend over monthly pageviews.

Monthly observations are treated as equally spaced points in time.

The slope is normalized by average monthly traffic.

The result is used to classify the overall trend as:

- `growing`;
- `flat`;
- `declining`.

The current heuristic uses the normalized slope to classify direction.

This is intended as a simple, explainable directional indicator.

It is not a seasonal model and should not be interpreted as a formal causal or forecasting model.

## Volatility

Monthly volatility is measured using the standard deviation of monthly pageviews.

The coefficient of variation is:

```text
standard deviation / mean monthly views
```

This makes volatility more interpretable across topics with different traffic scales.

The current heuristic interprets volatility approximately as:

- below 0.5: relatively stable;
- 0.5 to below 0.8: moderate volatility;
- 0.8 or above: high volatility.

These thresholds are transparent heuristics.

They are not statistically calibrated confidence boundaries.

## Spike detection

The skill performs simple spike detection using standardized deviation from the mean.

A month may be flagged as a major spike if its z-score is sufficiently high.

The current implementation uses a simple threshold-based approach.

Spike detection helps avoid treating temporary bursts of attention as sustained growth.

Possible causes of spikes include:

- news events;
- public controversies;
- school or university activity;
- media releases;
- sudden external linking;
- temporary viral interest.

The current approach is intentionally simple.

Future versions could use more robust techniques such as:

- median absolute deviation;
- rolling baselines;
- seasonal decomposition;
- event-aware anomaly detection.

## Confidence

Confidence is a transparent heuristic, not a statistical confidence interval.

The skill considers:

- amount of available history;
- traffic volatility;
- number of major spikes;
- consistency between year-over-year change and overall trend direction.

The purpose of the confidence label is to communicate how stable and internally consistent the observed signal appears.

It is not a probability that a conclusion is correct.

### High confidence

Usually indicates:

- sufficient historical coverage;
- relatively stable traffic;
- few major spikes;
- agreement between long-term trend direction and year-over-year change.

### Medium confidence

Usually indicates:

- moderate volatility;
- one or more anomalies;
- broadly consistent directional evidence.

### Low confidence

Usually indicates one or more of:

- high volatility;
- limited history;
- unstable traffic;
- strong anomalies;
- inconsistent directional indicators.

Confidence reasons are included in the structured output.

User-facing reports should explain the reason rather than presenting only the label.

For example:

```text
Low confidence because monthly traffic is highly volatile.
```

is more useful than:

```text
Confidence: low
```

without explanation.

## Indexed charts

For cross-language trend comparisons, the skill can create an indexed chart.

The first non-zero month for each series is assigned:

```text
100
```

Subsequent values show relative change from that baseline.

For example:

```text
100 → 120
```

means the monthly pageview count is 20% above that series' starting baseline.

This is useful for comparing trend shapes across language editions with very different raw traffic levels.

It is not normalization by:

- population;
- number of Wikipedia users;
- total Wikipedia edition traffic;
- number of speakers;
- market size.

An indexed chart should therefore be described as:

```text
Indexed monthly pageviews (first month = 100)
```

rather than as normalized market interest.

## Absolute charts

Absolute charts show raw monthly pageview counts.

They are useful for understanding scale within a language edition.

However, raw traffic across different Wikipedia editions should not be treated as directly comparable market size.

Different editions can have different:

- audience sizes;
- usage patterns;
- content coverage;
- article quality;
- internal linking behavior;
- search-engine visibility;
- proportions of native and non-native readers.

For market-oriented research, trend direction and stability are usually safer comparison signals than raw cross-language totals.

## Cross-language comparisons

Cross-language comparison requires semantic validation before numerical comparison.

The recommended sequence is:

1. Confirm that the articles represent the same concept.
2. Identify any missing exact equivalents.
3. Use explicit proxies only when justified.
4. Record proxy assumptions.
5. Compare relative trends.
6. Interpret raw traffic cautiously.
7. Explain confidence and anomalies.

The skill should not rank markets purely by absolute Wikipedia pageviews.

A larger Wikipedia article audience does not necessarily imply a larger commercial market.

## One-page PDF report

The PDF report is intentionally compact.

It includes:

- topic;
- analysis period;
- language and article mappings;
- trend direction;
- year-over-year change;
- average monthly views;
- latest monthly views;
- confidence;
- indexed chart;
- key findings;
- confidence explanation;
- assumptions;
- research implication;
- limitations;
- generation date;
- Wikimedia source.

The report is intended as a shareable research artifact rather than a full statistical report.

The PDF deliberately avoids displaying every internal metric.

More detailed values remain available in the structured JSON output.

## Research interpretation

The skill should distinguish clearly between:

```text
observed Wikipedia attention
```

and:

```text
commercial demand
```

Reasonable interpretations include:

> Wikipedia attention to this topic declined year over year.

> The decline appears relatively stable across the observed period.

> The signal has low confidence because traffic is highly volatile.

> This language edition may warrant further research because its trend differs from the others.

Unsupported interpretations include:

> The market is shrinking.

> Consumers are no longer interested in this product category.

> Users are willing to pay more in this country.

Wikipedia pageviews alone cannot support those claims.

## Research implication

For B2C or product-discovery workflows, Wikipedia analysis should be treated as an early research signal.

It can help:

- identify topics with changing attention;
- compare relative trend direction;
- identify unusual language-edition behavior;
- prioritize areas for follow-up research;
- generate hypotheses.

Follow-up research may include:

- search trend data;
- app-store data;
- social media activity;
- market reports;
- survey data;
- competitor analysis;
- product usage data.

Wikipedia pageviews should be one input among multiple signals.

## Forecast

The skill includes an experimental short-term linear forecast in structured output.

The forecast:

- uses recent monthly history;
- extends a simple linear trend;
- is directional only;
- is not included as primary evidence in the PDF summary;
- is not used to calculate confidence.

It should not be presented as a prediction of:

- market demand;
- future sales;
- product adoption;
- future Wikipedia traffic with statistical certainty.

Forecast quality can be especially poor when:

- traffic is seasonal;
- recent spikes occurred;
- the underlying trend is nonlinear;
- the recent baseline is unusual.

For this reason, forecast output is explicitly marked as experimental.

## Caching

API responses are cached locally.

Caching improves:

- repeated-query speed;
- reproducibility during iteration;
- Wikimedia API efficiency;
- low-cost agent workflows where repeated API calls would otherwise be unnecessary.

Cached data can become stale if Wikipedia mappings or historical records change.

For production use, cache expiration or invalidation rules should be added.

The current local cache is appropriate for development and small research workflows.

## Reproducibility

The skill attempts to make analysis reproducible by retaining:

- exact article titles;
- Wikipedia language codes;
- explicit date boundaries;
- structured monthly time series;
- calculated metrics;
- resolution status;
- proxy assumptions;
- output files.

For recent analysis using:

```bash
--months 24
```

the exact date range changes over time because the command always selects the latest 24 complete months.

For a permanently reproducible historical result, use explicit:

```bash
--start
```

and:

```bash
--end
```

values.

## Known limitations

The current implementation intentionally favors simplicity, transparency, and agent usability.

Known limitations include:

- basic English search may still require semantic review for ambiguous topics;
- some concepts do not have exact equivalents in all target-language Wikipedia editions;
- confidence is heuristic rather than statistically calibrated;
- spike detection is simple;
- trend estimation does not explicitly model seasonality;
- cross-language pageviews are not normalized for total Wikipedia edition activity;
- proxy article selection may require agent or user judgment;
- forecasting is experimental;
- large-scale workloads are processed sequentially;
- local cache invalidation is basic;
- Wikipedia attention is not equivalent to market demand.

These limitations should be disclosed rather than hidden.

## Failure behavior

The skill prefers explicit uncertainty over silent substitution.

If an exact interlanguage article is unavailable:

```text
needs_review
```

is returned.

If valid pageview data cannot be obtained, the analysis should not invent values.

If article mappings are ambiguous, the agent should clarify the concept or use an explicit reviewed override.

This conservative behavior is intentional.

## Future scaling

For larger research workflows, possible improvements include:

- concurrent Wikimedia API requests;
- retry logic with exponential backoff;
- persistent or shared caching;
- configurable cache expiration;
- batch topic processing;
- robust outlier detection;
- seasonal decomposition;
- normalization relative to total Wikipedia edition traffic;
- semantic similarity checks for article mappings;
- confidence calibration against labeled examples;
- benchmark datasets for regression testing;
- automated acceptance tests for article-resolution edge cases;
- configurable PDF templates;
- multi-topic research reports;
- additional external interest signals;
- data pipelines for larger historical datasets.

The current implementation is designed to remain understandable, reproducible, and usable by a fast, low-cost tool-capable agent.