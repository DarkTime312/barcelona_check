import os
import re
from datetime import datetime
import praw

# --- Configuration ---
OUTPUT_HTML = "post_comments.html"
# How many top-level comments to keep (set to None for all)
TOP_COMMENTS_LIMIT = 20

# --- Reddit API init ---
reddit = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent=os.environ.get("REDDIT_USER_AGENT", "GH_Action_Comments:v1.0")
)

def extract_submission_id(url: str) -> str:
    """Extract submission ID from common Reddit URL formats."""
    # Handles:
    # https://www.reddit.com/r/.../comments/<id>/...
    # https://redd.it/<id>
    # https://www.reddit.com/comments/<id>/...
    patterns = [
        r'(?:reddit\.com|redd\.it)/r/\w+/comments/([a-z0-9]+)',
        r'(?:reddit\.com|redd\.it)/comments/([a-z0-9]+)',
        r'redd\.it/([a-z0-9]+)'
    ]
    for pat in patterns:
        match = re.search(pat, url)
        if match:
            return match.group(1)
    # Fallback: assume raw ID if no pattern matched
    return url.strip()

def fetch_top_level_top_comments(post_url: str, limit=None):
    """Return top-level comments sorted by score (top), limited to `limit`."""
    submission = reddit.submission(url=post_url)
    # Sort by "top" before expanding
    submission.comment_sort = "top"
    # Expand all MoreComments to get full list
    submission.comments.replace_more(limit=None)

    all_comments = submission.comments.list()
    # Keep only top-level comments (parent is the submission itself)
    top_level = [c for c in all_comments if c.parent_id == submission.fullname]

    # They are already in "top" order thanks to comment_sort,
    # but we can sort explicitly by score descending to be safe.
    top_level.sort(key=lambda c: c.score, reverse=True)

    if limit:
        top_level = top_level[:limit]

    return submission, top_level

def comment_to_dict(comment):
    """Convert a praw Comment to a simple dict for rendering."""
    return {
        'author': str(comment.author) if comment.author else '[deleted]',
        'body': comment.body,
        'score': comment.score,
    }

def render_html(submission, comments):
    """Generate a minimal HTML page with the post details and top comments."""
    post_title = submission.title.replace('<', '&lt;').replace('>', '&gt;')
    post_author = str(submission.author) if submission.author else '[deleted]'
    post_score = submission.score
    post_url = submission.url
    num_comments = submission.num_comments

    # Render comments
    comments_html = ""
    for cmt in comments:
        body_escaped = cmt['body'].replace('\n', '<br>').replace('<', '&lt;').replace('>', '&gt;')
        comments_html += f"""
        <div class="comment">
            <span class="comment-author">u/{cmt['author']} ({cmt['score']} pts)</span>
            <div class="comment-body">{body_escaped}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Top comments on: {post_title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 20px auto; padding: 0 20px; }}
        h1 {{ font-size: 1.6em; }}
        .post-meta {{ color: #787c7e; margin-bottom: 20px; }}
        .comment {{ border-left: 3px solid #edeff1; padding-left: 10px; margin: 10px 0; }}
        .comment-author {{ color: #1a1a1b; font-weight: bold; }}
        .comment-body {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>Top‑level top comments on:<br><a href="{post_url}" target="_blank">{post_title}</a></h1>
    <div class="post-meta">by u/{post_author} | score: {post_score} | {num_comments} total comments | showing top {len(comments)}</div>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    {comments_html}
</body>
</html>"""
    return html

def main():
    post_url = os.environ.get("POST_URL")
    if not post_url:
        raise ValueError("Environment variable POST_URL is required")

    print(f"Fetching comments for: {post_url}")
    submission, top_comments = fetch_top_level_top_comments(
        post_url, limit=TOP_COMMENTS_LIMIT
    )
    comments_data = [comment_to_dict(c) for c in top_comments]
    html_content = render_html(submission, comments_data)

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Saved {len(comments_data)} top comments to {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
