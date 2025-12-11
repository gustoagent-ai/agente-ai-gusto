import os
import requests
from flask import Flask, request
from agent import run_agent  # tu lógica del agente

app = Flask(__name__)

WHATSAPP_TOKEN = os.getenv("EAAPKCE8WQ7ABQHIXmjMCZA6HZBBXusp9ZAx8KhqL4vcY86rG6IicKOnPu4APlmSPllDg1mGBDQQS8lyvYDB7qAEKaSAFGBn8I4y9XZAkqHJg7CK7gjjCurZCPFq5IrjnMwfdWybCmZCgyt58POtuCPxSZBD41UtPoc9UY6xWWsIKWopBlKwfuuMZCs4w74yhClXLZAdPqffWQowHwWZAFuoCNCCDpGYT6XXUNelX2NVx9clpSUHKofJgqqcP8tbK7R4MZBn1EPgt7G8YhTZBCcG1ImhbJAgdogZDZD")
PHONE_ID = os.getenv("1227444885954422")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "messages" in data["entry"][0]["changes"][0]["value"]:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        user = msg["from"]
        text = msg["text"]["body"]

        reply = run_agent(text)  # la función para procesar tu agente

        send_whatsapp_message(user, reply)

    return "EVENT_RECEIVED"

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, headers=headers, json=payload)

@app.route("/webhook", methods=["GET"])
def verify():
    return request.args.get("hub.challenge")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
