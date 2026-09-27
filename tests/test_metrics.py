from datetime import date

import pytest

from scripts.metrics import calculate_basic_metrics


def make_items(values, start_year=2024, start_month=1):
    items = []

    year = start_year
    month = start_month

    for value in values:
        timestamp = date(
            year,
            month,
            1,
        ).strftime("%Y%m%d") + "00"

        items.append(
            {
                "timestamp": timestamp,
                "views": value,
            }
        )

        month += 1

        if month > 12:
            month = 1
            year += 1

    return items


def test_basic_metrics():
    items = make_items([
        100,
        200,
        300,
    ])

    result = calculate_basic_metrics(items)

    assert result["months"] == 3
    assert result["total_views"] == 600
    assert result["average_monthly_views"] == 200
    assert result["first_month_views"] == 100
    assert result["latest_month_views"] == 300
    assert result["growth_pct"] == 200


def test_growing_trend():
    items = make_items([
        100,
        120,
        140,
        160,
        180,
        200,
    ])

    result = calculate_basic_metrics(items)

    assert result["trend_label"] == "growing"


def test_declining_trend():
    items = make_items([
        200,
        180,
        160,
        140,
        120,
        100,
    ])

    result = calculate_basic_metrics(items)

    assert result["trend_label"] == "declining"


def test_flat_trend():
    items = make_items([
        100,
        100,
        100,
        100,
        100,
        100,
    ])

    result = calculate_basic_metrics(items)

    assert result["trend_label"] == "flat"
    assert result["spike_count"] == 0


def test_spike_detection():
    items = make_items([
        100,
        105,
        95,
        102,
        98,
        500,
    ])

    result = calculate_basic_metrics(items)

    assert result["spike_count"] == 1


def test_yoy_growth():
    values = [
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
    ]

    result = calculate_basic_metrics(
        make_items(values)
    )

    assert result["previous_12_month_views"] == 1200
    assert result["latest_12_month_views"] == 1800
    assert result["yoy_growth_pct"] == 50


def test_short_series_has_no_yoy():
    items = make_items([
        100,
        120,
        130,
    ])

    result = calculate_basic_metrics(items)

    assert result["yoy_growth_pct"] is None


def test_empty_input_raises_error():
    with pytest.raises(ValueError):
        calculate_basic_metrics([])