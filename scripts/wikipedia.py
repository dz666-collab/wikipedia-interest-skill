import httpx
from metrics import calculate_basic_metrics

USER_AGENT = "WikipediaInterestSkill/0.1 (contact: dz546838@gmail.com)"


def search_english_article(topic: str) -> dict:
    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": topic,
        "format": "json",
        "utf8": 1,
        "srlimit": 5,
    }

    headers = {
        "User-Agent": USER_AGENT,
    }

    response = httpx.get(
        url,
        params=params,
        headers=headers,
        timeout=20.0,
    )
    response.raise_for_status()

    data = response.json()
    results = data["query"]["search"]

    if not results:
        raise ValueError(
            f"No English Wikipedia article found for topic '{topic}'"
        )

    best_match = results[0]

    return {
        "pageid": best_match["pageid"],
        "title": best_match["title"],
    }


def get_interlanguage_title(
    english_title: str,
    target_language: str,
) -> str | None:
    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "prop": "langlinks",
        "titles": english_title,
        "lllang": target_language,
        "lllimit": "max",
        "format": "json",
    }

    headers = {
        "User-Agent": USER_AGENT,
    }

    response = httpx.get(
        url,
        params=params,
        headers=headers,
        timeout=20.0,
    )
    response.raise_for_status()

    data = response.json()
    pages = data["query"]["pages"]

    page = next(iter(pages.values()))
    langlinks = page.get("langlinks", [])

    if not langlinks:
        return None

    return langlinks[0]["*"]


def resolve_article(topic: str, language: str) -> dict:
    """
    Resolve a topic through the English Wikipedia article
    and its interlanguage link.

    If no target-language article exists, return an explicit
    unresolved result instead of guessing from local search.
    """

    english_article = search_english_article(topic)

    # English requires no interlanguage lookup.
    if language == "en":
        return {
            "topic": topic,
            "source_language": "en",
            "source_title": english_article["title"],
            "language": "en",
            "title": english_article["title"],
            "url": (
                "https://en.wikipedia.org/wiki/"
                + english_article["title"].replace(" ", "_")
            ),
            "resolution_method": "english_search",
            "status": "resolved",
        }

    target_title = get_interlanguage_title(
        english_title=english_article["title"],
        target_language=language,
    )

    if target_title is None:
        return {
            "topic": topic,
            "source_language": "en",
            "source_title": english_article["title"],
            "language": language,
            "title": None,
            "url": None,
            "resolution_method": "interlanguage_link",
            "status": "unresolved",
            "reason": (
                f"No interlanguage article found for "
                f"'{english_article['title']}' in '{language}' Wikipedia."
            ),
        }

    article_url = (
        f"https://{language}.wikipedia.org/wiki/"
        f"{target_title.replace(' ', '_')}"
    )

    return {
        "topic": topic,
        "source_language": "en",
        "source_title": english_article["title"],
        "language": language,
        "title": target_title,
        "url": article_url,
        "resolution_method": "interlanguage_link",
        "status": "resolved",
    }

def fetch_pageviews(
    article_title: str,
    language: str,
    start: str,
    end: str,
    granularity: str = "monthly",
) -> list[dict]:
    """
    Fetch Wikipedia pageviews for an article.

    Dates must be in YYYYMMDD format.
    Example:
        start="20240101"
        end="20241231"
    """

    encoded_title = article_title.replace(" ", "_")

    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"{language}.wikipedia/all-access/user/"
        f"{encoded_title}/{granularity}/{start}/{end}"
    )

    headers = {
        "User-Agent": USER_AGENT,
    }

    response = httpx.get(
        url,
        headers=headers,
        timeout=30.0,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("items", [])

if __name__ == "__main__":
    result = resolve_article(
        topic="intermittent fasting",
        language="cs",
    )

    print("Resolved article:")
    print(result)

    if result["status"] == "resolved":
        views = fetch_pageviews(
            article_title=result["title"],
            language=result["language"],
            start="20230101",
            end="20241231",
        )

        print("\nPageviews:")
        for item in views:
            print(
                item["timestamp"],
                item["views"],
            )

        metrics = calculate_basic_metrics(views)

        print("\nMetrics:")
        for key, value in metrics.items():
            print(f"{key}: {value}")