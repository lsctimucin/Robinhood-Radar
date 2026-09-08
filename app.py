from config import BOT_TOKEN, CHAT_ID, TARGET_TOKEN
from telegram_sender import TelegramSender
from launcher_monitor import LaptopLaunchMonitor


def main():
    print("=" * 60)
    print("LAPTOP WATCH")
    print("Network: Base")
    print(f"Target token: {TARGET_TOKEN}")
    print("Mode: liquidity / pool candidate + trading activation")
    print("=" * 60)

    sender = TelegramSender(BOT_TOKEN, CHAT_ID)
    monitor = LaptopLaunchMonitor(sender)
    monitor.run()


if __name__ == "__main__":
    main()
