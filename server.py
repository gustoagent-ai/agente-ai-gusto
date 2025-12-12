# server.py
import os
import asyncio
import logging
import requests
from flask import Flask, request, jsonify

# importa tu función real - puede ser async o sync
from agent import run_agent

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Estos deben configurarse en Render (Environment > Environment Variables)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("PHONE_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")  # elige uno y configúralo en Meta
# Opcional: configuración de Langfuse si quieres instrumentarlo ahí
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL")

if not WHATSAPP_TOKEN or not PHONE_ID:
    logging.warning("WHATSAPP_TOKEN o PHONE_ID no definidos. Asegúrate de añadirlos en Render > Environment.")

def call_agent_sync_or_async(prompt: str) -> str:
    """
    Llama a tu run_agent. Si es async, lo ejecuta con asyncio.run;
    si es sync, lo ejecuta directamente.
    Debes ajustar el retorno según tu función (string esperado).
    """
    try:
        result = run_agent(prompt)
        if asyncio.iscoroutine(result):
            # Ejecutar coroutine hasta completarse
            return asyncio.run(result)
        else:
            return result
    except Exception as e:
        logging.exception("Error al ejecutar el agente.")
        return f"Error interno: {e}"

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Endpoint para verificación de webhook de Meta/WhatsApp"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info("Webhook verificado correctamente.")
        return challenge, 200
    else:
        logging.warning("Webhook verification failed.")
        return "Verification token mismatch", 403

@app.route("/webhook", methods=["POST"])
def webhook_received():
    """Webhook para recibir mensajes entrantes"""
    data = request.get_json(silent=True)
    logging.info("Webhook payload: %s", data)

    try:
        # payload típico: entry[0].changes[0].value.messages[0]
        entry = data.get("entry", [])
        if not entry:
            return jsonify({"ok": True}), 200

        change = entry[0].get("changes", [])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return jsonify({"ok": True}), 200

        msg = messages[0]
        user = msg.get("from")
        text = None
        # soporte texto simple
        if "text" in msg:
            text = msg["text"].get("body")
        # (añade otros tipos si lo necesitas: button, interactive, etc.)

        if text and user:
            # Llamada al agente (sync o async)
            reply = call_agent_sync_or_async(text)
            send_whatsapp_message(user, reply)

    except Exception as e:
        logging.exception("Error procesando webhook: %s", e)

    return jsonify({"ok": True}), 200

def send_whatsapp_message(to: str, message: str):
    """Envía mensaje usando la WhatsApp Cloud API (v19.0 o la versión que uses)"""
    if not WHATSAPP_TOKEN or not PHONE_ID:
        logging.error("No se puede enviar mensaje: WHATSAPP_TOKEN o PHONE_ID no definidos.")
        return

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
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        logging.info("Mensaje enviado a %s (status %s).", to, r.status_code)
    except Exception as e:
        logging.exception("Error al enviar mensaje a WhatsApp: %s", e)

if __name__ == "__main__":
    # Render/Heroku/proxy te proporcionan PORT en env vars
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
