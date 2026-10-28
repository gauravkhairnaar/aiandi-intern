"""Classify forum comments as acceptable / toxic / spam using Cloudflare's Clef,
then write results.json and an easy-to-scan results.html.

Usage:
    python classify.py            # uses the larger, more accurate "clef" model
    python classify.py clef-flash # faster / cheaper model

Credentials are read from cloud-flare.local.sh (never put them in code).
"""
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request

MODEL = sys.argv[1] if len(sys.argv) > 1 else "clef"
COMMENTS_FILE = "comments.json"
RESULTS_JSON = "results.json"
RESULTS_HTML = "results.html"

INSTRUCTIONS = (
    "Classify `comment`, a post written by a student in the discussion forum "
    "of an online college course on Generative AI. Decide whether the post "
    "is fine to keep, or should be removed because it is toxic or spam."
)
CRITERIA = {
    "acceptable": (
        "A genuine, on-topic post: a question, doubt, answer, thanks, feedback "
        "or opinion about the course. Frustration or criticism of the course "
        "is acceptable as long as it does not attack a person."
    ),
    "toxic": (
        "Abusive or harassing: insults, name-calling, profanity aimed at "
        "someone, hate or discrimination, threats, or demeaning or "
        "humiliating a student or teacher."
    ),
    "spam": (
        "Unwanted promotion or junk: ads, links to sell or promote something, "
        "get-rich-quick offers, repeated or copy-pasted messages, or content "
        "unrelated to the course."
    ),
}


def load_credentials():
    text = open("cloud-flare.local.sh").read()
    creds = dict(re.findall(r'export (\w+)="([^"]*)"', text))
    return creds["CLOUDFLARE_ACCOUNT_ID"], creds["CLOUDFLARE_API_TOKEN"]


def load_comments():
    """Return a list of (id, text). Tolerates a few common JSON layouts."""
    data = json.load(open(COMMENTS_FILE, encoding="utf-8"))
    if isinstance(data, dict):
        lists = [v for v in data.values() if isinstance(v, list)]
        data = lists[0] if lists else []
    comments = []
    for i, item in enumerate(data, start=1):
        if isinstance(item, str):
            comments.append((i, item))
            continue
        cid = next((item[k] for k in ("id", "comment_id", "ID") if k in item), i)
        text = next(
            (item[k] for k in ("text", "comment", "body", "content", "message") if k in item),
            json.dumps(item, ensure_ascii=False),
        )
        comments.append((cid, text))
    return comments


def classify(account, token, text):
    payload = {
        "state": {"comment": text},
        "questions": {
            "label": {
                "type": "choice",
                "instructions": INSTRUCTIONS,
                "criteria": CRITERIA,
            }
        },
    }
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{account}"
        f"/ai/run/@cf/cloudflare/{MODEL}"
    )
    for attempt in range(5):
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.load(response)
        except urllib.error.HTTPError as err:
            if err.code == 429:  # too many requests: wait and retry
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(
                f"HTTP {err.code}. If 401/403, check the account ID and token "
                "in cloud-flare.local.sh."
            )
        if not data.get("success"):
            raise SystemExit(f"API error: {data.get('errors')}")
        answer = data["result"]["answers"]["label"]
        return answer["choice"], answer["probabilities"], answer["confidence"]
    raise SystemExit("Too many retries (rate limit).")


def render_html(results):
    counts = {k: sum(1 for r in results if r["label"] == k) for k in CRITERIA}
    rows = []
    for r in results:
        probs = ", ".join(f"{k} {v:.2f}" for k, v in r["probabilities"].items())
        low = " low" if r["confidence"] < 0.5 else ""
        rows.append(
            f'<div class="card {r["label"]}{low}" data-label="{r["label"]}" '
            f'data-low="{1 if low else 0}">'
            f'<div class="top"><span class="id">#{html.escape(str(r["id"]))}</span>'
            f'<span class="badge {r["label"]}">{r["label"]}</span>'
            f'<span class="conf">confidence {r["confidence"]:.2f}</span></div>'
            f'<p>{html.escape(r["text"])}</p>'
            f'<div class="probs">{html.escape(probs)}</div></div>'
        )
    summary = " &middot; ".join(f"{k}: {v}" for k, v in counts.items())
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clef comment classification</title>
<style>
:root {{ --bg:#0f1115; --card:#181b22; --text:#e6e8ee; --muted:#8b92a3;
  --ok:#3fb950; --tox:#f85149; --spam:#d29922; }}
body {{ background:var(--bg); color:var(--text); font-family:system-ui,sans-serif;
  margin:0; padding:16px; max-width:820px; margin-inline:auto; }}
h1 {{ font-size:1.3rem; margin:0 0 4px; }}
.sub {{ color:var(--muted); margin-bottom:12px; font-size:.9rem; }}
.filters {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:16px; position:sticky;
  top:0; background:var(--bg); padding:8px 0; }}
button {{ background:var(--card); color:var(--text); border:1px solid #2b303b;
  border-radius:8px; padding:6px 12px; cursor:pointer; }}
button.active {{ border-color:#58a6ff; color:#58a6ff; }}
.card {{ background:var(--card); border-left:4px solid var(--ok); border-radius:8px;
  padding:10px 14px; margin-bottom:10px; }}
.card.toxic {{ border-color:var(--tox); }}
.card.spam {{ border-color:var(--spam); }}
.top {{ display:flex; gap:10px; align-items:center; font-size:.85rem; }}
.id {{ color:var(--muted); }}
.badge {{ font-weight:600; text-transform:uppercase; font-size:.75rem; }}
.badge.acceptable {{ color:var(--ok); }}
.badge.toxic {{ color:var(--tox); }}
.badge.spam {{ color:var(--spam); }}
.conf {{ margin-left:auto; color:var(--muted); }}
.card.low .conf {{ color:#f0883e; font-weight:600; }}
p {{ margin:8px 0; line-height:1.45; }}
.probs {{ color:var(--muted); font-size:.78rem; }}
</style></head><body>
<h1>Clef classification of forum comments</h1>
<div class="sub">Model: {html.escape(MODEL)} &middot; {summary}</div>
<div class="filters">
<button class="active" data-f="all">All ({len(results)})</button>
<button data-f="acceptable">Acceptable</button>
<button data-f="toxic">Toxic</button>
<button data-f="spam">Spam</button>
<button data-f="low">Low confidence</button>
</div>
{''.join(rows)}
<script>
document.querySelectorAll('button').forEach(b => b.onclick = () => {{
  document.querySelectorAll('button').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  const f = b.dataset.f;
  document.querySelectorAll('.card').forEach(c => {{
    c.style.display = (f === 'all' || c.dataset.label === f ||
      (f === 'low' && c.dataset.low === '1')) ? '' : 'none';
  }});
}});
</script></body></html>"""
    return page


def main():
    account, token = load_credentials()
    comments = load_comments()
    results = []
    for n, (cid, text) in enumerate(comments, start=1):
        label, probs, conf = classify(account, token, text)
        results.append(
            {"id": cid, "text": text, "label": label,
             "probabilities": probs, "confidence": conf}
        )
        print(f"[{n}/{len(comments)}] #{cid}: {label} ({conf:.2f})")
        time.sleep(0.1)
    json.dump(results, open(RESULTS_JSON, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    open(RESULTS_HTML, "w", encoding="utf-8").write(render_html(results))
    print(f"Done. Open {RESULTS_HTML} in your browser.")


if __name__ == "__main__":
    main()
