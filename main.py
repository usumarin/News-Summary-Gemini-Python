import os
import json
import requests
import feedparser
from google import genai  # ← ここが変わりました
from dotenv import load_dotenv

load_dotenv()

# --- 設定情報の取得 ---
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
USER_ID = os.environ.get("LINE_USER_ID", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 新しいクライアントの初期化
client = genai.Client(api_key=GEMINI_KEY)


def get_news():
    """Googleニュースのトップストーリーを取得"""
    rss_url = "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"
    feed = feedparser.parse(rss_url)
    return feed.entries[:5]


def summarize_text(title):
    """新しい書き方でGeminiに要約を頼む"""
    prompt = (
        f"以下のニュースを2行（60文字以内）で解説してください。\n"
        f"【重要】「**」などの記号は一切使わず、プレーンテキストのみで出力してください。\n"
        f"余計な挨拶や見出し（内容推測：など）も不要です。\n"
        f"タイトル: {title}"
    )
    try:
        # モデル名の指定方法が変わりました（'gemini-2.0-flash' などが使えます）
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        summary = response.text.strip()
        summary = summary.replace("*", "").replace("\n", " ")

        return summary
    except Exception as e:
        print(f"DEBUG: Summary Error: {e}")
        return "ニュース内容の解析中..."


def send_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}",
    }
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    # 送信結果を response に入れる
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # --- ここからデバッグ用ログ ---
    print(f"DEBUG: LINE Status Code: {response.status_code}")
    print(f"DEBUG: LINE Response Body: {response.text}")
    # ---------------------------

    if response.status_code == 200:
        print("LINE送信成功！")
    else:
        print("LINE送信失敗...")


def main():
    entries = get_news()
    msg = "📰 【今日のトップニュース要約】\n\n"
    for entry in entries:
        summary = summarize_text(entry.title)
        msg += f"📝 {summary}\n"
        msg += f"🔗 {entry.link}\n\n"
    send_line(msg)
    print("通知を送信しました。")
    print(msg)


if __name__ == "__main__":
    main()
