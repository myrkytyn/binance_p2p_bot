from loguru import logger
from aiogram import Bot, Dispatcher, executor, types
import json
import requests

#Working with JSON config file
f = open("/home/maksym/Maks/Projects/P2P-bot/aiogram/data.json", "r")
config = json.load(f)

API_TOKEN = config["API_TOKEN"]
binance_url = config["BINANCE_URL"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

#Keyboard on start
@dp.message_handler(commands="start")
async def start_cmd_handler(message: types.Message):
    if not await is_user_allowed(message.from_user.username, message.from_user.id):
        return
    keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
    text_and_data = (
        ("Отримати список p2p ордерів", "p2p_orders"),
        ("Слідкувати за ціною", "follow_price")
    )
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    await bot.send_message(message.from_user.id, str(message.from_user.username)+", обери що робитимемо", reply_markup=keyboard_markup)

#P2P orders button
@dp.callback_query_handler(text="p2p_orders")
async def choose_currency(query: types.CallbackQuery):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    text_and_data = (
        ("ГРИВНІ", "UAH"),
        ("ЄВРО", "EUR"),
        ("ФУНТИ", "GBP")
    )
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    await bot.send_message(query.from_user.id, "Обери валюту для отримання р2р курсу", reply_markup=keyboard_markup)

@dp.callback_query_handler(text="UAH")
@dp.callback_query_handler(text="EUR")
@dp.callback_query_handler(text="GBP")
async def p2p_orders(query: types.CallbackQuery):
    answer_data = query.data
    fiat = answer_data
    bank = config[fiat][0]["BANK"]

    rows = config["ROWS"]
    request_params={"page":1,"rows":rows,"payTypes":bank,"asset":"USDT","tradeType":"BUY","fiat":fiat}
    
    #Request to Binance and saving responce with currencies
    request_post = requests.post(binance_url, json=request_params)
    response_data = request_post.json()
    
    info_message = "Bank is: " + str(bank) + "\nPRICE FOR BEST " +  str(rows) + " ORDERS: \n"
    await bot.send_message(query.from_user.id, info_message)

    currency_message=""
    for i in range(int(rows)):
        k=i+1
        currency_message = currency_message + str(k) + " order: " + str(response_data["data"][i]["adv"]["price"]+ "\n")
    await bot.send_message(query.from_user.id, currency_message)

#Price following (Not workinkg)
@dp.callback_query_handler(text="follow_price")
async def follow_price(query: types.CallbackQuery):
    await bot.send_message(query.from_user.id, "Вибачте, поки не працює")

#Check user priviledges
async def is_user_allowed(username, user_id):
    if str(user_id) in config["ALLOWED_USERS"]:
        is_user_allowed = True
        logger.info("User " + str(username) + " started the conversation. ID - " + str(user_id))
    else:
        is_user_allowed = False
        logger.info("NOT allowed user " + str(username) + ". ID - " + str(user_id))
        await bot.send_message(user_id, str(username)+", тобі заборонено доступ до бота, звернись до @myrkytyn")
    return is_user_allowed

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
