from web3 import Web3
from web3.exceptions import Web3Exception

from config import RPC_URL, LAUNCHER_FACTORY


LAUNCH_CREATED_ABI = [{
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
        raise RuntimeError("RPC baglantisi kurulamadi.")

    print(f"RPC OK")
    print(f"Chain ID : {w3.eth.chain_id}")
    print(f"Latest   : {w3.eth.block_number}")
    print()

    factory_address = Web3.to_checksum_address(LAUNCHER_FACTORY)

    print(f"Factory:")
    print(factory_address)
    print()

    event_signature = Web3.keccak(
        text="LaunchCreated(address,address,address,string,string,string,string)"
    ).hex()

    print(f"LaunchCreated topic:")
    print(event_signature)
    print()

    factory = w3.eth.contract(
        address=factory_address,
        abi=LAUNCH_CREATED_ABI,
    )

    # ---------------------------------------------------------
    # TEST ICIN BURAYA CLOCKIN'IN BLOCK NUMARASINI YAZACAĞIZ.
    # ---------------------------------------------------------
    TEST_BLOCK = None

    if TEST_BLOCK is None:
        print("TEST_BLOCK henuz girilmedi.")
        print()
        print("Once CLOCKIN launch transaction/block numarasini")
        print("belirlememiz gerekiyor.")
        print()
        print("Ornek:")
        print("TEST_BLOCK = 33630000")
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
        print("SONUC: BU FACTORY'DE EVENT YOK.")
        print()
        print("Bu durumda CLOCKIN launch'i bizim dinledigimiz")
        print("Factory + LaunchCreated event'i uzerinden")
        print("olusturulmamis olabilir.")
        return

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
            print("Radar'in dinledigi event GERCEK.")
            print("Bir sonraki adim filter/Telegram zincirini")
            print("test etmek olacak.")

        except Exception as exc:
            print(f"EVENT DECODE ERROR: {exc}")


if __name__ == "__main__":
    main()
