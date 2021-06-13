import json
import config
import logging
import telebot
import ccxt
import pandas as pd
import dataframe_image as dfi
from DBHandler import DBHandler
import numpy as np

API_KEY = config.TELEGRAM_TOKEN
bot = telebot.TeleBot(API_KEY)
chat_id = int(config.TELEGRAM_CHAT_ID)

@bot.message_handler(commands=['help', 'start'])
def help(message):
	msg = '/greet\n'+\
		'/hello\n'+\
		'/portfolio\n'+\
		'/set_enable_status [0|1] (0=False, 1=True)\n'+\
		'/get_enable_status\n'+\
		'/set_test_run_status [0|1] (0=False, 1=True)\n'+\
		'/get_test_run_status\n'+\
		'/get_chat_id\n'+\
		'/get_order\n'+\
		'/get_params\n'+\
		'/get_chat_id\n'+\
		'/insert_params [ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend] (0=False, 1=True)\n'
	bot.reply_to(message, msg)

@bot.message_handler(commands=['greet'])
def greet(message):
	if message.chat.id == chat_id:
		bot.reply_to(message, 'What\'s up doc?')

@bot.message_handler(commands=['get_chat_id'])
def get_chat_id(message):
	bot.reply_to(message, message.chat.id)
	
@bot.message_handler(commands=['hello'])
def hello(message):
	if message.chat.id == chat_id:
		bot.send_message(message.chat.id, 'Hello, how are you.')

@bot.message_handler(commands=['portfolio'])
def portfolio(message):
	if message.chat.id == chat_id:
		bot.send_message(message.chat.id, 'Fetching...')
		bot.send_chat_action(message.chat.id, 'upload_photo')
		get_portfolio_df()
		photo = open('portfolio.png', 'rb')
		bot.send_photo(message.chat.id, photo)

@bot.message_handler(commands=['insert_params'])
def insert_params(message):
	if message.chat.id == chat_id:
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
	if message.chat.id == chat_id:
		bot.send_message(message.chat.id, json.dumps(DBHandler().get_params(), indent=2))

@bot.message_handler(commands=['get_order'])
def get_order(message):
	if message.chat.id == chat_id:
		order = DBHandler().get_order()
		print(order)
		bot.send_message(message.chat.id, json.dumps(order, indent=2))

@bot.message_handler(commands=['get_chat_id'])
def get_chat_id(message):
	if message.chat.id == chat_id:
		bot.send_message(message.chat.id, message.chat.id)

@bot.message_handler(commands=['get_enable_status'])
def get_enable_status(message):
	if message.chat.id == chat_id:
		bot.send_message(message.chat.id, json.dumps(DBHandler().get_enable_status(), indent=2))

@bot.message_handler(commands=['set_enable_status'])
def set_enable_status(message):
	if message.chat.id == chat_id:
		msg = message.text.split()
		if len(msg) == 2 and test_enable_param(msg[1]):
			DBHandler().update_enable_status(msg[1])
			bot.send_message(message.chat.id, 'Status: \n'+json.dumps(DBHandler().get_enable_status(), indent=2))
		else:
			bot.send_message(message.chat.id, 'Incorrect Parameters')

@bot.message_handler(commands=['get_test_run_status'])
def get_test_run_status(message):
	if message.chat.id == chat_id:
		bot.send_message(message.chat.id, json.dumps(DBHandler().get_testrun_status(), indent=2))

@bot.message_handler(commands=['set_enable_status'])
def set_test_run_status(message):
	if message.chat.id == chat_id:
		msg = message.text.split()
		if len(msg) == 2 and test_enable_param(msg[1]):
			DBHandler().update_testrun_status(msg[1])
			bot.send_message(message.chat.id, 'Status: \n'+json.dumps(DBHandler().get_testrun_status(), indent=2))
		else:
			bot.send_message(message.chat.id, 'Incorrect Parameters')

def test_message(chat_id, msg):
	if message.chat.id == chat_id:
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

def get_portfolio_df():
	binance = ccxt.binance ({
    'options': {
        'adjustForTimeDifference': True, 
    },
    'enableRateLimit': True,
    'apiKey': config.BINANCE_API_KEY,
    'secret': config.BINANCE_SECRET_KEY,
	})
	portfolio = pd.DataFrame.from_records([binance.fetchBalance()['total']]).T
	symbols = binance.symbols
	portfolio.columns = ['Balance']
	portfolio = portfolio[((portfolio['Balance'] != 0) & ('USDT' != portfolio.index) & ('BUSD' != portfolio.index))]

	for symbol in portfolio.index:
		mOrders = binance.fetchOrders(symbol+'/USDT') if symbol+'/USDT' in symbols else []
		mOrders.extend(binance.fetchOrders(symbol+'/BUSD') if symbol+'/BUSD' in symbols else [])
		mOrders.extend(binance.fetchOrders(symbol+'/BTC') if symbol+'/BTC' in symbols else [])
		df_orders = pd.DataFrame.from_dict(mOrders)
		df_orders = df_orders.loc[(df_orders.status=='closed'),].set_index('timestamp')
		
		pair_list = np.array([], dtype=object)
		price_list = np.array([], dtype=object)
		bought,spent,net_usd,sold,retrieved=[0]*5
		
		amt,cst = [0]*2
		for index, row in df_orders.iterrows():
			pair_list = np.insert(pair_list, 0, row['symbol'])
			if row['side']=='buy':
				amt = amt + row['amount']
				cst = cst + row['cost']
			elif row['side']=='sell':
				amt,cst = [0]*2

		pair_list = np.unique(pair_list)
		for pair in pair_list:
			price_tag  = pair.split('/').pop()+':'+str(binance.fetchTicker(pair)['last'])
			price_list = np.insert(price_list, 0, price_tag)

		sums = df_orders[['side','amount', 'cost']].groupby('side').agg('sum')
		sums['avg_price'] = sums['cost']/sums['amount']
		if sums.loc[sums.index=='buy',].size > 0:
			portfolio.loc[portfolio.index==symbol,['bought']] = sums.loc[sums.index=='buy',['amount']].values[0]
			portfolio.loc[portfolio.index==symbol,['spent']] = sums.loc[sums.index=='buy',['cost']].values[0]
			portfolio.loc[portfolio.index==symbol,['avg_buy_price']] = sums.loc[sums.index=='buy',['avg_price']].values[0]

		if sums.loc[sums.index=='sell',].size > 0:
			portfolio.loc[portfolio.index==symbol,['sold']] = sums.loc[sums.index=='sell',['amount']].values[0]
			portfolio.loc[portfolio.index==symbol,['retrieved']] = sums.loc[sums.index=='sell',['cost']].values[0]
			portfolio.loc[portfolio.index==symbol,['avg_sell_price']] = sums.loc[sums.index=='sell',['avg_price']].values[0]
		portfolio.loc[portfolio.index==symbol,['avg_last_buy_price']] = cst/amt if amt > 0 else 0
		portfolio.loc[portfolio.index==symbol,['market_price']] = ','.join(price_list)


	portfolio['net_usd'] = portfolio.fillna(0)['retrieved'] - portfolio['spent']
	portfolio = portfolio.style.background_gradient()
	dfi.export(portfolio, 'portfolio.png')
	return portfolio

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
	bot.send_message(chat_id, msg)

while True:
	try:
		bot.polling(none_stop=True)
	except Exception as ex:
		print(ex)