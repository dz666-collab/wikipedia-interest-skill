import httpx

from cache_utils import load_cache, save_cache


USER_AGENT = "WikipediaInterestSkill/0.1 (contact: dz546838@gmail.com)"


def search_english_article(topic: str) -> dict:
    cache_key = f"search_english_article::{topic}"
    cached = load_cache("article_search", cache_key)

    if cached is not None:
        return cached

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

    best_match = {
        "pageid": results[0]["pageid"],
        "title": results[0]["title"],
    }

    save_cache("article_search", cache_key, best_match)
    return best_match


def get_interlanguage_title(
    english_title: str,
    target_language: str,
) -> str | None:
    cache_key = (
        f"get_interlanguage_title::{english_title}::{target_language}"
    )
    cached = load_cache("langlinks", cache_key)

    if cached is not None:
        return cached["title"]

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
        save_cache(
            "langlinks",
            cache_key,
            {"title": None},
        )
        return None

    title = langlinks[0]["*"]

    save_cache(
        "langlinks",
        cache_key,
        {"title": title},
    )

    return title


def resolve_article(topic: str, language: str) -> dict:
    cache_key = f"resolve_article::{topic}::{language}"
    cached = load_cache("resolved_articles", cache_key)

    if cached is not None:
        return cached

    english_article = search_english_article(topic)

    if language == "en":
        result = {
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
        save_cache("resolved_articles", cache_key, result)
        return result

    target_title = get_interlanguage_title(
        english_title=english_article["title"],
        target_language=language,
    )

    if target_title is None:
        result = {
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
        save_cache("resolved_articles", cache_key, result)
        return result

    article_url = (
        f"https://{language}.wikipedia.org/wiki/"
        f"{target_title.replace(' ', '_')}"
    )

    result = {
        "topic": topic,
        "source_language": "en",
        "source_title": english_article["title"],
        "language": language,
        "title": target_title,
        "url": article_url,
        "resolution_method": "interlanguage_link",
        "status": "resolved",
    }

    save_cache("resolved_articles", cache_key, result)
    return result


def fetch_pageviews(
    article_title: str,
    language: str,
    start: str,
    end: str,
    granularity: str = "monthly",
) -> list[dict]:
    cache_key = (
        f"fetch_pageviews::{article_title}::{language}::"
        f"{start}::{end}::{granularity}"
    )
    cached = load_cache("pageviews", cache_key)

    if cached is not None:
        return cached

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
    items = data.get("items", [])

    save_cache("pageviews", cache_key, items)
    return items