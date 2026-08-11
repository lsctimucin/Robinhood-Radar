import requests

class TelegramSender:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    def send_message(self, text: str) -> bool:
        if not self.token or not self.chat_id:
            print("Telegram ayarlari eksik: BOT_TOKEN / CHAT_ID")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        try:
            response = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            if response.ok:
                print("Telegram: OK")
                return True

            print(f"Telegram: {response.status_code} {response.text}")
            return False
        except Exception as exc:
            print(f"Telegram exception: {exc}")
            return False
