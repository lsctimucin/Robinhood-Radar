import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# TELEGRAM
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")


# ============================================================
# ROBINHOOD CHAIN / RPC
# ============================================================

RPC_URL = os.getenv("RPC_URL", "")

# Robinhood Chain
CHAIN_ID = 4663

# Launcher Factory
LAUNCHER_FACTORY = os.getenv(
    "LAUNCHER_FACTORY",
    "0x631f9371Fd6B2C85F8f61d19A90547eE67Fa61A2"
)


# ============================================================
# TARGET
# ============================================================

# app.py bunu import ediyor.
# Şimdilik test amacıyla CLOCKIN.
TARGET_SYMBOL = os.getenv("TARGET_SYMBOL", "CLOCKIN")


# ============================================================
# POLLING / RPC EKONOMİ
# ============================================================

# Her 5 saniyede bir yeni block kontrol edilir.
# Yeni block'lar kaçırılmaz; bir sonraki sorguda topluca taranır.
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))

# Tek get_logs çağrısında maksimum 50 block.
# 5 saniyede bir kontrol edildiği için normal durumda
# tek sorguda birkaç block gelir.
BLOCK_BATCH_SIZE = int(os.getenv("BLOCK_BATCH_SIZE", "50"))
