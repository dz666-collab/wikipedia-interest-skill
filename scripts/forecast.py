from typing import List, Dict


def linear_forecast(
    series: List[Dict],
    months_ahead: int = 3,
    lookback_months: int = 12,
) -> dict:
    """
    Simple linear trend forecast.

    Uses the latest `lookback_months` observations and projects
    the linear trend forward for `months_ahead` periods.

    This is intended as a lightweight directional forecast,
    not a production forecasting model.
    """

    if not series:
        raise ValueError("No time series data provided.")

    if months_ahead < 1:
        raise ValueError("months_ahead must be at least 1.")

    values = [item["views"] for item in series]

    if len(values) < 2:
        raise ValueError(
            "At least 2 observations are required for forecasting."
        )

    lookback = min(
        lookback_months,
        len(values),
    )

    recent_values = values[-lookback:]

    n = len(recent_values)
    x = list(range(n))

    mean_x = sum(x) / n
    mean_y = sum(recent_values) / n

    numerator = sum(
        (xi - mean_x) * (yi - mean_y)
        for xi, yi in zip(x, recent_values)
    )

    denominator = sum(
        (xi - mean_x) ** 2
        for xi in x
    )

    if denominator == 0:
        slope = 0.0
    else:
        slope = numerator / denominator

    intercept = mean_y - slope * mean_x

    forecast_values = []

    for step in range(1, months_ahead + 1):
        x_future = n - 1 + step
        predicted = intercept + slope * x_future

        forecast_values.append(
            max(0, round(predicted))
        )

    return {
        "method": "linear_trend",
        "lookback_months": lookback,
        "months_ahead": months_ahead,
        "slope": slope,
        "forecast_views": forecast_values,
        "experimental": True,
        "warning": (
            "Directional projection only. "
            "Wikipedia traffic can be affected by seasonality, "
            "news events, and short-term spikes."
        ),
    }