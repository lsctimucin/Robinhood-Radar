rom html import escape

from config import RADAR_NAME
from telegram_sender import TelegramSender


def build_message(launch, matches):
    name = escape(str(launch.get("name") or "Unknown"))
    symbol = escape(str(launch.get("symbol") or "-"))
    token = str(launch.get("token") or "")
    creator = escape(str(launch.get("creator") or "-"))
    launch_address = escape(str(launch.get("launch") or "-"))
    tx_hash = str(launch.get("tx_hash") or "")
    platform = escape(str(launch.get("platform") or "UNKNOWN"))
    keyword_text = escape(", ".join(str(x) for x in matches))

    message = (
        f"🚨 {escape(str(RADAR_NAME))}\n\n"
        f"🪙 {name}\n"
        f"💎 ${symbol}\n\n"
        f"🌐 Robinhood Chain\n"
        f"🏭 Platform: {platform}\n"
        f"🔎 Keyword: {keyword_text}\n\n"
        f"📜 Token: <code>{escape(token)}</code>\n"
        f"🚀 Launch: {launch_address}\n"
        f"👤 Creator: {creator}\n"
    )

    if tx_hash:
        message += (
            f"🔗 TX: "
            f"https://robinhoodchain.blockscout.com/tx/{escape(tx_hash)}\n"
        )

    if token:
        message += (
            f"📊 Token: "
            f"https://robinhoodchain.blockscout.com/address/{escape(token)}"
        )

    return message


def make_notifier(sender: TelegramSender):
    def notify(launch, matches):
        message = build_message(launch, matches)

        print("\n" + "=" * 60)
        print(message)
        print("=" * 60 + "\n")

        sender.send_message(message)

    return notify
