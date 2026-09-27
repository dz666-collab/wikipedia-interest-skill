import re

import httpx

from cache_utils import load_cache, save_cache


USER_AGENT = "WikipediaInterestSkillBot/1.0"


def _headers() -> dict:
    return {
        "User-Agent": USER_AGENT,
    }


def _clean_snippet(snippet: str) -> str:
    """
    Remove simple HTML tags returned by MediaWiki search snippets.
    """
    return re.sub(r"<[^>]+>", "", snippet)


def search_english_article(topic: str) -> dict:
    cache_key = f"search_english_article::{topic}"

    cached = load_cache(
        "article_search",
        cache_key,
    )

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

    response = httpx.get(
        url,
        params=params,
        headers=_headers(),
        timeout=20.0,
    )
    response.raise_for_status()

    data = response.json()
    results = data["query"]["search"]

    if not results:
        raise ValueError(
            f"No English Wikipedia article found for topic '{topic}'"
        )

    result = {
        "pageid": results[0]["pageid"],
        "title": results[0]["title"],
    }

    save_cache(
        "article_search",
        cache_key,
        result,
    )

    return result


def get_english_article_by_title(title: str) -> dict:
    """
    Resolve an explicitly chosen canonical English Wikipedia article.
    """
    cache_key = f"english_article_by_title::{title}"

    cached = load_cache(
        "english_article_by_title",
        cache_key,
    )

    if cached is not None:
        return cached

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "titles": title,
        "format": "json",
        "redirects": 1,
    }

    response = httpx.get(
        url,
        params=params,
        headers=_headers(),
        timeout=20.0,
    )
    response.raise_for_status()

    data = response.json()
    pages = data["query"]["pages"]

    page = next(iter(pages.values()))

    if "missing" in page:
        raise ValueError(
            f"English Wikipedia article '{title}' was not found."
        )

    result = {
        "pageid": page["pageid"],
        "title": page["title"],
    }

    save_cache(
        "english_article_by_title",
        cache_key,
        result,
    )

    return result


def get_interlanguage_title(
    english_title: str,
    target_language: str,
) -> str | None:
    cache_key = (
        f"get_interlanguage_title::{english_title}::{target_language}"
    )

    cached = load_cache(
        "langlinks",
        cache_key,
    )

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

    response = httpx.get(
        url,
        params=params,
        headers=_headers(),
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


def search_local_candidates(
    topic: str,
    language: str,
    limit: int = 5,
) -> list[dict]:
    """
    Return local Wikipedia search candidates.

    Candidates are returned for review instead of being
    automatically selected.
    """
    cache_key = (
        f"local_candidates::{topic}::{language}::{limit}"
    )

    cached = load_cache(
        "local_candidates",
        cache_key,
    )

    if cached is not None:
        return cached

    url = f"https://{language}.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": topic,
        "format": "json",
        "utf8": 1,
        "srlimit": limit,
    }

    response = httpx.get(
        url,
        params=params,
        headers=_headers(),
        timeout=20.0,
    )
    response.raise_for_status()

    data = response.json()
    results = data["query"]["search"]

    candidates = []

    for item in results:
        candidates.append(
            {
                "pageid": item["pageid"],
                "title": item["title"],
                "snippet": _clean_snippet(
                    item.get("snippet", "")
                ),
            }
        )

    save_cache(
        "local_candidates",
        cache_key,
        candidates,
    )

    return candidates


def resolve_article(
    topic: str,
    language: str,
    article_override: str | None = None,
    source_article: str | None = None,
) -> dict:
    """
    Resolve a topic to an article in the target language.

    Resolution order:
    1. Explicit target-language article override.
    2. Explicit canonical English source article, if provided.
    3. English search result for the topic.
    4. Interlanguage link.
    5. Local candidates requiring review.
    """

    if article_override:
        return {
            "topic": topic,
            "source_language": None,
            "source_title": source_article,
            "language": language,
            "title": article_override,
            "url": (
                f"https://{language}.wikipedia.org/wiki/"
                f"{article_override.replace(' ', '_')}"
            ),
            "resolution_method": "explicit_override",
            "status": "resolved",
        }

    cache_key = (
        f"resolve_article::{topic}::{language}::{source_article}"
    )

    cached = load_cache(
        "resolved_articles",
        cache_key,
    )

    if cached is not None:
        return cached

    if source_article:
        english_article = get_english_article_by_title(
            source_article
        )
        source_method = "explicit_source_article"
    else:
        english_article = search_english_article(
            topic
        )
        source_method = "english_search"

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
            "resolution_method": source_method,
            "status": "resolved",
        }

        save_cache(
            "resolved_articles",
            cache_key,
            result,
        )

        return result

    target_title = get_interlanguage_title(
        english_title=english_article["title"],
        target_language=language,
    )

    if target_title is not None:
        result = {
            "topic": topic,
            "source_language": "en",
            "source_title": english_article["title"],
            "language": language,
            "title": target_title,
            "url": (
                f"https://{language}.wikipedia.org/wiki/"
                f"{target_title.replace(' ', '_')}"
            ),
            "resolution_method": (
                "interlanguage_link_from_explicit_source"
                if source_article
                else "interlanguage_link"
            ),
            "status": "resolved",
        }

        save_cache(
            "resolved_articles",
            cache_key,
            result,
        )

        return result

    candidates = search_local_candidates(
        topic=topic,
        language=language,
    )

    result = {
        "topic": topic,
        "source_language": "en",
        "source_title": english_article["title"],
        "language": language,
        "title": None,
        "url": None,
        "resolution_method": "local_candidates",
        "status": "needs_review",
        "reason": (
            f"No interlanguage article found for "
            f"'{english_article['title']}' "
            f"in '{language}' Wikipedia."
        ),
        "candidates": candidates,
    }

    save_cache(
        "resolved_articles",
        cache_key,
        result,
    )

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

    cached = load_cache(
        "pageviews",
        cache_key,
    )

    if cached is not None:
        return cached

    encoded_title = article_title.replace(" ", "_")

    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"{language}.wikipedia/all-access/user/"
        f"{encoded_title}/{granularity}/{start}/{end}"
    )

    response = httpx.get(
        url,
        headers=_headers(),
        timeout=30.0,
    )
    response.raise_for_status()

    data = response.json()
    items = data.get("items", [])

    save_cache(
        "pageviews",
        cache_key,
        items,
    )

    return items