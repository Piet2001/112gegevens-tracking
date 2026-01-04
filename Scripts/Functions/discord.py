import requests
import os

def webhook(message):
    color = "9212311"
    if "added" in message:
        color = "8388352"
    elif "removed" in message:
        color = "16711680"
    elif "changed" in message:
        color = "16746496"

    webhook_url = os.getenv("DISCORD")
    embed = {
        "title": "Change in 112 gegevens",
        "description": message,
        "color": color,
    }
    webhookdata = {
        "username": "112data Monitor",
        "embeds": [
            embed
        ],
    }

    headers = {
        "Content-Type": "application/json"
    }

    result = requests.post(webhook_url, json=webhookdata, headers=headers)
    if 200 <= result.status_code < 300:
        print(f"Webhook sent {result.status_code}")
    else:
        print(f"Not sent with {result.status_code}, response:\n{result.json()}")