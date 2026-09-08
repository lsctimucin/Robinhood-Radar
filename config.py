import os
from dotenv import load_dotenv

load_dotenv()

# TELEGRAM
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

# RADAR
RADAR_NAME = "LAPTOP WATCH"

# BASE
RPC_URL = os.getenv("RPC_URL", "")
CHAIN_ID = 8453

# Exact token to watch
TARGET_TOKEN = os.getenv(
    "TARGET_TOKEN",
    "0xB095274743941e953c746F9C228DA9c18Bb6ec29"
)

# Fast polling. 0.7s is intentionally aggressive for launch watch.
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "0.7"))

# Telegram dedupe / candidate tracking
MAX_SEEN_TX = 5000
