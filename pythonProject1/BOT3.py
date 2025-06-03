import telebot
from telebot.types import LabeledPrice, ShippingOption
import json
import csv
from datetime import datetime
import os
TOKEN = '8081325346:AAEtK6WGIBLkoiTY9-vCAbfxW5yrRJljSfI'
PAYMENT_PROVIDER_TOKEN = 'извините, юкасса отказывалась отправлять мне письмо на почту а в других местах требуется ИНН и остальная фигня)'
ADMIN_ID = @MCDerick_1
bot = telebot.TeleBot(TOKEN)
products = {
    1: {
        "name": "Промокод на скидку 20%",
        "description": "Дает право на скидку 20% на следующий заказ",
        "price": 5000,
        "currency": "RUB",
        "delivery_method": "text",
        "content": "Ваш промокод: DISCOUNT20\nСрок действия: 30 дней"
    },
    2: {
        "name": "Премиум подписка (1 месяц)",
        "description": "Доступ к премиум-функциям на 1 месяц",
        "price": 15000,
        "currency": "RUB",
        "delivery_method": "text",
        "content": "Ваш премиум-аккаунт активирован до: {expiry_date}"
    }
}
carts = {}
if not os.path.exists('purchases.csv'):
    with open('purchases.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["user_id", "username", "product_id", "product_name",
                         "amount", "currency", "payment_date", "delivered"])
def log_purchase(user_id, username, product_id, product_name, amount, currency):
    with open('purchases.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            user_id,
            username,
            product_id,
            product_name,
            amount,
            currency,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            True
        ])
def is_payment_unique(invoice_payload):
    return True
def deliver_product(product_id, user_id):
    product = products[product_id]
    if product["delivery_method"] == "text":
        if "{expiry_date}" in product["content"]:
            expiry = (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y")
            content = product["content"].format(expiry_date=expiry)
        else:
            content = product["content"]
        bot.send_message(user_id, f"🎉 Поздравляем с покупкой!\n\n{content}")
    else:
        bot.send_message(user_id, "Ваш товар был отправлен. Проверьте сообщения.")
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в наш магазин цифровых товаров!\n\n"
        "Доступные команды:\n"
        "/catalog - Показать каталог товаров\n"
        "/cart - Просмотреть корзину\n"
        "/help - Помощь"
    )
@bot.message_handler(commands=['catalog'])
def show_catalog(message):
    markup = telebot.types.InlineKeyboardMarkup()
    for product_id, product in products.items():
        btn = telebot.types.InlineKeyboardButton(
            text=f"{product['name']} - {product['price'] / 100} {product['currency']}",
            callback_data=f"product_{product_id}"
        )
        markup.add(btn)
    bot.send_message(
        message.chat.id,
        "📋 Каталог товаров:",
        reply_markup=markup
    )
@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def product_selected(call):
    product_id = int(call.data.split('_')[1])
    product = products[product_id]
    markup = telebot.types.InlineKeyboardMarkup()
    btn_add = telebot.types.InlineKeyboardButton(
        text="➕ Добавить в корзину",
        callback_data=f"add_to_cart_{product_id}"
    )
    btn_buy = telebot.types.InlineKeyboardButton(
        text="🛒 Купить сейчас",
        callback_data=f"buy_now_{product_id}"
    )
    markup.add(btn_add, btn_buy)
    bot.send_message(
        call.message.chat.id,
        f"<b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"Цена: <b>{product['price'] / 100} {product['currency']}</b>",
        parse_mode='HTML',
        reply_markup=markup
    )
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_cart_'))
def add_to_cart(call):
    user_id = call.from_user.id
    product_id = int(call.data.split('_')[3])
    if user_id not in carts:
        carts[user_id] = []
    carts[user_id].append(product_id)
    bot.answer_callback_query(call.id, "Товар добавлен в корзину!")
@bot.message_handler(commands=['cart'])
def show_cart(message):
    user_id = message.from_user.id
    if user_id not in carts or not carts[user_id]:
        bot.send_message(message.chat.id, "Ваша корзина пуста!")
        return
    total = 0
    cart_items = []
    for product_id in carts[user_id]:
        product = products[product_id]
        cart_items.append(f"{product['name']} - {product['price'] / 100} {product['currency']}")
        total += product['price']
    markup = telebot.types.InlineKeyboardMarkup()
    btn_clear = telebot.types.InlineKeyboardButton(
        text="❌ Очистить корзину",
        callback_data="clear_cart"
    )
    btn_checkout = telebot.types.InlineKeyboardButton(
        text="💳 Оформить заказ",
        callback_data="checkout"
    )
    markup.add(btn_clear, btn_checkout)
    bot.send_message(
        message.chat.id,
        "🛒 Ваша корзина:\n\n" + "\n".join(cart_items) + f"\n\nИтого: {total / 100} {products[1]['currency']}",
        reply_markup=markup
    )
@bot.callback_query_handler(func=lambda call: call.data == 'checkout')
def checkout(call):
    user_id = call.from_user.id
    if user_id not in carts or not carts[user_id]:
        bot.answer_callback_query(call.id, "Ваша корзина пуста")
        return
    product_id = carts[user_id][0]
    product = products[product_id]
    try:
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=product['name'],
            description=product['description'],
            invoice_payload=f"{user_id}_{product_id}_{datetime.now().timestamp()}",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency=product['currency'],
            prices=[LabeledPrice(label=product['name'], amount=product['price'])],
            start_parameter='time-machine-example',
            photo_url='https://via.placeholder.com/150',
            photo_size=100,
            photo_width=150,
            photo_height=150,
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ошибка при создании платежа: {e}")
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    product_id = int(payload.split('_')[1])
    if not is_payment_unique(payload):
        bot.send_message(message.chat.id, "Этот платеж уже был обработан ранее")
        return
    deliver_product(product_id, user_id)
    log_purchase(
        user_id=user_id,
        username=message.from_user.username,
        product_id=product_id,
        product_name=products[product_id]['name'],
        amount=message.successful_payment.total_amount,
        currency=message.successful_payment.currency
    )
    if user_id in carts:
        del carts[user_id]
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)