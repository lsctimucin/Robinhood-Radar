import time

from web3 import Web3
from web3.exceptions import Web3Exception

from config import (
    RPC_URL,
    LAUNCHER_FACTORY,
    POLL_SECONDS,
    BLOCK_BATCH_SIZE,
)

from filters import find_keyword_matches


# ============================================================
# STONK LAUNCHER - LaunchCreated EVENT
# ============================================================

LAUNCH_CREATED_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "creator",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "token",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "launch",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "name",
                "type": "string",
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "symbol",
                "type": "string",
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "metadataURI",
                "type": "string",
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "imageURI",
                "type": "string",
            },
        ],
        "name": "LaunchCreated",
        "type": "event",
    }
]


class LauncherMonitor:

    def __init__(self, on_match):
        self.on_match = on_match

        self.w3 = Web3(
            Web3.HTTPProvider(
                RPC_URL,
                request_kwargs={
                    "timeout": 10
                },
            )
        )

        self.factory_address = Web3.to_checksum_address(
            LAUNCHER_FACTORY
        )

        self.factory = self.w3.eth.contract(
            address=self.factory_address,
            abi=LAUNCH_CREATED_ABI,
        )

        self.last_block = None
        self.processed_transactions = set()

        # RPC'nin istediği 0x prefix'i garanti ediyoruz.
        topic = Web3.keccak(
            text=(
                "LaunchCreated("
                "address,address,address,"
                "string,string,string,string"
                ")"
            )
        ).hex()

        if not topic.startswith("0x"):
            topic = "0x" + topic

        self.event_signature = topic

    # ========================================================
    # CONNECTION CHECK
    # ========================================================

    def connect_check(self):

        if not self.w3.is_connected():
            raise RuntimeError(
                f"Robinhood RPC baglanamadi: {RPC_URL}"
            )

        chain_id = self.w3.eth.chain_id

        if chain_id != 4663:
            raise RuntimeError(
                f"Yanlis chain ID: {chain_id} | "
                f"Beklenen: 4663"
            )

        latest_block = self.w3.eth.block_number

        print(
            f"Robinhood Chain baglandi | "
            f"chain_id={chain_id} | "
            f"block={latest_block}"
        )

        print(
            f"Launcher Factory: "
            f"{LAUNCHER_FACTORY}"
        )

        print(
            f"LaunchCreated topic: "
            f"{self.event_signature}"
        )

        print(
            f"Polling: {POLL_SECONDS}s | "
            f"Batch: {BLOCK_BATCH_SIZE} blocks"
        )

    # ========================================================
    # LOG FETCH
    # ========================================================

    def _get_logs(self, from_block, to_block):

        return self.w3.eth.get_logs(
            {
                "address": self.factory_address,
                "topics": [
                    self.event_signature
                ],
                "fromBlock": from_block,
                "toBlock": to_block,
            }
        )

    # ========================================================
    # EVENT DECODE
    # ========================================================

    def _decode_launch(self, raw_log):

        event = (
            self.factory.events
            .LaunchCreated()
            .process_log(raw_log)
        )

        args = event["args"]

        return {
            "creator": args["creator"],
            "token": args["token"],
            "launch": args["launch"],
            "name": args["name"],
            "symbol": args["symbol"],
            "metadataURI": args["metadataURI"],
            "imageURI": args["imageURI"],
            "block": raw_log["blockNumber"],
            "tx_hash": raw_log[
                "transactionHash"
            ].hex(),
        }

    # ========================================================
    # PROCESS EVENT
    # ========================================================

    def _process_launch(self, raw_log):

        tx_hash = raw_log[
            "transactionHash"
        ].hex()

        if tx_hash in self.processed_transactions:
            return False

        self.processed_transactions.add(
            tx_hash
        )

        # Hafiza gereksiz buyumesin.
        if len(self.processed_transactions) > 10000:
            self.processed_transactions.clear()
            self.processed_transactions.add(
                tx_hash
            )

        launch = self._decode_launch(
            raw_log
        )

        name = launch["name"]
        symbol = launch["symbol"]

        print(
            f"LaunchCreated | "
            f"{name} ({symbol}) | "
            f"creator={launch['creator']} | "
            f"token={launch['token']} | "
            f"launch={launch['launch']} | "
            f"block={launch['block']}"
        )

        matches = find_keyword_matches(
            name,
            symbol,
        )

        if not matches:
            return False

        print(
            f"KEYWORD MATCH | "
            f"{name} ({symbol}) | "
            f"matches={matches}"
        )

        self.on_match(
            launch,
            matches,
        )

        return True

    # ========================================================
    # MAIN LOOP
    # ========================================================

    def run(self):

        self.connect_check()

        self.last_block = (
            self.w3.eth.block_number
        )

        print(
            f"Baslangic block: "
            f"{self.last_block}"
        )

        print("=" * 60)
        print("ROBINHOOD RADAR AKTIF")
        print("Kaynak: Stonk Launcher")
        print(
            f"Factory: {LAUNCHER_FACTORY}"
        )
        print("Event: LaunchCreated")
        print("Hood.fun API: DISABLED")
        print(
            "Alchemy/RPC polling: "
            "SADECE EVENT KONTROLU"
        )
        print("=" * 60)

        while True:

            try:

                latest_block = (
                    self.w3.eth.block_number
                )

                if latest_block > self.last_block:

                    from_block = (
                        self.last_block + 1
                    )

                    to_block = min(
                        from_block
                        + BLOCK_BATCH_SIZE
                        - 1,
                        latest_block,
                    )

                    logs = self._get_logs(
                        from_block,
                        to_block,
                    )

                    print(
                        f"Block taraniyor: "
                        f"{from_block} -> "
                        f"{to_block} | "
                        f"LaunchCreated="
                        f"{len(logs)}"
                    )

                    for raw_log in logs:

                        try:

                            self._process_launch(
                                raw_log
                            )

                        except Exception as exc:

                            print(
                                "Launch event "
                                f"parse hatasi: {exc}"
                            )

                    self.last_block = to_block

                time.sleep(
                    POLL_SECONDS
                )

            except (
                Web3Exception,
                ValueError,
                ConnectionError,
            ) as exc:

                print(
                    f"RPC/log hatasi: {exc}"
                )

                time.sleep(5)

            except Exception as exc:

                print(
                    f"Monitor hatasi: {exc}"
                )

                time.sleep(5)
