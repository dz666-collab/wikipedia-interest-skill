import argparse
import calendar
import json
from datetime import date
from pathlib import Path

from wikipedia import resolve_article, fetch_pageviews
from metrics import calculate_basic_metrics
from charts import generate_interest_chart
from forecast import linear_forecast
from summary import build_summary
from report import generate_pdf_report


def analyze_topic(
    topic: str,
    languages: list[str],
    start: str,
    end: str,
    article_overrides: dict[str, str] | None = None,
    source_article: str | None = None,
) -> dict:
    results = []
    article_overrides = article_overrides or {}

    for language in languages:
        article = resolve_article(
            topic=topic,
            language=language,
            article_override=article_overrides.get(language),
            source_article=source_article,
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

        metrics = calculate_basic_metrics(
            pageviews
        )

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
        "source_article": source_article,
        "start": start,
        "end": end,
        "results": results,
    }


def parse_article_overrides(
    values: list[str] | None,
) -> dict[str, str]:
    """
    Parse explicit target-language mappings such as:

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

        language, title = value.split(
            "=",
            1,
        )

        language = language.strip()
        title = title.strip()

        if not language or not title:
            raise ValueError(
                "Article override must use LANGUAGE=TITLE format."
            )

        overrides[language] = title

    return overrides


def resolve_date_range(
    start: str | None,
    end: str | None,
    months: int | None,
) -> tuple[str, str]:
    """
    Resolve the analysis period.

    When --months is supplied, analyze the latest N complete
    calendar months and exclude the current incomplete month.

    Otherwise both --start and --end must be supplied.
    """

    if months is not None:
        if months < 1:
            raise ValueError(
                "--months must be at least 1."
            )

        today = date.today()

        if today.month == 1:
            end_year = today.year - 1
            end_month = 12
        else:
            end_year = today.year
            end_month = today.month - 1

        end_day = calendar.monthrange(
            end_year,
            end_month,
        )[1]

        end_date = date(
            end_year,
            end_month,
            end_day,
        )

        start_month_index = (
            end_year * 12
            + end_month
            - months
        )

        start_year = (
            start_month_index // 12
        )

        start_month = (
            start_month_index % 12
            + 1
        )

        start_date = date(
            start_year,
            start_month,
            1,
        )

        return (
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d"),
        )

    if not start or not end:
        raise ValueError(
            "Provide either --months or both --start and --end."
        )

    return start, end


def save_json(
    data: dict,
    output_path: str,
) -> str:
    path = Path(
        output_path
    )

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

    return str(
        path
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Analyze Wikipedia pageview interest "
            "for a topic across language editions."
        )
    )

    parser.add_argument(
        "--topic",
        required=True,
        help=(
            "User topic to analyze."
        ),
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        required=True,
        help=(
            "Wikipedia language codes, "
            "for example: uk pl cs."
        ),
    )

    parser.add_argument(
        "--source-article",
        help=(
            "Explicit canonical English Wikipedia article. "
            "Use this when the user's topic is ambiguous or "
            "resolves to the wrong English concept."
        ),
    )

    parser.add_argument(
        "--start",
        help=(
            "Start date in YYYYMMDD format."
        ),
    )

    parser.add_argument(
        "--end",
        help=(
            "End date in YYYYMMDD format."
        ),
    )

    parser.add_argument(
        "--months",
        type=int,
        help=(
            "Analyze the latest N complete calendar months. "
            "If supplied, it takes precedence over --start and --end."
        ),
    )

    parser.add_argument(
        "--article-override",
        action="append",
        help=(
            "Explicit target-language article mapping using "
            "LANGUAGE=TITLE. Can be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--chart",
        help=(
            "Optional path for PNG chart output."
        ),
    )

    parser.add_argument(
        "--chart-mode",
        choices=[
            "absolute",
            "normalized",
        ],
        default="absolute",
        help=(
            "Chart mode: absolute uses raw monthly pageviews; "
            "normalized compares relative change from a "
            "common baseline of 100."
        ),
    )

    parser.add_argument(
        "--report",
        help=(
            "Optional path for one-page PDF report."
        ),
    )

    parser.add_argument(
        "--output",
        help=(
            "Optional path for JSON analysis output."
        ),
    )

    args = parser.parse_args()

    article_overrides = parse_article_overrides(
        args.article_override
    )

    start, end = resolve_date_range(
        start=args.start,
        end=args.end,
        months=args.months,
    )

    result = analyze_topic(
        topic=args.topic,
        languages=args.languages,
        start=start,
        end=end,
        article_overrides=article_overrides,
        source_article=args.source_article,
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

    if args.report:
        report_path = generate_pdf_report(
            analysis=result,
            output_path=args.report,
        )

        result["report"] = {
            "path": report_path,
            "format": "pdf",
        }

    if args.output:
        result["output"] = args.output

        save_json(
            data=result,
            output_path=args.output,
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