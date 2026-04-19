import os
from datetime import datetime
import praw
from praw.models import Comment, Submission

# --- Configuration ---
SUBREDDIT_NAME = "Barca"          # Change as needed, or use env var
POST_LIMIT = 20
OUTPUT_HTML = "reddit_feed.html"

# Reddit API credentials from environment
reddit = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent=os.environ["REDDIT_USER_AGENT"]
)

def fetch_top_posts(subreddit_name: str, limit: int):
    subreddit = reddit.subreddit(subreddit_name)
    return list(subreddit.top(limit=limit))  # default time filter = day

def build_comment_tree(comment_list):
    """Convert a list of praw Comments into a nested structure for HTML rendering."""
    comment_list.sort(key=lambda c: c.score, reverse=True)  # Optional: sort by score
    tree = []
    for comment in comment_list:
        if not isinstance(comment, Comment):
            continue
        # Recursively process replies
        replies = []
        if hasattr(comment, 'replies') and comment.replies:
            # Force replace_more to get all comments (limit to depth 5 for performance)
            comment.replies.replace_more(limit=0)
            replies = build_comment_tree(comment.replies.list())
        tree.append({
            'author': str(comment.author) if comment.author else '[deleted]',
            'body': comment.body,
            'score': comment.score,
            'replies': replies
        })
    return tree

def render_comments_html(comments_tree, level=0):
    """Recursively generate HTML <details> blocks for comments."""
    html = ""
    for comment in comments_tree:
        body_escaped = comment['body'].replace('\n', '<br>').replace('<', '&lt;').replace('>', '&gt;')
        author = comment['author']
        score = comment['score']
        replies = comment['replies']

        if replies:
            html += f"""
            <details class="comment-tree" style="margin-left: {level*20}px;">
                <summary><span class="comment-author">u/{author} ({score} pts)</span></summary>
                <div class="comment-body">
                    <div class="comment-text">{body_escaped}</div>
                    {render_comments_html(replies, level+1)}
                </div>
            </details>
            """
        else:
            html += f"""
            <div class="comment-tree" style="margin-left: {level*20}px;">
                <div class="comment-author">u/{author} ({score} pts)</div>
                <div class="comment-body">
                    <div class="comment-text">{body_escaped}</div>
                </div>
            </div>
            """
    return html

def generate_html(posts):
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>r/{SUBREDDIT_NAME} - Top {len(posts)} Posts</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 20px auto; padding: 0 20px; }}
        h1 {{ color: #1a1a1b; }}
        .post {{ border-bottom: 1px solid #ccc; margin-bottom: 25px; padding-bottom: 20px; }}
        .post-title {{ font-size: 1.6em; margin-bottom: 5px; }}
        .post-meta {{ color: #787c7e; margin-bottom: 10px; }}
        details {{ margin: 8px 0; }}
        summary {{ cursor: pointer; color: #1a1a1b; }}
        .comment-body {{ margin: 5px 0; padding-left: 15px; border-left: 2px solid #edeff1; }}
        .comment-author {{ color: #787c7e; font-size: 0.9em; }}
        .comment-text {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>r/{SUBREDDIT_NAME} – Top {len(posts)} Posts (with comments)</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""

    for post in posts:
        # Load full submission to get comments (already fetched as Submission objects)
        if not isinstance(post, Submission):
            continue
        # Expand "MoreComments" to get full tree (depth-limited for speed)
        post.comments.replace_more(limit=0)
        comments_tree = build_comment_tree(post.comments.list())

        title_escaped = post.title.replace('<', '&lt;').replace('>', '&gt;')
        html += f"""
    <div class="post">
        <div class="post-title"><a href="{post.url}" target="_blank">{title_escaped}</a></div>
        <div class="post-meta">by u/{post.author} | score: {post.score} | {post.num_comments} comments</div>
        <div class="comments">
            {render_comments_html(comments_tree)}
        </div>
    </div>
"""

    html += "</body>\n</html>"
    return html

def save_html(content, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"HTML saved to {filename}")

if __name__ == "__main__":
    print(f"Fetching top {POST_LIMIT} posts from r/{SUBREDDIT_NAME}...")
    top_posts = fetch_top_posts(SUBREDDIT_NAME, POST_LIMIT)
    print(f"Generating HTML...")
    html_content = generate_html(top_posts)
    save_html(html_content, OUTPUT_HTML)
    print("Done.")
