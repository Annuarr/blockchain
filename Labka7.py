import json
import requests
import os

API_KEY = ""

def place_limit_order(pair, action, rate):
    url = "https://api.ataix.kz/api/orders"
    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY
    }
    body = {
        "symbol": pair,
        "side": action,
        "type": "limit",
        "quantity": 1,
        "price": rate
    }
    try:
        res = requests.post(url, headers=headers, json=body, timeout=20)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"[Ошибка {res.status_code}] {res.text}")
            return None
    except Exception as e:
        print("[!] Ошибка соединения:", e)
        return None

def append_to_file(new_entries):
    path = "orders_data.json"
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                all_data = json.load(f)
        else:
            all_data = []
    except:
        all_data = []

    for entry in new_entries:
        if entry and "result" in entry:
            order = entry["result"]
            record = {
                "orderID": order.get("orderID"),
                "symbol": order.get("symbol"),
                "price": order.get("price"),
                "quantity": order.get("quantity"),
                "side": order.get("side"),
                "created": order.get("created"),
                "status": order.get("status", "NEW")
            }
            all_data.append(record)

    with open(path, "w") as f:
        json.dump(all_data, f, indent=4)

def process_sell_batch(symbol_list, base_prices):
    result_orders = []
    for i in range(len(symbol_list)):
        adjusted_price = round(base_prices[i] * 1.02, 4)
        response = place_limit_order(symbol_list[i], "sell", adjusted_price)
        result_orders.append(response)
    return result_orders

# Загружаем исходные ордера
with open("orders_data.json", "r") as f:
    old_orders = json.load(f)

symbols = [order["symbol"] for order in old_orders if "symbol" in order]
prices = [float(order["price"]) for order in old_orders if "price" in order]

print("\n[=] Имеющиеся ордера:")
for sym, pr in zip(symbols, prices):
    print(f" - {sym} по {pr} USD")

new_sell_orders = process_sell_batch(symbols, prices)
append_to_file(new_sell_orders)

print("\n[+] Новые ордера на продажу созданы:")
for i in range(len(symbols)):
    updated = round(prices[i] * 1.02, 4)
    print(f" - {symbols[i]} по {updated} USD")
