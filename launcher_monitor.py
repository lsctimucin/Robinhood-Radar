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
                request_kwargs={"timeout": 30},
            )
        )

        self.factory = self.w3.eth.contract(
            address=Web3.to_checksum_address(LAUNCHER_FACTORY),
            abi=LAUNCH_CREATED_ABI,
        )

        self.last_block = None

        self.event_signature = Web3.keccak(
            text=(
                "LaunchCreated("
                "address,address,address,string,string,string,string"
                ")"
            )
        ).hex()

    def connect_check(self):
        if not self.w3.is_connected():
            raise RuntimeError(
                f"Robinhood RPC baglanamadi: {RPC_URL}"
            )

        chain_id = self.w3.eth.chain_id

        if chain_id != 4663:
            raise RuntimeError(
                f"Yanlis chain ID: {chain_id}, beklenen: 4663"
            )

        latest = self.w3.eth.block_number

        print(
            f"Robinhood Chain baglandi | "
            f"chain_id={chain_id} | block={latest}"
        )

        print(
            f"Launcher Factory: {LAUNCHER_FACTORY}"
        )

        print("LaunchCreated dinleniyor...")

    def _get_logs(self, from_block, to_block):
        return self.w3.eth.get_logs(
            {
                "address": Web3.to_checksum_address(
                    LAUNCHER_FACTORY
                ),
                "topics": [self.event_signature],
                "fromBlock": from_block,
                "toBlock": to_block,
            }
        )

    def _decode(self, raw_log):
        event = self.factory.events.LaunchCreated().process_log(
            raw_log
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
            "tx_hash": raw_log["transactionHash"].hex(),
        }

    def run(self):
        self.connect_check()

        self.last_block = self.w3.eth.block_number

        print(
            f"Baslangic block: {self.last_block}"
        )

        while True:
            try:
                latest = self.w3.eth.block_number

                if latest > self.last_block:

                    start = self.last_block + 1

                    # RPC'yi yormamak için maksimum 20 blok.
                    safe_batch_size = min(
                        BLOCK_BATCH_SIZE,
                        20,
                    )

                    end = min(
                        start + safe_batch_size - 1,
                        latest,
                    )

                    logs = self._get_logs(
                        start,
                        end,
                    )

                    for raw_log in logs:

                        launch = self._decode(
                            raw_log
                        )

                        matches = find_keyword_matches(
                            launch["name"],
                            launch["symbol"],
                        )

                        print(
                            f"LaunchCreated | "
                            f"{launch['name']} "
                            f"({launch['symbol']}) | "
                            f"token={launch['token']} | "
                            f"block={launch['block']}"
                        )

                        if matches:

                            print(
                                f"KEYWORD MATCH | "
                                f"{matches}"
                            )

                            self.on_match(
                                launch,
                                matches,
                            )

                    # Sadece RPC isteği başarıyla tamamlandıysa
                    # last_block ilerler.
                    self.last_block = end

                time.sleep(POLL_SECONDS)

            except (
                Web3Exception,
                ValueError,
                ConnectionError,
            ) as exc:

                print(
                    f"RPC/log hatasi: {exc}"
                )

                # Event kaçırmamak için last_block
                # değiştirilmez.
                time.sleep(5)

            except Exception as exc:

                print(
                    f"Monitor hatasi: {exc}"
                )

                time.sleep(5)
