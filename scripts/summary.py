def build_summary(
    language: str,
    article: dict,
    metrics: dict,
    forecast: dict | None,
) -> dict:
    """
    Build a concise, report-ready summary from analysis metrics.
    """

    yoy_growth = metrics.get("yoy_growth_pct")
    trend = metrics.get("trend_label")
    confidence = metrics.get("confidence")
    spike_count = metrics.get("spike_count", 0)
    volatility = metrics.get("coefficient_of_variation")

    key_points = []

    if yoy_growth is not None:
        direction = "increased" if yoy_growth > 0 else "decreased"

        key_points.append(
            f"Pageviews {direction} by "
            f"{abs(yoy_growth):.1f}% year over year."
        )

    if trend:
        key_points.append(
            f"The overall trend is {trend}."
        )

    if volatility is not None:
        if volatility < 0.5:
            volatility_label = "low"
        elif volatility < 0.8:
            volatility_label = "moderate"
        else:
            volatility_label = "high"

        key_points.append(
            f"Monthly traffic volatility is {volatility_label}."
        )

    if spike_count == 0:
        key_points.append(
            "No major traffic spikes were detected."
        )
    elif spike_count == 1:
        key_points.append(
            "One major traffic spike was detected."
        )
    else:
        key_points.append(
            f"{spike_count} major traffic spikes were detected."
        )

    if forecast is not None:
        forecast_values = forecast.get("forecast_views", [])

        if forecast_values:
            key_points.append(
                "The experimental short-term projection is "
                f"{forecast_values[-1]} monthly views "
                f"after {forecast['months_ahead']} months."
            )

    limitations = [
        (
            "Wikipedia pageviews measure attention to Wikipedia content, "
            "not market size, purchase intent, or willingness to pay."
        ),
        (
            "Traffic may be influenced by seasonality, news events, "
            "education cycles, or temporary spikes."
        ),
        (
            "Cross-language absolute pageview levels should not be treated "
            "as directly comparable market sizes."
        ),
    ]

    return {
        "language": language,
        "article_title": article["title"],
        "trend": trend,
        "confidence": confidence,
        "yoy_growth_pct": yoy_growth,
        "key_points": key_points,
        "confidence_reasons": metrics.get(
            "confidence_reasons",
            [],
        ),
        "limitations": limitations,
    }