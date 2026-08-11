from web3 import Web3
from web3.exceptions import Web3Exception

from config import RPC_URL, LAUNCHER_FACTORY


LAUNCH_CREATED_ABI = [{
    "anonymous": False,
    "inputs": [
        {"indexed": True, "internalType": "address", "name": "creator", "type": "address"},
        {"indexed": False, "internalType": "address", "name": "token", "type": "address"},
        {"indexed": False, "internalType": "address", "name": "launch", "type": "address"},
        {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
        {"indexed": False, "internalType": "string", "name": "symbol", "type": "string"},
        {"indexed": False, "internalType": "string", "name": "metadataURI", "type": "string"},
        {"indexed": False, "internalType": "string", "name": "imageURI", "type": "string"},
    ],
    "name": "LaunchCreated",
    "type": "event",
}]


def main():
    print("=" * 60)
    print("ROBINHOOD RADAR - LAUNCH DIAGNOSTIC")
    print("=" * 60)

    w3 = Web3(
        Web3.HTTPProvider(
            RPC_URL,
            request_kwargs={"timeout": 15},
        )
    )

    if not w3.is_connected():
        print("RPC BAGLANTI HATASI")
        return

    chain_id = w3.eth.chain_id

    print(f"RPC OK")
    print(f"Chain ID : {chain_id}")
    print(f"Latest   : {w3.eth.block_number}")
    print()

    if chain_id != 4663:
        print("UYARI: Chain ID 4663 degil!")
        return

    factory_address = Web3.to_checksum_address(LAUNCHER_FACTORY)

    print(f"Factory:")
    print(factory_address)
    print()

    event_signature = Web3.keccak(
        text="LaunchCreated(address,address,address,string,string,string,string)"
    ).hex()

    print("LaunchCreated topic:")
    print(event_signature)
    print()

    # ---------------------------------------------------------
    # CLOCKIN'IN GERCEK BLOCK NUMARASINI BURAYA YAZACAGIZ
    # ---------------------------------------------------------
    TEST_BLOCK = None

    if TEST_BLOCK is None:
        print("TEST_BLOCK = None")
        print()
        print("CLOCKIN launch transaction/block numarasini")
        print("buldugumuzda sadece TEST_BLOCK degerini girecegiz.")
        return

    print(f"Test block : {TEST_BLOCK}")
    print("-" * 60)

    try:
        logs = w3.eth.get_logs({
            "address": factory_address,
            "topics": [event_signature],
            "fromBlock": TEST_BLOCK,
            "toBlock": TEST_BLOCK,
        })

    except (Web3Exception, ValueError) as exc:
        print(f"RPC ERROR: {exc}")
        return

    print(f"LaunchCreated events: {len(logs)}")
    print()

    if not logs:
        print("=" * 60)
        print("KESIN SONUC")
        print("=" * 60)
        print("LaunchCreated = YOK")
        print()
        print("Bu block'ta bizim Factory'den")
        print("LaunchCreated event'i bulunmuyor.")
        return

    factory = w3.eth.contract(
        address=factory_address,
        abi=LAUNCH_CREATED_ABI,
    )

    for index, raw_log in enumerate(logs, start=1):

        print("=" * 60)
        print(f"EVENT #{index}")
        print("=" * 60)

        try:
            event = factory.events.LaunchCreated().process_log(raw_log)
            args = event["args"]

            print(f"Block       : {raw_log['blockNumber']}")
            print(f"TX Hash     : {raw_log['transactionHash'].hex()}")
            print()
            print(f"Creator     : {args['creator']}")
            print(f"Token       : {args['token']}")
            print(f"Launch      : {args['launch']}")
            print(f"Name        : {args['name']}")
            print(f"Symbol      : {args['symbol']}")
            print(f"Metadata    : {args['metadataURI']}")
            print(f"Image       : {args['imageURI']}")
            print()

            print("=" * 60)
            print("KESIN SONUC")
            print("=" * 60)
            print("Factory + LaunchCreated = TRUE")
            print()
            print("Radar'in dinledigi event dogrulandi.")

        except Exception as exc:
            print(f"DECODE ERROR: {exc}")


if __name__ == "__main__":
    main()
