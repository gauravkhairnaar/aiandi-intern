# Notes

## How to run
1. Put your Cloudflare account ID and API token in 'cloud-flare.local.sh'
   (copy of cloud-flare.sh'; it is git-ignored).
2. Run: 'python classify.py' (uses the 'clef' model by default;
   'python classify.py clef-flash' uses the faster model).
3. Open 'results.html' in a browser to see every comment with its label.
   Raw output is saved in 'results.jso'.

## Tools and models used
- Claude (Anthropic) to write the Python program and the HTML page,
  and to explain the task and the Cloudflare setup.
- Cloudflare Workers AI with the Clef model (`clef`, the larger model)
  to classify comments as acceptable, toxic or spam.
- Python standard library only (no extra packages).
- The mistakes in MISTAKES.md are my own judgement. I read each comment
  with its label in results.html and did not use AI for this part.

## What I felt about this task
- The task was easy, as it was the first time took me little bit more time than(one hour),
but it's the repetitive one which makes it mroe easier and faster next time.

- I think the model which i used 'clef' filters out the "TOXIC" comments accurately and get's 
confused in general comments, like the 29th , 30th comment.
