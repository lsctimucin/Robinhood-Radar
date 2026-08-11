import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# TELEGRAM
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")


# ============================================================
# RADAR
# ============================================================

RADAR_NAME = "Robinhood Radar"

TARGET_SYMBOL = os.getenv("TARGET_SYMBOL", "CLOCKIN")


# ============================================================
# ROBINHOOD CHAIN RPC
# ============================================================

RPC_URL = os.getenv("RPC_URL", "")

CHAIN_ID = 4663


# ============================================================
# LAUNCHER FACTORY
# ============================================================

LAUNCHER_FACTORY = os.getenv(
    "LAUNCHER_FACTORY",
    "0x631f9371Fd6B2C85F8f61d19A90547eE67Fa61A2"
)


# ============================================================
# POLLING
# ============================================================

# RPC'yi ekonomik kullanmak için
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))

# Tek RPC log sorgusunda taranacak maksimum block sayısı
BLOCK_BATCH_SIZE = int(os.getenv("BLOCK_BATCH_SIZE", "50"))
