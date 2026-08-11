import os


# ==============================
# TELEGRAM
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# ==============================
# ROBINHOOD CHAIN RPC
# ==============================

RPC_URL = os.getenv("RPC_URL")


# ==============================
# LAUNCHER
# ==============================

LAUNCHER_FACTORY = os.getenv("LAUNCHER_FACTORY")


# ==============================
# MONITOR SETTINGS
# ==============================

# Alchemy RPC kullanımını ekonomik tutmak için
POLL_SECONDS = 3

# Bir RPC log sorgusunda taranacak maksimum blok
BLOCK_BATCH_SIZE = 50
