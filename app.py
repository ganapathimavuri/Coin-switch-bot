import os
import json
import time
import requests
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives.asymmetric import ed25519

app = Flask(__name__)

API_KEY = "83b0c60e699af18a5ec598776c0c5ae6909892865f058267857b2783d088576e"
SECRET_KEY_HEX = "78d5d252219782a42af07d77c9124b85a117005e55caafe037fd376a38ba9559"
BASE_URL = "https://coinswitch.co"
ENDPOINT = "/trade/api/v2/futures/order"

private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(SECRET_KEY_HEX))

@app.route('/', methods=['GET'])
def health():
    return "CoinSwitch Bot is Running!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        raw_text = request.get_data(as_text=True).strip()
        print(f"Received alert body: {raw_text}")

        data = request.get_json(silent=True) or {}
        if not data and raw_text:
            try:
                data = json.loads(raw_text)
            except Exception:
                data = {"side": raw_text}

        raw_side = str(data.get("side", "BUY")).upper()
        side = "SELL" if "SELL" in raw_side else "BUY"

        payload = {
            "exchange": str(data.get("exchange", "cs")),
            "symbol": str(data.get("symbol", "BTC/USDT")),
            "margin_amount": str(data.get("margin_amount", "1000")),
            "leverage": int(data.get("leverage", 25)),
            "side": side,
            "margin_currency": str(data.get("margin_currency", "INR")),
            "take_profit_percentage": float(data.get("take_profit_percentage", 25.0)),
            "stop_loss_percentage": float(data.get("stop_loss_percentage", 25.0)),
            "order_type": str(data.get("order_type", "MARKET"))
        }

        epoch_str = str(int(time.time() * 1000))
        msg = f"POST{ENDPOINT}{epoch_str}".encode('utf-8')
        sig = private_key.sign(msg).hex()

        headers = {
            "Content-Type": "application/json",
            "X-AUTH-APIKEY": API_KEY,
            "X-AUTH-EPOCH": epoch_str,
            "X-AUTH-SIGNATURE": sig
        }

        res = requests.post(BASE_URL + ENDPOINT, headers=headers, json=payload, timeout=10)
        print(f"CoinSwitch status: {res.status_code}, response: {res.text}")
        return res.text, res.status_code

    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
  
