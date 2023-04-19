import websocket
import json

def on_open(ws):
    params = {"method": "SUBSCRIBE", "params":["btcusdt@kline_1m"], "id": 1}
    ws.send(json.dumps(params))

def on_message(ws, message):
    data = json.loads(message)
    kline = data["k"]
    open_price = kline["o"]
    high_price = kline["h"]
    low_price = kline["l"]
    close_price = kline["c"]
    volume = kline["v"]
    print(f"Open: {open_price}, High: {high_price}, Low: {low_price}, Close: {close_price}, Volume: {volume}")

ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws",
                            on_open=on_open,
                            on_message=on_message)
ws.run_forever()
