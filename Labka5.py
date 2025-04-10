import requests, json, re, sys, os

KEY = ""

def extract_tokens(text_str, trigger_word):
    all_words = re.findall(r'\b\w+\b', text_str)
    return {re.sub(r'[^a-zA-Zа-яА-Я]', '', all_words[i + 1]) for i in range(len(all_words)-1) if all_words[i] == trigger_word}

def collect_pairs(response, identifier):
    elements = re.findall(r'\b\w+(?:/\w+)?\b', response)
    return [elements[i + 1] for i in range(len(elements)-1) if elements[i] == identifier]

def match_prices(content, term):
    price_pattern = rf'{term}[\s\W]*([-+]?\d*\.\d+|\d+)'
    return re.findall(price_pattern, content)

def log_to_file(dataset):
    file = "orders_data.json"
    previous = []
    if os.path.exists(file):
        try:
            with open(file, "r") as fp:
                previous = json.load(fp)
        except Exception:
            pass
    for entry in dataset:
        result = entry["result"]
        previous.append({
            "orderID": result["orderID"],
            "price": result["price"],
            "quantity": result["quantity"],
            "symbol": result["symbol"],
            "created": result["created"],
            "status": result.get("status", "NEW")
        })
    with open(file, "w") as fp:
        json.dump(previous, fp, indent=4)

def perform_request(api_path, req_type, symbol_name="", deal_price=""):
    full_url = f"https://api.ataix.kz{api_path}"
    headers = {
        "accept": "application/json",
        "X-API-Key": KEY
    }
    order_data = {
        "symbol": symbol_name,
        "side": "buy",
        "type": "limit",
        "quantity": 1,
        "price": deal_price
    }
    try:
        if req_type == "get":
            reply = requests.get(full_url, headers=headers, timeout=20)
        else:
            reply = requests.post(full_url, headers=headers, json=order_data, timeout=20)
        return reply.json() if reply.status_code == 200 else f"[{reply.status_code}] {reply.text}"
    except Exception as ex:
        return str(ex)

# === Вывод баланса ===
print("Ваш баланс в USDT:")

coin_list = extract_tokens(json.dumps(perform_request("/api/symbols", "get")), "base")
for token in coin_list:
    balance = perform_request(f"/api/user/balances/{token}", "get")
    available = re.search(r"'available':\s*'([\d.]+)'", str(balance))
    if available:
        print(f"{token:<10} | {available.group(1):>10} USDT")

# === Вывод подходящих пар ===
print("\nДоступные пары дешевле 0.6 USDT:")

symbol_pairs = collect_pairs(json.dumps(perform_request("/api/symbols", "get")), "symbol")
price_values = match_prices(json.dumps(perform_request("/api/prices", "get")), "lastTrade")

valid_pairs = []
current_rates = {}

for i in range(len(symbol_pairs)):
    pair = symbol_pairs[i]
    rate = float(price_values[i])
    if "USDT" in pair and rate <= 0.6:
        print(f"{pair:<15} | {rate:>10} USDT")
        valid_pairs.append(pair)
        current_rates[pair] = rate

# === Выбор токена ===
while True:
    user_input = input("Введите токен или 'exit' --> ").upper()
    if user_input + "/USDT" in valid_pairs:
        chosen_token = user_input
        base_cost = current_rates[chosen_token + "/USDT"]
        break
    elif user_input == "EXIT":
        sys.exit()
    else:
        print("[!] Не удалось найти указанную пару.")

# === Создание ордеров ===
print(f"\nВы выбрали: {chosen_token}, цена: {base_cost} USDT")

steps = [0.98, 0.95, 0.92]
levels = [round(float(base_cost) * step, 4) for step in steps]

print("\nБудут созданы ордера по ценам:")
for pct, lvl in zip([2, 5, 8], levels):
    print(f"- {pct}% ниже: {lvl} USDT")

# === Подтверждение ===
print("\nПодтвердите действие: 'yes' или 'exit'")
while True:
    ready = input("--> ")
    if ready == "yes":
        break
    elif ready == "exit":
        sys.exit()

# === Отправка ордеров ===
pending_orders = []
for entry_price in levels:
    result = perform_request("/api/orders", "post", chosen_token + "/USDT", entry_price)
    pending_orders.append(result)

log_to_file(pending_orders)

print("\n[✓] Ордера успешно размещены и сохранены в 'orders_data.json'")
print("[i] Проверяйте в личном кабинете ATAIX.")
print("=" * 60)
