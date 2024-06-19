from flask import Flask, request
import feedparser
import requests
import aiohttp
import asyncio
import os
import datetime

app = Flask(__name__)

# LINE Notify token
LINE_NOTIFY_TOKEN = "GHRzDeRzQr5OYqAtiOM23ytNa2pnWDXLvYF1D0PbVKY"
LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"

# RSS feed URL
RSS_URL = "https://webboard-nsoc.ncsa.or.th/category/12.rss"


def get_last_processed_time():
    last_processed_time = os.getenv("LAST_PROCESSED_TIME")
    if last_processed_time:
        return datetime.datetime.fromisoformat(last_processed_time)
    return None


def set_last_processed_time(time):
    os.environ["LAST_PROCESSED_TIME"] = time.isoformat()


async def send_line_notify(session, message, token):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {token}",
    }
    data = {"message": message}
    async with session.post(LINE_NOTIFY_API, headers=headers, data=data) as response:
        return response.status


async def fetch_and_notify():
    last_processed_time = get_last_processed_time()
    feed = feedparser.parse(RSS_URL)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for entry in feed.entries:
            entry_time = datetime.datetime(*entry.published_parsed[:6])
            if last_processed_time is None or entry_time > last_processed_time:
                title = entry.title
                link = entry.link
                message = f"New post: {title}\nLink: {link}"
                tasks.append(send_line_notify(session, message, LINE_NOTIFY_TOKEN))
        if tasks:
            await asyncio.gather(*tasks)
            # Update the last processed time to the latest entry's time
            set_last_processed_time(
                datetime.datetime(*feed.entries[0].published_parsed[:6])
            )


@app.route("/notify", methods=["GET"])
def notify():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fetch_and_notify())
    return "Notifications sent!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
