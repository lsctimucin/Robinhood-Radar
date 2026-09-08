import time

from web3 import Web3
from web3.exceptions import Web3Exception

from config import (
    RPC_URL,
    CHAIN_ID,
    TARGET_TOKEN,
    POLL_SECONDS,
    MAX_SEEN_TX,
)


TRANSFER_TOPIC = Web3.keccak(
    text="Transfer(address,address,uint256)"
).hex()

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def _topic_to_address(topic):
    h = topic.hex() if hasattr(topic, "hex") else str(topic)
    if h.startswith("0x"):
        h = h[2:]
    return Web3.to_checksum_address("0x" + h[-40:])


def _hex_hash(value):
    if hasattr(value, "hex"):
        result = value.hex()
        return result if result.startswith("0x") else "0x" + result
    value = str(value)
    return value if value.startswith("0x") else "0x" + value


class LaptopLaunchMonitor:
    def __init__(self, sender):
        self.sender = sender
        self.w3 = Web3(
            Web3.HTTPProvider(
                RPC_URL,
                request_kwargs={"timeout": 8},
            )
        )

        self.token = Web3.to_checksum_address(TARGET_TOKEN)
        self.last_block = None

        self.seen_logs = set()
        self.candidate_contracts = set()
        self.candidate_directions = {}

        self.pool_alert_sent = set()
        self.trading_alert_sent = set()

    def _send(self, text):
        print("\n" + "=" * 60)
        print(text)
        print("=" * 60 + "\n")
        self.sender.send_message(text)

    def _connect_check(self):
        if not RPC_URL:
            raise RuntimeError("RPC_URL Railway variable bos.")

        if not self.w3.is_connected():
            raise RuntimeError("Base RPC baglanamadi.")

        chain_id = self.w3.eth.chain_id
        if chain_id != CHAIN_ID:
            raise RuntimeError(
                f"Yanlis chain ID: {chain_id} | Beklenen Base: {CHAIN_ID}"
            )

        code = self.w3.eth.get_code(self.token)
        latest = self.w3.eth.block_number

        print(
            f"Base connected | chain_id={chain_id} | "
            f"block={latest} | token_code_bytes={len(code)}"
        )

    def _get_token_logs(self, from_block, to_block):
        return self.w3.eth.get_logs(
            {
                "address": self.token,
                "topics": [TRANSFER_TOPIC],
                "fromBlock": from_block,
                "toBlock": to_block,
            }
        )

    def _is_contract(self, address):
        if address.lower() == ZERO_ADDRESS:
            return False
        try:
            return len(self.w3.eth.get_code(address)) > 0
        except Exception:
            return False

    def _remember(self, key):
        self.seen_logs.add(key)
        if len(self.seen_logs) > MAX_SEEN_TX:
            # We only need a bounded launch-time dedupe cache.
            self.seen_logs.clear()
            self.seen_logs.add(key)

    def _pool_candidate_alert(self, contract_address, tx_hash, block_number):
        if contract_address in self.pool_alert_sent:
            return

        self.pool_alert_sent.add(contract_address)

        self._send(
            "🚨🚨 LAPTOP LIQUIDITY / POOL SIGNAL 🚨🚨\n\n"
            "🌐 Base\n"
            f"🪙 CA: {self.token}\n\n"
            "🔥 TOKEN TRANSFER TO CONTRACT DETECTED\n"
            "⚠️ Possible liquidity / pool activation\n\n"
            f"🏊 Contract: {contract_address}\n"
            f"🧱 Block: {block_number}\n"
            f"🔗 TX: https://basescan.org/tx/{tx_hash}\n\n"
            "➡️ GMGN READY"
        )

    def _trading_alert(self, contract_address, tx_hash, block_number):
        if contract_address in self.trading_alert_sent:
            return

        self.trading_alert_sent.add(contract_address)

        self._send(
            "🚨🚨🚨 LAPTOP TRADING LIVE 🚨🚨🚨\n\n"
            "🌐 Base\n"
            f"🪙 CA: {self.token}\n\n"
            "🔥 BIDIRECTIONAL TOKEN FLOW DETECTED\n"
            "🔥 Pool/contract has both received and sent LAPTOP\n"
            "✅ Strong trading activation signal\n\n"
            f"🏊 Contract: {contract_address}\n"
            f"🧱 Block: {block_number}\n"
            f"🔗 TX: https://basescan.org/tx/{tx_hash}\n\n"
            "➡️ BUY CHECK NOW"
        )

    def _process_log(self, log):
        topics = log.get("topics", [])
        if len(topics) < 3:
            return

        tx_hash = _hex_hash(log["transactionHash"])
        log_index = int(log["logIndex"])
        key = f"{tx_hash}:{log_index}"

        if key in self.seen_logs:
            return

        self._remember(key)

        from_addr = _topic_to_address(topics[1])
        to_addr = _topic_to_address(topics[2])
        block_number = int(log["blockNumber"])

        try:
            amount = int(log["data"].hex(), 16)
        except Exception:
            amount = 0

        print(
            f"LAPTOP Transfer | block={block_number} | "
            f"from={from_addr} | to={to_addr} | amount_raw={amount} | "
            f"tx={tx_hash}"
        )

        # Ignore pure mint creation as liquidity/trading.
        from_is_zero = from_addr.lower() == ZERO_ADDRESS
        to_is_zero = to_addr.lower() == ZERO_ADDRESS

        # Any non-zero transfer INTO a contract is an immediate pool/liquidity
        # candidate. This is intentionally generic so it does not depend on
        # knowing the DEX in advance.
        if not from_is_zero and not to_is_zero and amount > 0:
            if self._is_contract(to_addr):
                self.candidate_contracts.add(to_addr)
                dirs = self.candidate_directions.setdefault(to_addr, set())
                dirs.add("IN")
                self._pool_candidate_alert(
                    to_addr, tx_hash, block_number
                )

            if self._is_contract(from_addr):
                self.candidate_contracts.add(from_addr)
                dirs = self.candidate_directions.setdefault(from_addr, set())
                dirs.add("OUT")

        # Stronger confirmation: same contract appears on both sides across
        # token transfers. Typical pool activity does this once swaps begin.
        for candidate in (from_addr, to_addr):
            if candidate not in self.candidate_contracts:
                continue

            dirs = self.candidate_directions.setdefault(candidate, set())

            if to_addr == candidate and not from_is_zero:
                dirs.add("IN")

            if from_addr == candidate and not to_is_zero:
                dirs.add("OUT")

            if "IN" in dirs and "OUT" in dirs:
                self._trading_alert(
                    candidate, tx_hash, block_number
                )

    def run(self):
        self._connect_check()

        # Start one block behind current tip to avoid missing a race during boot.
        self.last_block = max(self.w3.eth.block_number - 1, 0)

        self._send(
            "🟢 LAPTOP WATCH ONLINE\n\n"
            "🌐 Base\n"
            f"🪙 CA: {self.token}\n"
            f"⚡ Poll: {POLL_SECONDS}s\n\n"
            "Watching:\n"
            "1) token transfer to contract → LIQUIDITY/POOL SIGNAL\n"
            "2) same contract IN + OUT → TRADING LIVE"
        )

        print(f"Start block: {self.last_block}")

        while True:
            try:
                latest = self.w3.eth.block_number

                if latest > self.last_block:
                    # Base blocks are fast. Read each new range immediately.
                    logs = self._get_token_logs(
                        self.last_block + 1,
                        latest,
                    )

                    if logs:
                        print(
                            f"Block {self.last_block + 1}->{latest} | "
                            f"LAPTOP transfers={len(logs)}"
                        )

                    for log in logs:
                        try:
                            self._process_log(log)
                        except Exception as exc:
                            print(f"Transfer parse error: {exc}")

                    self.last_block = latest

                time.sleep(POLL_SECONDS)

            except (
                Web3Exception,
                ValueError,
                ConnectionError,
            ) as exc:
                print(f"RPC/log error: {exc}")
                time.sleep(2)

            except Exception as exc:
                print(f"Monitor error: {exc}")
                time.sleep(2)
