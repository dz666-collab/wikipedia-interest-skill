import argparse
import json
from pathlib import Path

from wikipedia import resolve_article, fetch_pageviews
from metrics import calculate_basic_metrics
from charts import generate_interest_chart
from forecast import linear_forecast
from summary import build_summary


def analyze_topic(
    topic: str,
    languages: list[str],
    start: str,
    end: str,
    article_overrides: dict[str, str] | None = None,
) -> dict:
    results = []
    article_overrides = article_overrides or {}

    for language in languages:
        article = resolve_article(
            topic=topic,
            language=language,
            article_override=article_overrides.get(language),
        )

        if article["status"] != "resolved":
            results.append(
                {
                    "language": language,
                    "article": article,
                    "metrics": None,
                    "series": [],
                    "forecast": None,
                    "summary": None,
                    "status": article["status"],
                }
            )
            continue

        pageviews = fetch_pageviews(
            article_title=article["title"],
            language=language,
            start=start,
            end=end,
        )

        metrics = calculate_basic_metrics(pageviews)

        series = [
            {
                "timestamp": item["timestamp"],
                "views": item["views"],
            }
            for item in pageviews
        ]

        forecast = linear_forecast(
            series=pageviews,
            months_ahead=3,
            lookback_months=12,
        )

        summary = build_summary(
            language=language,
            article=article,
            metrics=metrics,
            forecast=forecast,
        )

        results.append(
            {
                "language": language,
                "article": article,
                "metrics": metrics,
                "series": series,
                "forecast": forecast,
                "summary": summary,
                "status": "ok",
            }
        )

    return {
        "topic": topic,
        "start": start,
        "end": end,
        "results": results,
    }


def parse_article_overrides(
    values: list[str] | None,
) -> dict[str, str]:
    if not values:
        return {}

    overrides = {}

    for value in values:
        if "=" not in value:
            raise ValueError(
                "Article override must use LANGUAGE=TITLE format."
            )

        language, title = value.split("=", 1)

        language = language.strip()
        title = title.strip()

        if not language or not title:
            raise ValueError(
                "Article override must use LANGUAGE=TITLE format."
            )

        overrides[language] = title

    return overrides


def save_json(
    data: dict,
    output_path: str,
) -> str:
    path = Path(output_path)

    if path.parent != Path("."):
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return str(path)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Wikipedia interest for a topic."
    )

    parser.add_argument(
        "--topic",
        required=True,
        help="Topic to analyze.",
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        required=True,
        help="Wikipedia language codes, e.g. cs uk pl.",
    )

    parser.add_argument(
        "--start",
        required=True,
        help="Start date in YYYYMMDD format.",
    )

    parser.add_argument(
        "--end",
        required=True,
        help="End date in YYYYMMDD format.",
    )

    parser.add_argument(
        "--article-override",
        action="append",
        help=(
            "Explicit article mapping in LANGUAGE=TITLE format. "
            "Can be provided multiple times."
        ),
    )

    parser.add_argument(
        "--chart",
        help="Optional path for PNG chart output.",
    )

    parser.add_argument(
        "--chart-mode",
        choices=["absolute", "normalized"],
        default="absolute",
        help="Chart mode: raw pageviews or normalized trend.",
    )

    parser.add_argument(
        "--output",
        help="Optional path for JSON analysis output.",
    )

    args = parser.parse_args()

    article_overrides = parse_article_overrides(
        args.article_override
    )

    result = analyze_topic(
        topic=args.topic,
        languages=args.languages,
        start=args.start,
        end=args.end,
        article_overrides=article_overrides,
    )

    if args.chart:
        chart_path = generate_interest_chart(
            analysis=result,
            output_path=args.chart,
            mode=args.chart_mode,
        )

        result["chart"] = {
            "path": chart_path,
            "mode": args.chart_mode,
        }

    if args.output:
        output_path = save_json(
            data=result,
            output_path=args.output,
        )

        result["output"] = output_path

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()