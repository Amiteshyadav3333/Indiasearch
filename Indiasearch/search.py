from elasticsearch import Elasticsearch
import re


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_snippet(content, query):
    content = clean_text(content)

    query = query.lower()

    idx = content.lower().find(query)

    if idx == -1:
        return content[:160] + "..."

    start = max(idx - 60, 0)
    end = min(idx + 60, len(content))

    snippet = content[start:end]

    return "... " + snippet + " ..."


def search_query(es: Elasticsearch, index: str, query: str):

    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": [
                    "title^3",
                    "content"
                ]
            }
        },
        "highlight": {
            "fields": {
                "content": {}
            }
        },
        "size": 10
    }

    res = es.search(index=index, body=body)

    results = []

    for hit in res["hits"]["hits"]:
        source = hit["_source"]

        title = source.get("title", "No Title")
        url = source.get("url", "")
        content = source.get("content", "")

        snippet = make_snippet(content, query)

        results.append({
            "title": title,
            "url": url,
            "snippet": snippet,
            "score": hit["_score"]
        })

    return results