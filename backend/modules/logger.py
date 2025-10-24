import requests

def telegram_notify(token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        params = {"chat_id": chat_id, "text": message}
        requests.post(url, params=params, timeout=10)  # Таймаут 10 сек
    except Exception as e:
        print(f"Telegram error: {e}")
