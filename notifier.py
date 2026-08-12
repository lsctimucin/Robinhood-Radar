from config import RADAR_NAME
from telegram_sender import TelegramSender


def build_message(launch, matches):
    name = launch.get("name") or "Unknown"
    symbol = launch.get("symbol") or "-"
    token = launch.get("token", "")
    creator = launch.get("creator", "")
    launch_address = launch.get("launch", "")
    tx_hash = launch.get("tx_hash", "")
    platform = launch.get(
        "platform",
        "UNKNOWN"
    )

    return (
        f"🚨 {RADAR_NAME}\n\n"
        f"🪙 {name}\n"
        f"💎 ${symbol}\n\n"
        f"🌐 Robinhood Chain\n"
        f"🏭 Platform: {platform}\n"
        f"🔎 Keyword: {', '.join(matches)}\n\n"
        f"📜 Token: `{token}`\n"
        f"🚀 Launch: {launch_address}\n"
        f"👤 Creator: {creator}\n"
        f"🔗 TX: "
        f"https://robinhoodchain.blockscout.com/tx/{tx_hash}\n"
        f"📊 Token: "
        f"https://robinhoodchain.blockscout.com/address/{token}"
    )


def make_notifier(sender: TelegramSender):

    def notify(launch, matches):
        message = build_message(
            launch,
            matches
        )

        print(
            "\n" + "=" * 60
        )

        print(message)

        print(
            "=" * 60 + "\n"
        )

        sender.send_message(
            message
        )

    return notify
