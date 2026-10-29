# Notes

## How to run
1. Put your Cloudflare account ID and API token in 'cloud-flare.local.sh'
   (copy of cloud-flare.sh'; it is git-ignored).
2. Run the classifier on each comments file:
   - `python classify.py` (reads `comments.json`, writes `results.json`
     and `results.html`)
   - `python classify.py comments-v2.json` (reads `comments-v2.json`,
     writes `results-v2.json` and `results-v2.html`)
3. Open the `.html` file in a browser to see every comment with its      label, confidence and class probabilities. Low-confidence comments are
highlighted and can be filtered.

## Tools and models used
- Claude (Anthropic) to write the Python program and the HTML page.
- Cloudflare Workers AI with the Clef model (`clef`, the larger model)
  to classify comments as acceptable, toxic or spam.
- Python standard library only (no extra packages).
- The mistakes in MISTAKES.md are my own judgement, for both
  `comments.json` and `comments-v2.json`. I read each comment together with its label in the HTML page and did not use AI for this part.

## What I felt about this task
- The task was easy, completed it fast than the earlier one.
- I think the model which i used 'clef' filters out the "TOXIC" comments accurately and get's confused in general comments, it's obvious as the bot can't think like an actual human.
