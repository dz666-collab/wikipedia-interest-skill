from scripts.metrics import calculate_basic_metrics


def make_items(values):
    return [
        {
            "timestamp": f"2024{index + 1:02d}0100",
            "views": value,
        }
        for index, value in enumerate(values)
    ]


def test_basic_metrics():
    items = make_items([100, 200, 300])

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
    try:
        calculate_basic_metrics([])
        assert False
    except ValueError:
        assert True