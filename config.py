import os


# ==============================
# TELEGRAM
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# ==============================
# TARGET
# ==============================

TARGET_SYMBOL = os.getenv("TARGET_SYMBOL", "$CLOCKIN")


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

# RPC kullanımını ekonomik tutmak için
POLL_SECONDS = 3

# Tek sorguda maksimum taranacak blok
BLOCK_BATCH_SIZE = 50
