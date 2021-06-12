import json
import config
import logging
import telebot
import ccxt
import pandas as pd
import dataframe_image as dfi
from DBHandler import DBHandler

API_KEY = config.TELEGRAM_TOKEN
bot = telebot.TeleBot(API_KEY)

@bot.message_handler(commands=['help'])
def help(message):
	msg = '/greet\n'+\
		'/hello\n'+\
		'/portfolio\n'+\
		'/set_enable_status [0|1] (0=False, 1=True)\n'+\
		'/get_enable_status\n'+\
		'/get_chat_id\n'+\
		'/get_order\n'+\
		'/get_params\n'+\
		'/insert_params [ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend] (0=False, 1=True)\n'
	bot.reply_to(message, msg)

@bot.message_handler(commands=['greet'])
def greet(message):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		bot.reply_to(message, 'What\'s up doc?')
	
@bot.message_handler(commands=['hello'])
def hello(message):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		bot.send_message(message.chat.id, 'Hello, how are you.')

@bot.message_handler(commands=['portfolio'])
def portfolio(message):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		bot.send_message(message.chat.id, 'Fetching...')
		bot.send_chat_action(message.chat.id, 'upload_photo')
		get_portfolio()
		photo = open('portfolio.png', 'rb')
		bot.send_photo(message.chat.id, photo)

@bot.message_handler(commands=['insert_params'])
def insert_params(message):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		if len(message.text.split()) == 8:
			current_params = DBHandler().get_params()
			chat_id = current_params['chat_id']
			msg, ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend = message.text.split()

			if(test_insert_param(ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend)):
				DBHandler().insert_params(ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend, chat_id)
				bot.send_message(message.chat.id, json.dumps(DBHandler().get_params(), indent=2))
			else:
				bot.send_message(message.chat.id, 'Incorrect Parameters')
		else:
			bot.send_message(message.chat.id, 'Incorrect number of Parameters')

@bot.message_handler(commands=['get_params'])
def get_params(message):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		bot.send_message(message.chat.id, json.dumps(DBHandler().get_params(), indent=2))

@bot.message_handler(commands=['get_order'])
def get_order(message):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		order = DBHandler().get_order()
		print(order)
		bot.send_message(message.chat.id, json.dumps(order, indent=2))

@bot.message_handler(commands=['get_chat_id'])
def get_chat_id(message):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		bot.send_message(message.chat.id, message.chat.id)

@bot.message_handler(commands=['get_enable_status'])
def get_enable_status(message):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		bot.send_message(message.chat.id, json.dumps(DBHandler().get_enable_status(), indent=2))

@bot.message_handler(commands=['set_enable_status'])
def set_enable_status(message):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		msg = message.text.split()
		if len(msg) == 2 and test_enable_param(msg[1]):
			DBHandler().update_enable_status(msg[1])
			bot.send_message(message.chat.id, 'Status: \n'+json.dumps(DBHandler().get_enable_status(), indent=2))
		else:
			bot.send_message(message.chat.id, 'Incorrect Parameters')

def test_message(chat_id, msg):
	if message.chat.id == config.TELEGRAM_CHAT_ID:
		bot.send_message(chat_id, msg)


def price_request(message):
	request = message.text.split()
	if len(request < 2) or request[0].lower not in 'price':
		return False
	else:
		return True

def get_portfolio():
	binance = ccxt.binance ({
	    'options': {
	        'adjustForTimeDifference': True, 
	    },
	    'enableRateLimit': True,
	    'apiKey': config.BINANCE_API_KEY,
	    'secret': config.BINANCE_SECRET_KEY,
	})
	balances = binance.fetchBalance()
	symbols = binance.symbols
	balance_totals = balances['total']
	orders = []
	portfolio = {}
	for symbol,value in balance_totals.items():
	    if 'USD' in symbol or value == 0:
	        continue
	    print(symbol,value)
	    if value != 0:
	        mOrders = binance.fetchOrders(symbol+'/USDT') if symbol+'/USDT' in binance.symbols else []
	        mOrders.extend(binance.fetchOrders(symbol+'/BUSD') if symbol+'/BUSD' in binance.symbols else [])
	        mOrders.extend(binance.fetchOrders(symbol+'/BTC') if symbol+'/BTC' in binance.symbols else [])
	        for coin_order in mOrders:
	            if not symbol in portfolio:
	                    portfolio[symbol] = {}
	                    portfolio[symbol]['symbols'] = {}
	            if 'info' in coin_order and coin_order['info']['status'] == 'FILLED':
	                orders.append(coin_order)
	                if coin_order['info']['side'] == 'BUY':
	                    portfolio[symbol]['bought'] = portfolio[symbol].get('bought',0) + coin_order['amount']
	                    portfolio[symbol]['spent'] = portfolio[symbol].get('spent',0) + coin_order['cost']
	                    portfolio[symbol]['net_usd'] = portfolio[symbol].get('net_usd',0) - coin_order['cost']
	                if coin_order['info']['side'] == 'SELL':
	                    portfolio[symbol]['sold'] = portfolio[symbol].get('sold',0) + coin_order['amount']
	                    portfolio[symbol]['retrieved'] = portfolio[symbol].get('retrieved',0) + coin_order['cost']
	                    portfolio[symbol]['net_usd'] = portfolio[symbol].get('net_usd',0) + coin_order['cost']
	                if not coin_order['info']['symbol'] in portfolio[symbol]['symbols'].keys():
	                    pair = symbol + '/' + coin_order['info']['symbol'].split(symbol).pop()
	                    portfolio[symbol]['symbols'][pair] = binance.fetchTicker(pair)['last']
	        portfolio[symbol]['current_amount']=value
	        portfolio[symbol]['avg_buy_price']=portfolio[symbol].get('spent',0) / portfolio[symbol].get('bought',0) if portfolio[symbol].get('bought',0) > 0 else 0
	        portfolio[symbol]['avg_sell_price']=portfolio[symbol].get('retrieved',0) / portfolio[symbol].get('sold',0) if portfolio[symbol].get('sold',0) > 0 else 0

	portfolio_df = pd.DataFrame(data=portfolio)
	portfolio_df = portfolio_df.fillna(' ').T
	portfolio_df = portfolio_df.style.background_gradient()
	dfi.export(portfolio_df, 'portfolio.png')
	return portfolio_df

def test_enable_param(msg):
	return True if msg =='0'or msg=='1' else False

def test_insert_param(ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend):
	binance = ccxt.binance ({
	    'options': {
	        'adjustForTimeDifference': True, 
	    },
	    'enableRateLimit': True,
	    'apiKey': config.BINANCE_API_KEY,
	    'secret': config.BINANCE_SECRET_KEY,
	})
	print(ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend)
	if ta in ['bb', 'st', 'rsi', 'ema_psar_macd', 'stock_rsi', 'macd','psar', 'ema_20_50', 'st_macd','bb_rsi'] and \
		scale in binance.timeframes and \
		stop_loss in ['0','1'] and \
		stop_profit in ['0','1'] and \
		enforce_profit in ['0','1'] and \
		daily_trend in ['0','1']:
		return True
	else:
		return False

def send_notification(msg):
	bot.send_message(config.TELEGRAM_CHAT_ID, msg)


while True:
	try:
		bot.polling(none_stop=True)
	except Exception as ex:
		print(ex)
		