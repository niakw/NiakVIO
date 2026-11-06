#!/usr/bin/env python3
"""One-shot GitHub Discussions announcement; fail closed, idempotent by title."""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

OWNER, REPO = "niakw", "NiakVIO"
TITLE = "Contributions welcome — build a more reliable NiakVIO together!"
ROOT = Path(__file__).resolve().parents[1]
BODY_PATH = ROOT / "docs" / "COMMUNITY_CONTRIBUTIONS_2026-11-06.md"

def graphql(query: str, variables: dict[str, object] | None = None) -> dict:
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        raise RuntimeError("GitHub Discussions write token not available")
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    request = Request("https://api.github.com/graphql", data=payload, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }, method="POST")
    with urlopen(request, timeout=30) as response:
        result = json.loads(response.read(500000).decode("utf-8"))
    if result.get("errors"):
        raise RuntimeError("Discussion GraphQL error: " + json.dumps(result["errors"])[:1000])
    return result.get("data") or {}

def main() -> None:
    body = BODY_PATH.read_text(encoding="utf-8")
    if len(body) < 300 or "Brain-LLM" not in body:
        raise ValueError("Contribution announcement body missing or incomplete")
    q = """
    query($owner:String!, $name:String!) {
      repository(owner:$owner,name:$name) {
        id
        discussionCategories(first:40) { nodes { id name slug } }
        discussions(last:100) { nodes { title url } }
      }
    }
    """
    repository = graphql(q, {"owner": OWNER, "name": REPO}).get("repository")
    if not isinstance(repository, dict):
        raise RuntimeError("GitHub Discussions unavailable on target repository")
    existing = next((x for x in repository["discussions"]["nodes"]
                     if x.get("title") == TITLE), None)
    if existing:
        print("FIELD_NIAKVIO_COMMUNITY_DISCUSSION_EXISTING " + str(existing["url"]))
        return
    categories = repository["discussionCategories"]["nodes"]
    category = next((row for slug in ("general", "announcements", "ideas", "q-a")
                     for row in categories if row.get("slug") == slug), None)
    if not category:
        raise RuntimeError("No writable general/announcements Discussion category")
    mutation = """
    mutation($repositoryId:ID!, $categoryId:ID!, $title:String!, $body:String!) {
      createDiscussion(input:{repositoryId:$repositoryId,categoryId:$categoryId,title:$title,body:$body}) {
        discussion { url number title }
      }
    }
    """
    data = graphql(mutation, {"repositoryId": repository["id"], "categoryId": category["id"],
                             "title": TITLE, "body": body})
    created = (data.get("createDiscussion") or {}).get("discussion") or {}
    url = created.get("url")
    if not url or not url.startswith("https://github.com/niakw/NiakVIO/discussions/"):
        raise RuntimeError("GitHub did not confirm a NiakVIO Discussion URL")
    print("FIELD_NIAKVIO_COMMUNITY_DISCUSSION_PUBLISHED " + url)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
            out.write("Contribution invitation published: " + url + "\\n")

if __name__ == "__main__":
    main()
