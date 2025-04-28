import json
import requests

TOKEN = ""

def api_interaction(route, method, ticker="", direction="", rate=""):
    endpoint = f"https://api.ataix.kz{route}"
    headers = {
        "accept": "application/json",
        "X-API-Key": TOKEN
    }
    payload = {
        "symbol": ticker,
        "side": direction,
        "type": "limit",
        "quantity": 1,
        "price": rate
    }

    try:
        if method == "get":
            resp = requests.get(endpoint, headers=headers, timeout=20)
        elif method == "post":
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=20)
        elif method == "delete":
            resp = requests.delete(endpoint, headers=headers, timeout=20)
        else:
            return "Неизвестный метод запроса."

        if resp.status_code == 200:
            return resp.json()
        else:
            return f"Запрос не выполнен: {resp.status_code} - {resp.text}"
    except requests.RequestException as e:
        return f"Ошибка подключения: {e}"

# Чтение списка ордеров
with open("orders_data.json", "r") as file:
    orders_data = json.load(file)

ids = [order["orderID"] for order in orders_data if "orderID" in order]
symbols = [order["symbol"] for order in orders_data if "symbol" in order]
prices = [float(order["price"]) for order in orders_data if "price" in order]
sides = [order["side"] for order in orders_data if "side" in order]
statuses = [order["status"] for order in orders_data if "status" in order]
commissions = [float(order["commission"]) for order in orders_data if "commission" in order]

# Обновление статусов ордеров
for idx in ids:
    api_interaction(f"/api/orders/{idx}", "get")

buy_total = round(sum(prices[:3]), 4)
buy_fee = round(sum(commissions[:3]), 4)

sell_total = round(sum(prices[3:]), 4)
sell_fee = round(sum(commissions[3:]), 4)

print("\n[#] Информация по активным ордерам:")
print("ID заявки\t\t\t| Тикер\t\t | Цена\t   |Направление\t | Комиссия\t | Статус")
for id_, symbol, price, side, fee, stat in zip(ids, symbols, prices, sides, commissions, statuses):
    print(f"{id_}\t| {symbol}\t | {price}  | {side}\t | {fee}\t | {stat}")

print(f"\nПокупка всего на: {buy_total}$ (с учётом комиссии: {buy_fee}$)")
print(f"Продажа всего на: {sell_total}$ (с учётом комиссии: {sell_fee}$)")

gross_income = sell_total - sell_fee
total_expense = buy_total + buy_fee
profit = round(gross_income - total_expense, 4)

if total_expense != 0:
    profit_percent = round((profit / total_expense) * 100, 2)
else:
    profit_percent = 0.0

print(f"Результат сделки: {profit}$ ({profit_percent}%)")
