import argparse
import json

from wikipedia import resolve_article, fetch_pageviews
from metrics import calculate_basic_metrics


def analyze_topic(
    topic: str,
    languages: list[str],
    start: str,
    end: str,
) -> dict:
    results = []

    for language in languages:
        article = resolve_article(
            topic=topic,
            language=language,
        )

        if article["status"] != "resolved":
            results.append(
                {
                    "language": language,
                    "article": article,
                    "metrics": None,
                    "series": [],
                    "status": "unresolved",
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

    args = parser.parse_args()

    result = analyze_topic(
        topic=args.topic,
        languages=args.languages,
        start=args.start,
        end=args.end,
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()