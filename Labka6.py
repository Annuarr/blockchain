import json
import os
import sys
import requests

ACCESS_TOKEN = ""

def api_handler(path, action, pair="", value=""):
    url = f"https://api.ataix.kz{path}"
    headers = {
        "accept": "application/json",
        "X-API-Key": ACCESS_TOKEN
    }

    data = {
        "symbol": pair,
        "side": "buy",
        "type": "limit",
        "quantity": 1,
        "price": value
    }

    if action == "get":
        reply = requests.get(url, headers=headers, timeout=20)
    elif action == "post":
        reply = requests.post(url, headers=headers, json=data, timeout=20)
    elif action == "delete":
        reply = requests.delete(url, headers=headers, timeout=20)
    else:
        raise Exception("Unsupported method.")

    return reply.json() if reply.status_code == 200 else f"Error: {reply.status_code}, {reply.text}"

def update_order_file(new_data):
    file_path = "orders_data.json"
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                current_data = json.load(f)
        except json.JSONDecodeError:
            current_data = []
    else:
        current_data = []

    for record in new_data:
        info = record["result"]
        current_data.append({
            "orderID": info["orderID"],
            "price": info["price"],
            "quantity": info["quantity"],
            "symbol": info["symbol"],
            "created": info["created"],
            "status": info.get("status", "NEW")
        })

    with open(file_path, "w") as f:
        json.dump(current_data, f, indent=4)


with open("orders_data.json", "r") as f:
    records = json.load(f)

ids = [r["orderID"] for r in records if "orderID" in r]
prices = [r["price"] for r in records if "price" in r]
symbols = [r["symbol"] for r in records if "symbol" in r]
statuses = [r["status"] for r in records if "status" in r]

pending_ids = []
pending_prices = []


print("📋 CURRENT ORDER STATUSES")
for i, oid in enumerate(ids):
    print(f"ID: {oid}\t STATUS: {statuses[i]}")

print("NOTE: Filled orders = 'filled'. Others will be canceled.")

found_filled = False
for i, oid in enumerate(ids):
    check = api_handler(f"/api/orders/{oid}", "get")

    if "filled" in str(check):
        for item in records:
            if item["orderID"] == oid:
                item["status"] = "filled"
        found_filled = True
    else:
        print(f"ID: {oid}\t PRICE: {prices[i]}$\t STATUS: {statuses[i]}")
        pending_ids.append(oid)
        pending_prices.append(prices[i])
        for item in records:
            if item["orderID"] == oid:
                item["status"] = "cancelled"

    with open("orders_data.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)

if found_filled:
    print("✅ Some orders completed.")
    sys.exit()

print("🔻 CANCELING UNFILLED ORDERS")
for oid in pending_ids:
    api_handler(f"/api/orders/{oid}", "delete")
    print(f"[-] Order Canceled: {oid}")

print("🔼 RE-CREATING ORDERS +1%")
new_batch = []
for i, pid in enumerate(pending_ids):
    improved_price = round(float(pending_prices[i]) * 1.01, 4)
    created = api_handler("/api/orders", "post", symbols[i], improved_price)
    new_batch.append(created)
    print(f"[+] New Order: {symbols[i]} @ {improved_price}$")

update_order_file(new_batch)
print("[✔] New orders saved to 'orders_data.json'")
print("[ℹ] Check them on ATAIX > My Orders")
