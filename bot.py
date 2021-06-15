from datetime import datetime
import pandas as pd
import ccxt
import json
import config
import schedule
from StrategyTesting import StrategyTesting 
import time
import sqlite3
from DBHandler import DBHandler
import telebot
import warnings
warnings.filterwarnings("ignore")

def init_variables():	
	global db, params, binance, bot, chat_id
	db = DBHandler()
	params = db.get_params()
	API_KEY = config.TELEGRAM_TOKEN
	bot = telebot.TeleBot(API_KEY)

	binance = ccxt.binance ({
	    'options': {
	        'adjustForTimeDifference': True, 
	    },
	    'enableRateLimit': True,
	    'apiKey': config.BINANCE_API_KEY,
	    'secret': config.BINANCE_SECRET_KEY,
	})

	chat_id = params['chat_id']

# markets = binance.load_markets()

def send_notification(msg):
	bot.send_message(chat_id, msg)


def buy_order(symbol, st):
	## get price and amount
	usdt_to_use = float(binance.fetch_balance().get(symbol.split('/')[1]).get('free'))
	symbol_price = float(binance.fetchTicker(symbol).get('last'))
	amount_to_buy = usdt_to_use / symbol_price
	## place order
	# order = binance.createMarketBuyOrder(symbol, amount_to_buy)

	# extra params and overrides if needed
	binance_params={}
	isTestRun = db.get_testrun_status()['test_run']
	if isTestRun == 1:
		binance_params = {
			'test': True,  # test if it's valid, but don't actually place it
		}
	order = binance.createOrder(symbol, 'market', 'buy', amount_to_buy, symbol_price, binance_params)
	stop_loss_price = st.df.iloc[-1]['stop_loss']
	stop_profit_price = st.df.iloc[-1]['stop_profit']
	db.insert_order('buy', order['price'], params['id'], stop_loss_price, stop_profit_price, order['datetime'], order['amount'])

	db_order = json.dumps(db.get_order(), indent=2)
	send_notification(db_order)
	print(db_order)
	# print(amount_to_buy, symbol_price, stop_loss_price, stop_profit_price)

def sell_order(symbol, st, last_order):
	## get price and amount
	amount_to_sell = float(binance.fetch_balance().get(symbol.split('/')[0]).get('free'))
	symbol_price = float(binance.fetchTicker(symbol).get('last'))
	## place order
	# extra params and overrides if needed
	isTestRun = db.get_testrun_status()['test_run']
	binance_params={}
	if isTestRun == 1:
		binance_params = {
			'test': True,  # test if it's valid, but don't actually place it
		}
	order = binance.createOrder(symbol, 'market', 'sell', amount_to_sell, symbol_price, binance_params)
	# stop_loss_price = st.df.iloc[-1]['stop_loss']
	# stop_profit_price = st.df.iloc[-1]['stop_profit']
	db.insert_order('sell', order['price'], last_order['param_id'], last_order['stop_loss_price'], last_order['stop_profit_price'], order['datetime'], order['amount'])
	
	db_order = json.dumps(db.get_order(), indent=2)
	send_notification(db_order)
	print(db_order)
	# print(amount_to_sell, symbol_price, last_order['stop_loss_price'], last_order['stop_profit_price'])

def check_condition(ta, st):
	row = st.df.iloc[-1]
	signal = st.check_condition(ta, row)
	print(ta, " - signal: ", signal, row['stop_loss'], row['stop_profit'], st.stop_multiplier)
	return signal

def check_buy_sell_signals(st):
	isEnabled = db.get_enable_status()['execute_orders']
	last_order = db.get_order()
	signal = check_condition(params['ta'], st)
	# print(params['ta'])
	if(signal == 'buy' and isEnabled == 1):
		if(not last_order or (last_order and last_order['order_type'] == 'sell')):
			if(params['daily_trend'] == 1 and st.df.iloc[-1]['SUPERTd_7_3.0_daily'] > 0):
				buy_order(params['symbol'], st)
			elif(params['daily_trend'] != 1):
				buy_order(params['symbol'], st)
	elif(last_order and last_order['order_type'] == 'buy'):
		order_params = db.get_params(last_order['param_id'])
		symbol_price = float(binance.fetchTicker(order_params['symbol']).get('last'))
		if(signal == 'sell'):
			last_order['price'] = float(last_order['price']) if last_order['price'] else 0
			if(order_params['enforce_profit'] == 1 and symbol_price > last_order['price']):
				sell_order(order_params['symbol'], st, last_order)	
			elif(order_params['enforce_profit'] != 1):
				sell_order(order_params['symbol'], st, last_order)	
		elif(order_params['stop_loss'] == 1 and symbol_price <= float(last_order['stop_loss_price'])):
			sell_order(order_params['symbol'], st, last_order)
		elif(order_params['stop_profit'] == 1 and symbol_price >= float(last_order['stop_profit_price'])):
			sell_order(order_params['symbol'], st, last_order)

def execute_bot():
	init_variables()
	if params:
		try:
			print(f'Fetching Ticker Data for {datetime.now().isoformat()}')
			tickers = binance.fetch_ohlcv(params['symbol'], timeframe=params['scale'], limit=100)
			df = pd.DataFrame(tickers[:-1], columns=['time', 'open', 'high', 'low','close', 'volume'])
			df['time'] = pd.to_datetime(df['time'], unit='ms')
			df.set_index(pd.DatetimeIndex(df["time"]), inplace=True)

			daily_tickers = binance.fetch_ohlcv(params['symbol'], timeframe=params['scale'], limit=100)
			daily_df = pd.DataFrame(daily_tickers[:-1], columns=['time', 'open', 'high', 'low','close', 'volume'])
			daily_df['time'] = pd.to_datetime(daily_df['time'], unit='ms')
			daily_df.set_index(pd.DatetimeIndex(daily_df["time"]), inplace=True)

			st = StrategyTesting(df)
			st.add_daywise_df(daily_df)

			check_buy_sell_signals(st)
		except Exception as e:
			send_notification(e)
			print(e)

# init_variables()

schedule.every(60).seconds.do(execute_bot)
while True:
	schedule.run_pending()
	time.sleep(1)