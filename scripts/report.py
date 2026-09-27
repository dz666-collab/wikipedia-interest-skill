from datetime import datetime, date
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt


def _format_pct(value):
    if value is None:
        return "n/a"

    return f"{value:+.1f}%"


def _format_number(value):
    if value is None:
        return "n/a"

    return f"{round(value):,}"


def _format_period_date(value: str) -> str:
    """
    Convert YYYYMMDD to a human-readable month label.

    Monthly pageviews are analyzed, so showing exact days in the
    report would imply more temporal precision than the data provides.
    """
    try:
        parsed = datetime.strptime(value, "%Y%m%d")
        return parsed.strftime("%b %Y")
    except (TypeError, ValueError):
        return value or "unknown"


def _resolved_results(analysis: dict) -> list[dict]:
    return [
        item
        for item in analysis.get("results", [])
        if item.get("status") == "ok"
        and item.get("metrics") is not None
    ]


def _unresolved_results(analysis: dict) -> list[dict]:
    return [
        item
        for item in analysis.get("results", [])
        if item.get("status") != "ok"
    ]


def _build_findings(results: list[dict]) -> list[str]:
    findings = []

    for item in results[:3]:
        language = item["language"].upper()
        metrics = item["metrics"]

        findings.append(
            f"{language}: "
            f"{metrics['trend_label']} trend, "
            f"{_format_pct(metrics.get('yoy_growth_pct'))} YoY, "
            f"{metrics['confidence']} confidence."
        )

    return findings


def _build_confidence_note(results: list[dict]) -> str:
    notes = []

    for item in results[:3]:
        language = item["language"].upper()
        metrics = item["metrics"]

        reasons = metrics.get(
            "confidence_reasons",
            [],
        )

        if reasons:
            notes.append(
                f"{language}: "
                f"{metrics['confidence']} - "
                f"{reasons[0]}"
            )
        else:
            notes.append(
                f"{language}: "
                f"{metrics['confidence']} confidence."
            )

    return " ".join(notes)


def _build_assumption_note(analysis: dict) -> str:
    notes = []

    source_override_used = bool(
        analysis.get("source_article")
    )

    if source_override_used:
        notes.append(
            "A canonical English source article was explicitly selected "
            "to clarify the intended concept."
        )

    override_languages = []

    for item in analysis.get("results", []):
        article = item.get("article") or {}

        if article.get("resolution_method") == "explicit_override":
            override_languages.append(
                item["language"].upper()
            )

    if override_languages:
        languages = ", ".join(
            override_languages
        )

        notes.append(
            f"Proxy articles were explicitly selected for {languages}. "
            "They approximate the requested concept and may not represent "
            "exactly the same user intent."
        )

    if not notes:
        notes.append(
            "Article mappings were resolved through Wikipedia "
            "interlanguage links where available."
        )

    unresolved = _unresolved_results(
        analysis
    )

    if unresolved:
        unresolved_codes = ", ".join(
            item["language"].upper()
            for item in unresolved
        )

        notes.append(
            f"Unresolved language editions were excluded from the "
            f"quantitative comparison: {unresolved_codes}."
        )

    return " ".join(notes)


def _build_research_note(results: list[dict]) -> str:
    if len(results) == 1:
        return (
            "Use this trend as an attention signal for further research. "
            "It should not be treated as evidence of market demand, "
            "purchase intent, or willingness to pay."
        )

    return (
        "Use differences in trend direction and stability to prioritize "
        "follow-up research. Absolute Wikipedia traffic should not be "
        "used alone to rank markets."
    )


def generate_pdf_report(
    analysis: dict,
    output_path: str,
) -> str:
    """
    Generate a compact one-page PDF research report.
    """

    results = _resolved_results(
        analysis
    )

    if not results:
        raise ValueError(
            "Cannot generate report: no successfully resolved results."
        )

    path = Path(
        output_path
    )

    if path.parent != Path("."):
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    # A4 portrait
    fig = plt.figure(
        figsize=(8.27, 11.69),
    )

    # --------------------------------------------------
    # Header
    # --------------------------------------------------

    fig.suptitle(
        "Wikipedia Interest Analysis",
        fontsize=18,
        fontweight="bold",
        y=0.975,
    )

    topic = analysis.get(
        "topic",
        "Unknown topic",
    )

    start = _format_period_date(
        analysis.get("start", "")
    )

    end = _format_period_date(
        analysis.get("end", "")
    )

    months = max(
        (
            item["metrics"].get("months", 0)
            for item in results
        ),
        default=0,
    )

    fig.text(
        0.07,
        0.935,
        f"Topic: {topic}",
        fontsize=11.5,
        fontweight="bold",
    )

    fig.text(
        0.07,
        0.910,
        f"Period: {start} to {end} ({months} complete months)",
        fontsize=9.2,
    )

    # --------------------------------------------------
    # Summary table
    # --------------------------------------------------

    ax_table = fig.add_axes(
        [0.055, 0.715, 0.89, 0.15]
    )

    ax_table.axis(
        "off"
    )

    rows = []

    for item in results[:3]:
        article = item["article"]
        metrics = item["metrics"]

        rows.append(
            [
                item["language"].upper(),
                article["title"],
                metrics["trend_label"],
                _format_pct(
                    metrics.get(
                        "yoy_growth_pct"
                    )
                ),
                _format_number(
                    metrics.get(
                        "average_monthly_views"
                    )
                ),
                _format_number(
                    metrics.get(
                        "latest_month_views"
                    )
                ),
                metrics["confidence"],
            ]
        )

    table = ax_table.table(
        cellText=rows,
        colLabels=[
            "Lang",
            "Article",
            "Trend",
            "YoY",
            "Avg/mo",
            "Latest",
            "Confidence",
        ],
        colWidths=[
            0.07,
            0.27,
            0.13,
            0.11,
            0.12,
            0.12,
            0.13,
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        7.5
    )

    table.scale(
        1,
        1.55,
    )

    # --------------------------------------------------
    # Indexed trend chart
    # --------------------------------------------------

    ax_chart = fig.add_axes(
        [0.09, 0.445, 0.82, 0.225]
    )

    for item in results[:3]:
        series = item.get(
            "series",
            [],
        )

        if not series:
            continue

        views = [
            point["views"]
            for point in series
        ]

        baseline = next(
            (
                value
                for value in views
                if value > 0
            ),
            None,
        )

        if baseline is None:
            continue

        normalized = [
            value / baseline * 100
            for value in views
        ]

        labels = [
            point["timestamp"][:6]
            for point in series
        ]

        ax_chart.plot(
            labels,
            normalized,
            marker="o",
            markersize=2.1,
            linewidth=1.2,
            label=item["language"].upper(),
        )

    ax_chart.set_title(
        "Indexed monthly pageviews (first month = 100)",
        fontsize=9.4,
    )

    ax_chart.set_ylabel(
        "Index",
        fontsize=8,
    )

    ax_chart.tick_params(
        axis="both",
        labelsize=6.7,
    )

    for index, label in enumerate(
        ax_chart.get_xticklabels()
    ):
        if index % 3 != 0:
            label.set_visible(
                False
            )
        else:
            label.set_rotation(
                45
            )

    ax_chart.legend(
        fontsize=7.2,
        loc="best",
    )

    ax_chart.grid(
        alpha=0.2,
    )

    # --------------------------------------------------
    # Key findings
    # --------------------------------------------------

    fig.text(
        0.07,
        0.395,
        "Key findings",
        fontsize=10.3,
        fontweight="bold",
    )

    findings = _build_findings(
        results
    )

    y = 0.372

    for finding in findings:
        fig.text(
            0.09,
            y,
            f"- {finding}",
            fontsize=8.1,
        )

        y -= 0.021

    # --------------------------------------------------
    # Confidence
    # --------------------------------------------------

    fig.text(
        0.07,
        0.295,
        "Confidence",
        fontsize=10.3,
        fontweight="bold",
    )

    confidence_note = _build_confidence_note(
        results
    )

    fig.text(
        0.09,
        0.272,
        fill(
            confidence_note,
            width=108,
        ),
        fontsize=7.8,
        va="top",
    )

    # --------------------------------------------------
    # Assumptions
    # --------------------------------------------------

    fig.text(
        0.07,
        0.218,
        "Assumptions / interpretation",
        fontsize=10.3,
        fontweight="bold",
    )

    assumption = _build_assumption_note(
        analysis
    )

    fig.text(
        0.09,
        0.195,
        fill(
            assumption,
            width=108,
        ),
        fontsize=7.6,
        va="top",
    )

    # --------------------------------------------------
    # Research implication
    # --------------------------------------------------

    fig.text(
        0.07,
        0.140,
        "Research implication",
        fontsize=10.3,
        fontweight="bold",
    )

    research_note = _build_research_note(
        results
    )

    fig.text(
        0.09,
        0.117,
        fill(
            research_note,
            width=108,
        ),
        fontsize=7.6,
        va="top",
    )

    # --------------------------------------------------
    # Limitations
    # --------------------------------------------------

    fig.text(
        0.07,
        0.074,
        "Limitations",
        fontsize=10.3,
        fontweight="bold",
    )

    limitation_text = (
        "Wikipedia pageviews measure attention, not market size, "
        "purchase intent, or willingness to pay. Traffic can be "
        "affected by seasonality, news, education cycles, and temporary "
        "spikes. Absolute traffic across language editions should not "
        "be interpreted as directly comparable market size."
    )

    fig.text(
        0.09,
        0.052,
        fill(
            limitation_text,
            width=108,
        ),
        fontsize=7.0,
        va="top",
    )

    # --------------------------------------------------
    # Footer
    # --------------------------------------------------

    generated = date.today().isoformat()

    fig.text(
        0.07,
        0.010,
        (
            f"Source: Wikimedia Pageviews API | Generated: {generated} | "
            "Confidence is a transparent heuristic, not a statistical "
            "confidence interval."
        ),
        fontsize=6.0,
    )

    fig.savefig(
        path,
        format="pdf",
    )

    plt.close(
        fig
    )

    return str(
        path
    )