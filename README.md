# Robinhood Radar — $CLOCKIN

Patoshi Radar'dan bağımsız, Robinhood Chain üzerinde StonkBrokers Stonk Launcher'ı izleyen hızlı keyword radar.

## Amaç

Wallet/creator analizi yok.
Sadece:

1. StonkBrokers Launcher Factory'den `LaunchCreated` event'ini izle.
2. Token `name` + `symbol` üzerinde Patoshi Radar keyword'lerini ara.
3. Match varsa anında Telegram alarmı gönder.

## Ağ

- Robinhood Chain mainnet
- Chain ID: 4663
- RPC: https://rpc.mainnet.chain.robinhood.com
- Explorer: https://robinhoodchain.blockscout.com

## Launcher Factory

`0x631f9371Fd6B2C85F8f61d19A90547eE67Fa61A2`

## Kurulum

```bash
pip install -r requirements.txt
copy .env.example .env
```

`.env` içine `BOT_TOKEN` ve `CHAT_ID` gir.

Çalıştır:

```bash
python app.py
```

## Not

Public RPC rate-limited olabilir. Hız/üretim için Robinhood'ın resmi dokümanında önerilen Alchemy WebSocket/RPC endpoint'ine geçilebilir.
