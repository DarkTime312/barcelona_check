import praw
import os
import json

# Authenticate using Environment Variables
reddit = praw.Reddit(
    client_id=os.environ['REDDIT_CLIENT_ID'],
    client_secret=os.environ['REDDIT_CLIENT_SECRET'],
    user_agent=os.environ['REDDIT_USER_AGENT']
)

# Example: Fetch the top 10 "hot" posts from a specific subreddit
subreddit = reddit.subreddit("barca") # Change to whatever you want
data = []

for submission in subreddit.hot(limit=10):
    data.append({
        "title": submission.title,
        "score": submission.score,
        "author": str(submission.author),
        "url": submission.url,
        "text": submission.selftext
    })

# Save to a JSON file
with open("barca_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)
