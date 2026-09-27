import statistics


def _linear_trend_slope(values: list[int]) -> float:
    n = len(values)

    if n < 2:
        return 0.0

    x = list(range(n))

    mean_x = sum(x) / n
    mean_y = sum(values) / n

    numerator = sum(
        (xi - mean_x) * (yi - mean_y)
        for xi, yi in zip(x, values)
    )

    denominator = sum(
        (xi - mean_x) ** 2
        for xi in x
    )

    if denominator == 0:
        return 0.0

    return numerator / denominator


def _detect_spikes(values: list[int]) -> list[int]:
    if len(values) < 3:
        return []

    mean = statistics.mean(values)
    stdev = statistics.stdev(values)

    if stdev == 0:
        return []

    spike_indexes = []

    for index, value in enumerate(values):
        z_score = (value - mean) / stdev

        if z_score >= 2.0:
            spike_indexes.append(index)

    return spike_indexes


def _assess_confidence(metrics: dict) -> tuple[str, list[str]]:
    reasons = []

    months = metrics["months"]
    cv = metrics["coefficient_of_variation"]
    spike_count = metrics["spike_count"]
    trend_label = metrics["trend_label"]
    yoy_growth_pct = metrics["yoy_growth_pct"]

    if months < 12:
        reasons.append("Short time series with fewer than 12 months.")
        return "low", reasons

    if months < 18:
        reasons.append("Limited historical coverage.")

    if cv is not None:
        if cv < 0.5:
            reasons.append("Monthly traffic is relatively stable.")
        elif cv < 0.8:
            reasons.append("Monthly traffic shows moderate volatility.")
        else:
            reasons.append("Monthly traffic is highly volatile.")

    if spike_count == 0:
        reasons.append("No major traffic spikes detected.")
    elif spike_count == 1:
        reasons.append("One major traffic spike detected.")
    else:
        reasons.append("Multiple major traffic spikes detected.")

    trend_consistent = False

    if yoy_growth_pct is not None:
        if trend_label == "growing" and yoy_growth_pct > 0:
            trend_consistent = True
        elif trend_label == "declining" and yoy_growth_pct < 0:
            trend_consistent = True
        elif trend_label == "flat" and abs(yoy_growth_pct) < 10:
            trend_consistent = True

    if trend_consistent:
        reasons.append(
            "Long-term trend direction is consistent with year-over-year change."
        )
    else:
        reasons.append(
            "Trend indicators are mixed or insufficient for a strong conclusion."
        )

    if (
        months >= 18
        and cv is not None
        and cv < 0.5
        and spike_count <= 1
        and trend_consistent
    ):
        confidence = "high"

    elif (
        months >= 12
        and cv is not None
        and cv < 0.8
        and spike_count <= 2
        and trend_consistent
    ):
        confidence = "medium"

    else:
        confidence = "low"

    return confidence, reasons


def calculate_basic_metrics(items: list[dict]) -> dict:
    if not items:
        raise ValueError("No pageview data provided.")

    views = [item["views"] for item in items]

    first = views[0]
    last = views[-1]

    if first == 0:
        growth_pct = None
    else:
        growth_pct = ((last - first) / first) * 100

    mean_views = statistics.mean(views)

    if len(views) > 1:
        stdev_views = statistics.stdev(views)
    else:
        stdev_views = 0.0

    if mean_views == 0:
        coefficient_of_variation = None
    else:
        coefficient_of_variation = stdev_views / mean_views

    trend_slope = _linear_trend_slope(views)

    if mean_views == 0:
        normalized_trend_pct = 0.0
    else:
        normalized_trend_pct = (
            trend_slope / mean_views
        ) * 100

    if normalized_trend_pct > 1:
        trend_label = "growing"
    elif normalized_trend_pct < -1:
        trend_label = "declining"
    else:
        trend_label = "flat"

    spike_indexes = _detect_spikes(views)

    spike_months = [
        items[index]["timestamp"]
        for index in spike_indexes
    ]

    metrics = {
        "months": len(views),
        "total_views": sum(views),
        "average_monthly_views": mean_views,
        "first_month_views": first,
        "latest_month_views": last,
        "growth_pct": growth_pct,
        "min_month_views": min(views),
        "max_month_views": max(views),
        "volatility_std": stdev_views,
        "coefficient_of_variation": coefficient_of_variation,
        "trend_slope": trend_slope,
        "normalized_trend_pct": normalized_trend_pct,
        "trend_label": trend_label,
        "spike_count": len(spike_indexes),
        "spike_months": spike_months,
    }

    if len(views) >= 24:
        previous_12 = views[-24:-12]
        latest_12 = views[-12:]

        previous_total = sum(previous_12)
        latest_total = sum(latest_12)

        if previous_total == 0:
            yoy_growth_pct = None
        else:
            yoy_growth_pct = (
                (latest_total - previous_total)
                / previous_total
            ) * 100

        metrics["previous_12_month_views"] = previous_total
        metrics["latest_12_month_views"] = latest_total
        metrics["yoy_growth_pct"] = yoy_growth_pct
    else:
        metrics["yoy_growth_pct"] = None

    confidence, confidence_reasons = _assess_confidence(metrics)

    metrics["confidence"] = confidence
    metrics["confidence_reasons"] = confidence_reasons

    return metrics