import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

# Robinhood Chain mainnet
RPC_URL = os.getenv(
    "ROBINHOOD_RPC_URL",
    "https://rpc.mainnet.chain.robinhood.com"
)

CHAIN_ID = 4663

# StonkBrokers Launcher Factory
LAUNCHER_FACTORY = os.getenv(
    "LAUNCHER_FACTORY",
    "0x631f9371Fd6B2C85F8f61d19A90547eE67Fa61A2"
)

POLL_SECONDS = float(os.getenv("POLL_SECONDS", "1.0"))
BLOCK_BATCH_SIZE = int(os.getenv("BLOCK_BATCH_SIZE", "20"))

# Radar identity
RADAR_NAME = "Robinhood Radar"
TARGET_SYMBOL = "CLOCKIN"
