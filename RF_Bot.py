import telebot
import requests
import datetime
import time
import os
import concurrent.futures
import logging
from telegram.ext import CommandHandler, MessageHandler, updater
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# logs for debugging
# logger = telebot.logger
# logging.basicConfig(filename='log.txt',
#                     filemode='a',
#                     format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
#                     datefmt='%H:%M:%S',
#                     level=logging.DEBUG)

bot = telebot.TeleBot(TOKEN)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")

userdetails = {}

stock_profile = {}

now = datetime.datetime.now()

menulist = {
    "main": [
        ("View Portfolio", "main#portfolio")

    ], "portfolio": [
        ("Get Stock prices 💹", "portfolio@i"),
        ("Add Stocks to Portfolio ✅", "portfolio@a"),
        ("Remove Stocks from Portfolio ❌", "portfolio@r"),
        ("Back to main menu ⬅️", "main#main")
    ]
}


def stock_in_portfolio(userid, stockid):
    return True if stockid in userdetails[userid]["portfolio"] else False


def stocksearch(userid, stock):
    try:
        browser = webdriver.Chrome(
            executable_path="chromedriver", options=chrome_options)

        url = "https://sg.finance.yahoo.com/"
        browser.get(url)

        # Stock search
        browser.find_element_by_id("yfin-usr-qry").send_keys(stock)
        browser.find_element_by_xpath(
            "//button[@id = 'search-button']").click()

        # Get elements from new page
        time.sleep(0.75)
        stype = browser.current_url.split('/')

        if len(stype) == 4:
            browser.close()
            return "nil"

        stocksplit = browser.find_element_by_xpath(
            "//h1[@class='D(ib) Fz(18px)']").text
        stocksplit = stocksplit.split(" (")
        stockid = stocksplit[1][:-1]
        stockname = stocksplit[0]

        # Get stock price
        price = browser.find_elements_by_xpath(
            "//div[@class='D(ib) Mend(20px)']/span")[0].text
        if "," in price:
            price = "".join(price.split(","))
        price = round(float(price), 2)

        # Get PE ratio
        pe_ratio = browser.find_element_by_xpath(
            "//td[@data-test = 'PE_RATIO-value']"
        ).text
        if pe_ratio == "N/A":
            pe_ratio = 0.00
        else:
            pe_ratio = round(float(pe_ratio), 2)

        # Get sector
        browser.find_element_by_xpath(
            "//li[@data-test = 'COMPANY_PROFILE']/a").click()
        time.sleep(0.5)
        sector = browser.find_element_by_xpath(
            "//p[@class = 'D(ib) Va(t)']/span[2]").text

        browser.close()

        # Enter/Update stock in stock_profile
        stock_profile[stockid] = {
            'stockid': stockid, 'stockname': stockname, 'stockprice': price, 'pe-ratio': pe_ratio, 'sector': sector, 'updated-datetime': now.strftime("%Y-%m-%d %H:%M:%S")
        }
        return (stockname, stockid)
    except:
        pass


@bot.callback_query_handler(func=lambda message: 'main#' in message.data)
def change_menu(message):
    menu, function = message.data.split("#")
    if message.from_user.id not in userdetails:
        userdetails[message.from_user.id] = {
            "userid": message.from_user.id, "menu": "", "function": "", "portfolio": []
        }

    userdetails[message.from_user.id]["menu"] = menu
    userdetails[message.from_user.id]["function"] = function

    markup = telebot.types.InlineKeyboardMarkup()

    for i in range(len(menulist[function])):
        markup.add(telebot.types.InlineKeyboardButton(
            menulist[function][i][0], callback_data=menulist[function][i][1]))

    bot.send_message(message.from_user.id,
                     "What would you like to do?", reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda message: 'portfolio@' in message.data)
def manage_portfolio(message):
    menu, function = message.data.split("@")
    if message.from_user.id not in userdetails:
        userdetails[message.from_user.id] = {
            "userid": message.from_user.id, "menu": "", "function": "", "portfolio": []
        }

    userdetails[message.from_user.id]["menu"] = menu
    userdetails[message.from_user.id]["function"] = function

    return_message = ""
    if function == "r":
        return_message = "*Which stock do you want to remove from your portfolio?*"

        user_stocks = [
            (
                stock_profile[stock]["stockid"], stock_profile[stock]["stockname"]
            )
            for stock in userdetails[message.from_user.id]['portfolio']
        ]
        markup = telebot.types.InlineKeyboardMarkup()

        for i in range(len(user_stocks)):
            markup.add(telebot.types.InlineKeyboardButton(
                user_stocks[i][1], callback_data="confirmation$" + user_stocks[i][0] + "$" + user_stocks[i][1]))

        markup.add(telebot.types.InlineKeyboardButton(
            "Back to Portfolio", callback_data="main#portfolio"
        ))
        bot.send_message(userdetails[message.from_user.id]["userid"],
                         return_message, reply_markup=markup, parse_mode="Markdown")
    else:
        if function == "i":
            if len(userdetails[message.from_user.id]["portfolio"]) == 0:
                return_message = "You have no stocks in your portfolio! Click on 'Add Stocks to Portfolio' to view stock price."
            else:
                return_message = "{0:<15} {1}".format(
                    "*Stock Code*", "*Price (SGD)*") + "\n"

                return_message += '\n'.join(
                    [
                        "{0:<19} ${1:.2f}".format(
                            stock_profile[i]["stockid"], stock_profile[i]["stockprice"])
                        for i in userdetails[message.from_user.id]["portfolio"]
                    ]
                )

                return_message += "\n*Updated as of : " + \
                    datetime.datetime.now().strftime("%d %b %Y %H:%M:%S")+"*"

        elif function == "a":
            return_message = "*Please enter the stock code of the stock*"
        bot.send_message(message.from_user.id, return_message,
                         parse_mode="Markdown")


@bot.callback_query_handler(func=lambda message: 'confirmation$' in message.data)
def confirm_remove(message):
    _, stockid, stockname = message.data.split("$")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        "YES ✅", callback_data="r!ans!y!" + stockid + "!" + stockname
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        "NO ❌", callback_data="r!ans!n!" + stockid + "!" + stockname
    ))

    bot.send_message(message.from_user.id, "Are you sure you want to remove " +
                     stockid + " (" + stockname + ") from your portfolio?", reply_markup=markup)


@bot.callback_query_handler(func=lambda message: 'ans!' in message.data)
def manage_yes_no_ans(message):
    function, _, response, stockid, stockname = message.data.split("!")
    if response == "y":
        if function == "a":
            userdetails[message.from_user.id]["portfolio"].append(stockid)
            bot.send_message(
                message.from_user.id, "Stock added to portfolio!\nTo stop adding stocks into your portfolio, type 'N', else please enter another stock.")

        elif function == "r":
            userdetails[message.from_user.id]["portfolio"].remove(stockid)

            bot.send_message(message.from_user.id, stockid +
                             " (" + stockname + ") has been removed from your portfolio!")

            return_message = "*Which stock do you want to remove from your portfolio?*"
            user_stocks = [
                (stock_profile[stock]["stockid"], stock_profile[stock]["stockname"]) for stock in userdetails[message.from_user.id]["portfolio"]]

            markup = telebot.types.InlineKeyboardMarkup()
            for i in range(len(user_stocks)):
                markup.add(telebot.types.InlineKeyboardButton(
                    user_stocks[i][1], callback_data="confirmation$" +
                    user_stocks[i][0] + "$" + user_stocks[i][1]
                ))

            markup.add(telebot.types.InlineKeyboardButton(
                "Back to Portfolio", callback_data="main#portfolio"
            ))
            bot.send_message(message.from_user.id,
                             return_message, reply_markup=markup, parse_mode="Markdown")

    else:
        if function == "a":
            bot.send_message(message.from_user.id,
                             "If you would like to stop adding stocks, type 'N'")
        elif function == "r":
            return_message = "*Which stock do you want to remove from your portfolio?*"
            user_stocks = [
                (stock_profile[stock]["stockid"], stock_profile[stock]["stockname"]) for stock in userdetails[message.from_user.id]["portfolio"]]

            markup = telebot.types.InlineKeyboardMarkup()

            for i in range(len(user_stocks)):
                markup.add(telebot.types.InlineKeyboardButton(
                    user_stocks[i][1], callback_data="confirmation$" +
                    user_stocks[i][0] + "$" + user_stocks[i][1]
                ))
            markup.add(telebot.types.InlineKeyboardButton(
                "Back to Portfolio", callback_data="main#portfolio"
            ))
            bot.send_message(message.from_user.id,
                             return_message, reply_markup=markup, parse_mode="Markdown")


# Message Handlers
@bot.message_handler(commands=['start'])
def start(message):
    welcome = "Welcome " + \
        str(message.chat.first_name)+"! How can I help you today?"

    # userdetails global var
    userdetails[message.from_user.id] = {
        "userid": message.from_user.id, "menu": "", "function": "", "portfolio": []
    }

    markup = telebot.types.InlineKeyboardMarkup()
    for i in range(len(menulist["main"])):
        markup.add(telebot.types.InlineKeyboardButton(
            menulist["main"][i][0], callback_data=menulist["main"][i][1]))

    bot.send_message(message.from_user.id, welcome, reply_markup=markup,
                     parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.from_user.id not in userdetails:
        userdetails[message.chat.id] = {
            "userid": message.chat.id, "menu": "", "function": ""}

    if message.text.lower() == "n":
        userdetails[message.from_user.id]["menu"] = "main"
        userdetails[message.from_user.id]["function"] = "portfolio"
        markup = telebot.types.InlineKeyboardMarkup()

        for i in range(len(menulist["portfolio"])):
            markup.add(telebot.types.InlineKeyboardButton(
                menulist["portfolio"][i][0], callback_data=menulist["portfolio"][i][1]))

        bot.send_message(
            message.chat.id, "What would you like to do today?", reply_markup=markup, parse_mode="Markdown")

    elif userdetails[message.from_user.id]["menu"] == "portfolio" and userdetails[message.from_user.id]["function"] == "a":
        bot.send_message(
            message.chat.id, "Please hold on, verifying your stock...")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                stocksearch, message.from_user.id, message.text)
            validate_stock = future.result()

        if validate_stock == None:
            bot.reply_to(
                message, "Could not find stock! Please re-enter your stock")
        elif stock_in_portfolio(message.from_user.id, validate_stock[1]):
            bot.send_message(
                message.from_user.id, "Stock already in portfolio! Please enter another stock")
        elif validate_stock != "nil":
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(
                "YES 👍🏼", callback_data="a!ans!y!" + validate_stock[1] + "!" + validate_stock[0]
            ))
            markup.add(telebot.types.InlineKeyboardButton(
                "NO 👎🏼", callback_data="a!ans!n!" + validate_stock[1] + "!" + validate_stock[0]
            ))
            bot.reply_to(message, "Did you mean *" + validate_stock[0] +
                         "*?", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.reply_to(
                message, "Could not find stock! Please re-enter your stock")
    else:
        bot.reply_to(
            message, "Hi! I am RedFlag Stock Bot created by Sean! To get start, click on /start")


while True:
    try:
        bot.polling()
    except:
        time.sleep(10)
