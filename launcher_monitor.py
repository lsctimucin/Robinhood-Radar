# ============================================================
# ROBINHOOD RADAR
# LAUNCHER MONITOR - HOOD.FUN API FINAL
# ============================================================
#
# Kaynak:
#   https://hood.fun/api/board
#
# Akış:
#
#   hood.fun/api/board
#          ↓
#   yeni token kontrolü
#          ↓
#   name + symbol
#          ↓
#   callback(new_token)
#          ↓
#   Patoshi / keyword / creator filtreleri
#          ↓
#   Telegram
#
# ÖNEMLİ:
# - Alchemy RPC KULLANMAZ
# - RPC_URL KULLANMAZ
# - Blockchain polling KULLANMAZ
# - Alchemy kredisi harcamaz
#
# ============================================================

import json
import os
import threading
import time

import requests


# ============================================================
# AYARLAR
# ============================================================

BOARD_URL = os.getenv(
    "HOOD_BOARD_URL",
    "https://hood.fun/api/board"
).strip()

POLL_SECONDS = int(
    os.getenv("HOOD_POLL_SECONDS", "5")
)

HTTP_TIMEOUT = int(
    os.getenv("HOOD_HTTP_TIMEOUT", "10")
)


# ============================================================
# DURUM
# ============================================================

_running = False
_thread = None

_callback = None

_seen_addresses = set()
_seen_lock = threading.Lock()


# ============================================================
# LOG
# ============================================================

def log(message):
    print(message, flush=True)


# ============================================================
# CALLBACK
# ============================================================

def set_callback(callback):
    global _callback

    _callback = callback

    log(
        "🧩 HOOD.FUN CALLBACK HAZIR."
    )


# ============================================================
# HTTP
# ============================================================

def _fetch_board():
    try:
        response = requests.get(
            BOARD_URL,
            timeout=HTTP_TIMEOUT,
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "Robinhood-Radar/1.0"
                ),
            },
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            log(
                "⚠️ HOOD.FUN API beklenmeyen cevap."
            )
            return []

        tokens = data.get("tokens")

        if not isinstance(tokens, list):
            log(
                "⚠️ HOOD.FUN API 'tokens' alanı bulunamadı."
            )
            return []

        return tokens

    except requests.RequestException as exc:
        log(
            f"⚠️ HOOD.FUN HTTP HATASI => {exc}"
        )
        return []

    except ValueError as exc:
        log(
            f"⚠️ HOOD.FUN JSON HATASI => {exc}"
        )
        return []

    except Exception as exc:
        log(
            f"❌ HOOD.FUN API HATASI => {exc}"
        )
        return []


# ============================================================
# TOKEN NORMALIZE
# ============================================================

def _normalize_token(item):
    if not isinstance(item, dict):
        return None

    address = str(
        item.get("address", "")
    ).strip()

    if not address:
        return None

    name = str(
        item.get("name", "")
    ).strip()

    symbol = str(
        item.get("symbol", "")
    ).strip()

    creator = str(
        item.get("creator", "")
    ).strip()

    launchpad = str(
        item.get("launchpad", "")
    ).strip()

    timestamp = item.get(
        "timestamp"
    )

    created_at_block = item.get(
        "createdAtBlock"
    )

    curve = item.get(
        "curve"
    )

    if not isinstance(curve, dict):
        curve = {}

    virtual_eth = curve.get(
        "virtualEth"
    )

    real_eth = curve.get(
        "realEth"
    )

    graduated = bool(
        curve.get(
            "graduated",
            False
        )
    )

    migrated = bool(
        curve.get(
            "migrated",
            False
        )
    )

    # --------------------------------------------------------
    # Patoshi Radar / mevcut app.py uyumluluğu
    # --------------------------------------------------------
    #
    # app.py şu alanları bekliyor:
    #
    # mint
    # traderPublicKey
    # name
    # symbol
    # marketCapSol
    #
    # Robinhood Chain tarafında bunların karşılığı:
    #
    # address  -> mint
    # creator  -> traderPublicKey
    #
    # --------------------------------------------------------

    normalized = {
        "mint": address,
        "traderPublicKey": creator,

        "name": name or "Bilinmiyor",
        "symbol": symbol or "-",

        # Board şu anda doğrudan SOL market cap
        # vermiyor.
        "marketCapSol": 0,

        # Robinhood'a özgü bilgiler
        "marketCapEth": None,

        "address": address,
        "creator": creator,
        "launchpad": launchpad,

        "timestamp": timestamp,
        "createdAtBlock": created_at_block,

        "virtualEth": virtual_eth,
        "realEth": real_eth,

        "graduated": graduated,
        "migrated": migrated,

        # Kaynağın tamamını kaybetmeyelim.
        "hood_raw": item,
    }

    return normalized


# ============================================================
# YENİ TOKEN KONTROLÜ
# ============================================================

def _process_tokens(tokens):
    new_count = 0

    for item in tokens:

        token = _normalize_token(item)

        if not token:
            continue

        address = token["mint"]

        with _seen_lock:

            if address in _seen_addresses:
                continue

            _seen_addresses.add(address)

        new_count += 1

        name = token.get(
            "name",
            "Bilinmiyor"
        )

        symbol = token.get(
            "symbol",
            "-"
        )

        log(
            "🆕 HOOD.FUN TOKEN => "
            f"{name} ({symbol}) | {address}"
        )

        # ----------------------------------------------------
        # Callback
        # ----------------------------------------------------

        if _callback:

            try:
                _callback(token)

            except Exception as exc:

                log(
                    "❌ HOOD.FUN CALLBACK HATASI => "
                    f"{exc}"
                )

                # Callback hatası bütün radarın
                # durmasına sebep olmasın.

    return new_count


# ============================================================
# POLLING LOOP
# ============================================================

def _worker():

    global _running

    log(
        "🌐 HOOD.FUN BOARD MONITOR BAŞLADI."
    )

    log(
        f"📡 Kaynak: {BOARD_URL}"
    )

    log(
        f"⏱ Polling: {POLL_SECONDS}s"
    )

    log(
        "💳 Alchemy: KULLANILMIYOR"
    )

    # --------------------------------------------------------
    # İlk çekim
    #
    # İlk çalıştırmada board'daki mevcut tokenların tamamını
    # yeni token olarak Telegram'a göndermemek için sadece
    # cache'e alıyoruz.
    # --------------------------------------------------------

    initial_tokens = _fetch_board()

    initial_count = 0

    for item in initial_tokens:

        token = _normalize_token(item)

        if not token:
            continue

        address = token["mint"]

        with _seen_lock:
            _seen_addresses.add(address)

        initial_count += 1

    log(
        f"📦 İlk board senkronizasyonu: "
        f"{initial_count} token"
    )

    # --------------------------------------------------------
    # Sürekli takip
    # --------------------------------------------------------

    while _running:

        try:

            tokens = _fetch_board()

            if tokens:

                new_count = _process_tokens(
                    tokens
                )

                if new_count:
                    log(
                        f"📥 Yeni token: "
                        f"{new_count}"
                    )

        except Exception as exc:

            log(
                f"❌ HOOD.FUN POLLING HATASI => "
                f"{exc}"
            )

        time.sleep(
            POLL_SECONDS
        )


# ============================================================
# START
# ============================================================

def start():

    global _running
    global _thread

    if _running:
        log(
            "⚠️ HOOD.FUN MONITOR zaten çalışıyor."
        )
        return

    _running = True

    _thread = threading.Thread(
        target=_worker,
        daemon=True,
        name="HoodBoardMonitor",
    )

    _thread.start()


# ============================================================
# STOP
# ============================================================

def stop():

    global _running
    global _thread

    _running = False

    if _thread:
        _thread.join(
            timeout=2
        )

    _thread = None

    log(
        "🛑 HOOD.FUN MONITOR durduruldu."
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    def test_callback(data):

        print(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            )
        )

    set_callback(
        test_callback
    )

    start()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        stop()
