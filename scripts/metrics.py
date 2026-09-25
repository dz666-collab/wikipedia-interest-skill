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

    metrics = {
        "months": len(views),
        "total_views": sum(views),
        "average_monthly_views": sum(views) / len(views),
        "first_month_views": first,
        "latest_month_views": last,
        "growth_pct": growth_pct,
        "min_month_views": min(views),
        "max_month_views": max(views),
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

    return metrics