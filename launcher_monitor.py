import time
import requests

from config import POLL_SECONDS
from filters import find_keyword_matches


BOARD_URL = "https://hood.fun/api/board"

REQUEST_TIMEOUT = 10
RETRY_SECONDS = 5


class LauncherMonitor:

    def __init__(self, on_match):
        self.on_match = on_match
        self.seen_tokens = set()

    def _fetch_board(self):
        response = requests.get(
            BOARD_URL,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Robinhood-Radar/1.0",
                "Accept": "application/json",
            },
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(
                "Hood API beklenmeyen veri döndürdü."
            )

        tokens = data.get("tokens", [])

        if not isinstance(tokens, list):
            raise ValueError(
                "Hood API 'tokens' listesi bulunamadı."
            )

        return tokens

    def _detect_platform(self, launchpad):
        """
        Launchpad alanından platformu belirler.

        Önemli:
        Bu monitorün veri kaynağı hood.fun API olduğu için
        bilinmeyen launchpadleri otomatik olarak hood.fun
        kabul etmiyoruz.
        """

        value = str(
            launchpad or ""
        ).strip().lower()

        if not value:
            return "UNKNOWN"

        if "hood" in value:
            return "HOOD.FUN"

        if "stonk" in value:
            return "STONKBROKERS"

        return str(launchpad)

    def _normalize_token(self, token):

        address = token.get(
            "address",
            ""
        )

        creator = token.get(
            "creator",
            ""
        )

        launchpad = token.get(
            "launchpad",
            ""
        )

        name = token.get(
            "name",
            ""
        ) or ""

        symbol = token.get(
            "symbol",
            ""
        ) or ""

        created_at_block = token.get(
            "createdAtBlock",
            ""
        )

        platform = self._detect_platform(
            launchpad
        )

        return {
            "token": address,
            "creator": creator,
            "launch": launchpad,
            "platform": platform,
            "name": name,
            "symbol": symbol,
            "metadataURI": token.get(
                "metadataURI",
                ""
            ),
            "imageURI": "",
            "block": created_at_block,
            "tx_hash": "",
        }

    def _token_id(self, token):

        return (
            token.get("address")
            or (
                f"{token.get('name', '')}:"
                f"{token.get('symbol', '')}:"
                f"{token.get('createdAtBlock', '')}"
            )
        )

    def connect_check(self):

        print(
            "Hood.fun API kontrol ediliyor..."
        )

        tokens = self._fetch_board()

        print(
            f"Hood.fun API baglandi | "
            f"endpoint={BOARD_URL} | "
            f"tokens={len(tokens)}"
        )

        print(
            f"Polling: {POLL_SECONDS}s | "
            f"Kaynak: Hood.fun /api/board"
        )

    def _initial_snapshot(self, tokens):
        """
        Radar ilk açıldığında mevcut coinleri alarm olarak göndermez.
        Sadece mevcut listeyi hafızaya alır.
        """

        for token in tokens:

            token_id = self._token_id(
                token
            )

            if token_id:
                self.seen_tokens.add(
                    token_id
                )

        print(
            f"Ilk snapshot alindi | "
            f"Mevcut token={len(self.seen_tokens)}"
        )

    def _process_tokens(self, tokens):

        new_count = 0
        match_count = 0

        for raw_token in tokens:

            token_id = self._token_id(
                raw_token
            )

            if not token_id:
                continue

            if token_id in self.seen_tokens:
                continue

            self.seen_tokens.add(
                token_id
            )

            new_count += 1

            launch = self._normalize_token(
                raw_token
            )

            matches = find_keyword_matches(
                launch["name"],
                launch["symbol"],
            )

            print(
                f"Yeni coin | "
                f"{launch['name']} "
                f"({launch['symbol']}) | "
                f"platform={launch['platform']} | "
                f"token={launch['token']}"
            )

            if matches:

                match_count += 1

                print(
                    f"KEYWORD MATCH | "
                    f"{launch['name']} "
                    f"({launch['symbol']}) | "
                    f"platform={launch['platform']} | "
                    f"{matches}"
                )

                self.on_match(
                    launch,
                    matches,
                )

        return (
            new_count,
            match_count
        )

    def run(self):

        self.connect_check()

        tokens = self._fetch_board()

        self._initial_snapshot(
            tokens
        )

        print("=" * 60)
        print(
            "ROBINHOOD RADAR AKTIF"
        )
        print(
            "Kaynak: Hood.fun /api/board"
        )
        print(
            "Platform detection: AKTIF"
        )
        print(
            "Alchemy/RPC polling: DISABLED"
        )
        print(
            "LaunchCreated event polling: DISABLED"
        )
        print("=" * 60)

        while True:

            try:

                tokens = self._fetch_board()

                (
                    new_count,
                    match_count
                ) = self._process_tokens(
                    tokens
                )

                print(
                    f"Board tarandi | "
                    f"tokens={len(tokens)} | "
                    f"yeni={new_count} | "
                    f"match={match_count}"
                )

                time.sleep(
                    POLL_SECONDS
                )

            except requests.RequestException as exc:

                print(
                    f"Hood API hatasi: {exc}"
                )

                time.sleep(
                    RETRY_SECONDS
                )

            except ValueError as exc:

                print(
                    f"Board veri hatasi: {exc}"
                )

                time.sleep(
                    RETRY_SECONDS
                )

            except Exception as exc:

                print(
                    f"Monitor hatasi: {exc}"
                )

                time.sleep(
                    RETRY_SECONDS
                )
