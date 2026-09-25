from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


def _parse_timestamp(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, "%Y%m%d%H")


def _normalize_views(series: list[dict]) -> list[float]:
    """
    Normalize a time series so the first non-zero value equals 100.
    """
    baseline = None

    for item in series:
        if item["views"] > 0:
            baseline = item["views"]
            break

    if baseline is None:
        return [0.0 for _ in series]

    return [
        (item["views"] / baseline) * 100
        for item in series
    ]


def generate_interest_chart(
    analysis: dict,
    output_path: str = "interest_chart.png",
    mode: str = "absolute",
) -> str:
    """
    Generate a line chart from analysis output.

    mode:
        absolute   -> raw monthly pageviews
        normalized -> first non-zero month = 100
    """

    if mode not in {"absolute", "normalized"}:
        raise ValueError(
            "Chart mode must be 'absolute' or 'normalized'."
        )

    valid_results = [
        result
        for result in analysis["results"]
        if result["status"] == "ok" and result["series"]
    ]

    if not valid_results:
        raise ValueError(
            "No resolved time series available for charting."
        )

    plt.figure(figsize=(10, 5.5))

    for result in valid_results:
        dates = [
            _parse_timestamp(item["timestamp"])
            for item in result["series"]
        ]

        if mode == "absolute":
            values = [
                item["views"]
                for item in result["series"]
            ]
        else:
            values = _normalize_views(result["series"])

        language = result["language"]
        title = result["article"]["title"]

        plt.plot(
            dates,
            values,
            marker="o",
            markersize=3,
            linewidth=2,
            label=f"{language.upper()} — {title}",
        )

    topic = analysis["topic"]

    if mode == "absolute":
        plt.title(f'Wikipedia interest: "{topic}"')
        plt.ylabel("Monthly pageviews")
    else:
        plt.title(
            f'Wikipedia interest trend: "{topic}"'
        )
        plt.ylabel("Interest index (first month = 100)")

    plt.xlabel("Month")

    plt.grid(
        True,
        alpha=0.25,
    )

    plt.legend()
    plt.tight_layout()

    output = Path(output_path)

    if output.parent != Path("."):
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    plt.savefig(
        output,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close()

    return str(output)