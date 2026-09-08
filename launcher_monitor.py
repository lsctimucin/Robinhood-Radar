import queue
import threading
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

# Common EVM DEX swap event families used by Uniswap-compatible / Solidly-style
# pools on Base. Verification runs ONLY in the background worker.
SWAP_V2_TOPIC = Web3.keccak(
    text="Swap(address,uint256,uint256,uint256,uint256,address)"
).hex()

SWAP_V3_TOPIC = Web3.keccak(
    text="Swap(address,address,int256,int256,uint160,uint128,int24)"
).hex()

SWAP_TOPICS = {
    SWAP_V2_TOPIC.lower(): "V2 / Solidly-compatible Swap",
    SWAP_V3_TOPIC.lower(): "V3-compatible Swap",
}

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# token0() / token1() selectors. These work for the major Uniswap-compatible
# pool families and give an extra pair-level verification when available.
TOKEN0_SELECTOR = "0x0dfe1681"
TOKEN1_SELECTOR = "0xd21220a7"


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


def _topic_hex(topic):
    if hasattr(topic, "hex"):
        value = topic.hex()
    else:
        value = str(topic)
    return value if value.startswith("0x") else "0x" + value


def _decode_address_word(raw):
    if raw is None:
        return None

    if isinstance(raw, (bytes, bytearray)):
        h = raw.hex()
    else:
        h = str(raw)
        if h.startswith("0x"):
            h = h[2:]

    if len(h) < 40:
        return None

    try:
        return Web3.to_checksum_address("0x" + h[-40:])
    except Exception:
        return None


class LaptopLaunchMonitor:
    def __init__(self, sender):
        self.sender = sender

        # Main polling client: kept dedicated to the speed-critical monitor.
        self.w3 = Web3(
            Web3.HTTPProvider(
                RPC_URL,
                request_kwargs={"timeout": 8},
            )
        )

        # Separate RPC client for background swap confirmation so receipt /
        # pool calls cannot block the main transfer polling loop.
        self.confirm_w3 = Web3(
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

        # Background FIRST SWAP confirmation.
        self.confirm_queue = queue.Queue(maxsize=256)
        self.confirm_queued = set()
        self.confirm_queued_lock = threading.Lock()
        self.first_swap_alert_sent = False
        self.first_swap_lock = threading.Lock()
        self.confirm_thread = None

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

    def _first_swap_alert(
        self,
        pool_address,
        tx_hash,
        block_number,
        swap_family,
        pair_verified,
        router_address,
    ):
        with self.first_swap_lock:
            if self.first_swap_alert_sent:
                return
            self.first_swap_alert_sent = True

        pair_line = (
            "✅ Pair token check: LAPTOP verified\n"
            if pair_verified
            else "✅ Swap pool linked to LAPTOP transfer\n"
        )

        router_line = ""
        if router_address:
            router_line = f"🧭 Router/Executor: {router_address}\n"

        self._send(
            "🚨🚨🚨 LAPTOP FIRST SWAP / TRADING CONFIRMED 🚨🚨🚨\n\n"
            "🌐 Base\n"
            f"🪙 CA: {self.token}\n\n"
            "🔥 REAL DEX SWAP EVENT DETECTED\n"
            f"✅ {swap_family}\n"
            f"{pair_line}"
            "✅ ON-CHAIN TRADING CONFIRMED\n\n"
            f"🏊 Pool: {pool_address}\n"
            f"{router_line}"
            f"🧱 Block: {block_number}\n"
            f"🔗 TX: https://basescan.org/tx/{tx_hash}\n\n"
            "➡️ GMGN: TRADING CONFIRMED"
        )

    def _queue_confirmation(self, candidate, tx_hash, block_number):
        # Never block the main polling path.
        with self.first_swap_lock:
            if self.first_swap_alert_sent:
                return

        key = f"{candidate.lower()}:{tx_hash.lower()}"

        with self.confirm_queued_lock:
            if key in self.confirm_queued:
                return
            self.confirm_queued.add(key)

        try:
            self.confirm_queue.put_nowait(
                (candidate, tx_hash, block_number, key)
            )
        except queue.Full:
            with self.confirm_queued_lock:
                self.confirm_queued.discard(key)
            print(
                "Swap confirmation queue full; "
                f"skipping candidate={candidate} tx={tx_hash}"
            )

    def _pool_contains_target(self, pool_address):
        """
        Return True when token0/token1 explicitly contains LAPTOP.
        Return False when both calls succeed and neither is LAPTOP.
        Return None when this pool family does not expose token0/token1.
        """
        try:
            token0_raw = self.confirm_w3.eth.call(
                {
                    "to": Web3.to_checksum_address(pool_address),
                    "data": TOKEN0_SELECTOR,
                }
            )
            token1_raw = self.confirm_w3.eth.call(
                {
                    "to": Web3.to_checksum_address(pool_address),
                    "data": TOKEN1_SELECTOR,
                }
            )

            token0 = _decode_address_word(token0_raw)
            token1 = _decode_address_word(token1_raw)

            if not token0 or not token1:
                return None

            target = self.token.lower()
            return token0.lower() == target or token1.lower() == target

        except Exception:
            return None

    def _find_swap_event(self, receipt, candidate):
        candidate_lower = candidate.lower()

        for event_log in receipt.get("logs", []):
            topics = event_log.get("topics", [])
            if not topics:
                continue

            topic0 = _topic_hex(topics[0]).lower()
            swap_family = SWAP_TOPICS.get(topic0)
            if not swap_family:
                continue

            try:
                emitter = Web3.to_checksum_address(event_log["address"])
            except Exception:
                continue

            # Strongest path: a known Swap signature emitted by the exact
            # contract already observed moving LAPTOP.
            if emitter.lower() == candidate_lower:
                pair_verified = self._pool_contains_target(emitter)

                # Even if token0/token1 is unsupported, the emitter is already
                # cryptographically linked to LAPTOP by the Transfer log that
                # queued this exact candidate/transaction.
                if pair_verified is not False:
                    return emitter, swap_family, pair_verified is True

                # Defensive fallback: if token0/token1 explicitly says the
                # candidate does NOT contain LAPTOP, do not confirm it.
                continue

            # A swap can be emitted by another pool inside the same routed tx.
            # Confirm that pool only when token0/token1 explicitly contains
            # LAPTOP.
            pair_verified = self._pool_contains_target(emitter)
            if pair_verified is True:
                return emitter, swap_family, True

        return None

    def _confirm_worker(self):
        print("Background FIRST SWAP confirmation worker online.")

        while True:
            candidate, tx_hash, block_number, key = self.confirm_queue.get()

            try:
                with self.first_swap_lock:
                    if self.first_swap_alert_sent:
                        continue

                receipt = None

                # A Transfer log normally means the receipt is already
                # available, but short retries make the worker resilient to an
                # RPC node briefly lagging behind. This sleep is BACKGROUND
                # ONLY and never delays the main monitor.
                for attempt in range(3):
                    try:
                        receipt = self.confirm_w3.eth.get_transaction_receipt(
                            tx_hash
                        )
                        break
                    except Exception as exc:
                        if attempt == 2:
                            print(
                                "Swap receipt check failed | "
                                f"tx={tx_hash} | error={exc}"
                            )
                        else:
                            time.sleep(0.20)

                if receipt is None:
                    continue

                status = int(receipt.get("status", 1))
                if status != 1:
                    continue

                found = self._find_swap_event(receipt, candidate)
                if not found:
                    continue

                pool_address, swap_family, pair_verified = found

                router_address = None
                try:
                    tx = self.confirm_w3.eth.get_transaction(tx_hash)
                    tx_to = tx.get("to")
                    if tx_to:
                        router_address = Web3.to_checksum_address(tx_to)
                except Exception:
                    pass

                receipt_block = int(
                    receipt.get("blockNumber", block_number)
                )

                self._first_swap_alert(
                    pool_address=pool_address,
                    tx_hash=tx_hash,
                    block_number=receipt_block,
                    swap_family=swap_family,
                    pair_verified=pair_verified,
                    router_address=router_address,
                )

            except Exception as exc:
                print(
                    "Background swap confirmation error | "
                    f"candidate={candidate} | tx={tx_hash} | error={exc}"
                )

            finally:
                with self.confirm_queued_lock:
                    self.confirm_queued.discard(key)
                self.confirm_queue.task_done()

    def _start_confirmation_worker(self):
        if self.confirm_thread and self.confirm_thread.is_alive():
            return

        self.confirm_thread = threading.Thread(
            target=self._confirm_worker,
            name="first-swap-confirmation",
            daemon=True,
        )
        self.confirm_thread.start()

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
        # candidate. This remains exactly on the speed-critical path.
        if not from_is_zero and not to_is_zero and amount > 0:
            if self._is_contract(to_addr):
                self.candidate_contracts.add(to_addr)
                dirs = self.candidate_directions.setdefault(to_addr, set())
                dirs.add("IN")

                # Existing immediate alert: NOT delayed by swap confirmation.
                self._pool_candidate_alert(
                    to_addr, tx_hash, block_number
                )

            if self._is_contract(from_addr):
                self.candidate_contracts.add(from_addr)
                dirs = self.candidate_directions.setdefault(from_addr, set())
                dirs.add("OUT")

        # Stronger existing signal: same contract appears on both sides across
        # LAPTOP token transfers.
        for candidate in (from_addr, to_addr):
            if candidate not in self.candidate_contracts:
                continue

            dirs = self.candidate_directions.setdefault(candidate, set())

            if to_addr == candidate and not from_is_zero:
                dirs.add("IN")

            if from_addr == candidate and not to_is_zero:
                dirs.add("OUT")

            if "IN" in dirs and "OUT" in dirs:
                # Existing immediate alert: NOT delayed.
                self._trading_alert(
                    candidate, tx_hash, block_number
                )

            # Background-only verification for EVERY later transfer involving
            # a candidate. This is important: if the first IN/OUT tx is not a
            # real swap, a later real swap can still trigger FIRST SWAP.
            if (
                amount > 0
                and not from_is_zero
                and not to_is_zero
                and (from_addr == candidate or to_addr == candidate)
            ):
                self._queue_confirmation(
                    candidate, tx_hash, block_number
                )

    def run(self):
        self._connect_check()
        self._start_confirmation_worker()

        # Start one block behind current tip to avoid missing a race during boot.
        self.last_block = max(self.w3.eth.block_number - 1, 0)

        self._send(
            "🟢 LAPTOP WATCH ONLINE\n\n"
            "🌐 Base\n"
            f"🪙 CA: {self.token}\n"
            f"⚡ Poll: {POLL_SECONDS}s\n\n"
            "Watching:\n"
            "1) token transfer to contract → LIQUIDITY/POOL SIGNAL\n"
            "2) same contract IN + OUT → TRADING LIVE\n"
            "3) background real Swap event → FIRST SWAP / CONFIRMED"
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
