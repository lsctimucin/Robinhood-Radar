from config import RADAR_NAME
from telegram_sender import TelegramSender

def build_message(launch, matches):
    name = launch["name"] or "Unknown"
    symbol = launch["symbol"] or "-"
    token = launch["token"]
    creator = launch["creator"]
    launch_address = launch["launch"]
    tx_hash = launch["tx_hash"]

    return (
        f"🚨 {RADAR_NAME}\n\n"
        f"🪙 {name}\n"
        f"💎 ${symbol}\n\n"
        f"🌐 Robinhood Chain\n"
        f"🔎 Keyword: {', '.join(matches)}\n\n"
        f"📜 Token: {token}\n"
        f"🚀 Launch: {launch_address}\n"
        f"👤 Creator: {creator}\n"
        f"🔗 TX: https://robinhoodchain.blockscout.com/tx/{tx_hash}\n"
        f"📊 Token: https://robinhoodchain.blockscout.com/address/{token}"
    )

def make_notifier(sender: TelegramSender):
    def notify(launch, matches):
        message = build_message(launch, matches)
        print("\n" + "=" * 60)
        print(message)
        print("=" * 60 + "\n")
        sender.send_message(message)
    return notify
