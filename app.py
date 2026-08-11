from config import BOT_TOKEN, CHAT_ID, TARGET_SYMBOL
from telegram_sender import TelegramSender
from notifier import make_notifier
from launcher_monitor import LauncherMonitor

def main():
    print("=" * 60)
    print("ROBINHOOD RADAR")
    print(f"Target launch: ${TARGET_SYMBOL}")
    print("Keyword mode: Patoshi Radar keywords")
    print("Wallet analysis: DISABLED")
    print("=" * 60)

    sender = TelegramSender(BOT_TOKEN, CHAT_ID)
    notifier = make_notifier(sender)

    monitor = LauncherMonitor(notifier)
    monitor.run()

if __name__ == "__main__":
    main()
