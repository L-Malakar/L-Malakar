import json
import os
import base64
import urllib.request

user = os.environ["GH_USER"]
token = os.environ["GH_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    name
    login
    avatarUrl
    contributionsCollection {
      contributionCalendar {
        totalContributions
      }
      commitContributionsByRepository(maxRepositories: 10) {
        repository { name }
        contributions { totalCount }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {"login": user}}).encode(),
    headers={
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    },
)

with urllib.request.urlopen(req) as resp:
    data = json.load(resp)

if "errors" in data:
    print("::error::GraphQL API returned errors:", data["errors"])
    raise SystemExit(1)

u = data["data"]["user"]
name = u["name"] or u["login"]
avatar_url = u["avatarUrl"]
cc = u["contributionsCollection"]
total = cc["contributionCalendar"]["totalContributions"]

repos = cc["commitContributionsByRepository"]
repos_sorted = sorted(repos, key=lambda r: r["contributions"]["totalCount"], reverse=True)
top_names = [r["repository"]["name"] for r in repos_sorted[:2]]

if len(top_names) >= 2:
    top_line = f"{top_names[0]}, {top_names[1]} and more..."
elif len(top_names) == 1:
    top_line = f"{top_names[0]} and more..."
else:
    top_line = "no contributions yet"

print(f"Resolved -> name={name!r} total={total} top_line={top_line!r}")

with urllib.request.urlopen(avatar_url) as img_resp:
    avatar_bytes = img_resp.read()
avatar_b64 = base64.b64encode(avatar_bytes).decode()


def xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


with open("images/banner-template.svg", encoding="utf-8") as f:
    svg = f.read()

svg = svg.replace("__AVATAR_BASE64__", avatar_b64)
svg = svg.replace("__NAME__", xml_escape(name))
svg = svg.replace("__TOTAL_CONTRIBUTIONS__", str(total))
svg = svg.replace("__TOP_REPOS_LINE__", xml_escape(top_line))

with open("dist/loading-banner.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("Wrote dist/loading-banner.svg")
