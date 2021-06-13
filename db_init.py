from DBHandler import DBHandler
import config

db = DBHandler()

db.reset_db()

# ta, symbol, scale, stop_loss, stop_profit, enforce_profit, daily_trend, chat_id
db.insert_params('stock_rsi', 'MATIC/USDT', '1m', 0, 0, 1, 0, config.TELEGRAM_CHAT_ID)

# # order_type, price, param_id, stop_loss_price, stop_profit_price, timestamp, amount_bought
# db.insert_order('buy', '10', 1, 10, 10, '2021-01-01', 100)

# dt = db.get_params()
# print(dt)