import sqlite3
import os


class DBHandler(object):
	def __init__(self):
		self.con = sqlite3.connect('binance_bot.db')
		

	def reset_db(self):
		self.create_params_table()
		self.create_enabled_tables()
		self.create_orders_table()

	def create_params_table(self):
		self.cur = self.con.cursor()
		
		self.cur.execute('drop table if exists params')
		self.cur.execute('''CREATE TABLE params
		               ( _id INTEGER PRIMARY KEY, ta TEXT, symbol TEXT, scale TEXT, stop_loss NUMERIC, stop_profit NUMERIC, enforce_profit NUMERIC, daily_trend NUMERIC, chat_id TEXT)
		               ''')
		self.con.commit()
		self.cur.close()

	def create_enabled_tables(self):
		self.cur = self.con.cursor()

		self.cur.execute('drop table if exists enabled')
		self.cur.execute('''CREATE TABLE enabled
		               ( execute_orders NUMERIC)
		               ''')
		self.cur.execute('''insert into enabled (execute_orders)
               values (1);''')

		self.con.commit()
		self.cur.close()

	def create_orders_table(self):
		self.cur = self.con.cursor()
		self.cur.execute('drop table if exists orders')
		self.cur.execute('''CREATE TABLE orders
		               ( _id INTEGER PRIMARY KEY, order_type TEXT, price TEXT, param_id id, stop_loss_price TEXT, stop_profit_price NUMERIC, timestamp TEXT, amount_bought TEXT)
		               ''')
		self.con.commit()
		self.cur.close()

	def insert_params(self, ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend, chat_id):
		self.cur = self.con.cursor()
		self.cur.execute('''insert into params (ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend, chat_id) 
						values (?, ?, ?, ?, ?, ?, ?, ?)''', (ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend, chat_id))
		self.con.commit()
		self.cur.close()
		
	def update_enable_status(self, enable):
		self.cur = self.con.cursor()
		if enable=='1':
			update_query = f'''update enabled
					set execute_orders = 1;'''
			self.cur.execute(update_query)
		elif enable=='0':
			update_query = f'''update enabled
					set execute_orders = 0;'''
			self.cur.execute(update_query)

		self.con.commit()
		self.cur.close()

	def insert_order(self, order_type, price, param_id, stop_loss_price, stop_profit_price, timestamp, amount_bought):
		self.cur = self.con.cursor()
		self.cur.execute('''insert into orders (order_type, price, param_id, stop_loss_price, stop_profit_price, timestamp, amount_bought) 
				values (?, ?, ?, ?, ?, ?, ?)''', (order_type, price, param_id, stop_loss_price, stop_profit_price, timestamp, amount_bought))
		self.con.commit()
		self.cur.close()

	def get_params(self, id=None):
		self.cur = self.con.cursor()
		keys=['id', 'ta', 'symbol', 'scale', 'stop_loss', 'stop_profit', 'enforce_profit', 'daily_trend', 'chat_id']
		if id:
			self.cur.execute("select * from params where _id=:id", {"id": id})
		else:
			self.cur.execute("select * from params where _id=(select max(_id) _id from params)")
		result_set = self.cur.fetchone()
		self.cur.close()
		return self.get_dict_from_cursor(keys, result_set)

	def get_order(self, id=None):
		self.cur = self.con.cursor()
		keys=['id', 'order_type', 'price', 'param_id', 'stop_loss_price', 'stop_profit_price', 'timestamp', 'amount_bought']
		if id:
			self.cur.execute("select * from orders where _id=:id", {"id": id})
		else:
			self.cur.execute("select * from orders where _id=(select max(_id) _id from orders)")
		result_set = self.cur.fetchone()
		self.cur.close()
		return self.get_dict_from_cursor(keys, result_set)

	def get_enable_status(self):
		self.cur = self.con.cursor()
		keys=['execute_orders']
		self.cur.execute("select execute_orders from enabled")
		result_set = self.cur.fetchone()
		self.cur.close()
		return self.get_dict_from_cursor(keys, result_set)

	def get_dict_from_cursor(self, keys, values):
		if values:
			return dict(zip(keys, values))