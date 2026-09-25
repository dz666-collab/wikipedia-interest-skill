import argparse
import json

from wikipedia import resolve_article, fetch_pageviews
from metrics import calculate_basic_metrics
from charts import generate_interest_chart


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

        results.append(
            {
                "language": language,
                "article": article,
                "metrics": metrics,
                "series": series,
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
    """
    Parse values like:
        pl=Głodówka lecznicza
        cs=Přerušovaný půst
    """
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

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()