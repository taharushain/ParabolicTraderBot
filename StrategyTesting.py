from ta.volatility import BollingerBands, AverageTrueRange
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import IchimokuIndicator, MACD, EMAIndicator, PSARIndicator
import pandas as pd
import pandas_ta as ta
import ta
import math

class StrategyTesting(object):
    def __init__(self, df):
        self.df = df
        self.df['status'] = ''
        self.df['amount_bought'] = 0
        self.df['gain'] = 0
        self.df['balance'] = 0

        self.balance = 100
        self.last_balance = 100
        self.amount_bought = 0
        self.cur_status = ''
        self.stop_multiplier = 3
        # TA Indicators
        bb_ind = BollingerBands(self.df['close'], window=20, window_dev=2)
        atr_ind = AverageTrueRange(self.df.high, self.df.low, self.df.close, window=14)
        rsi_ind = RSIIndicator(self.df['close'])
        stock_rsi_ind = StochRSIIndicator(self.df['close'])
        ichimoku_ind = IchimokuIndicator(self.df['high'], self.df['low']) # TODO
        macd_ind = MACD(self.df['close']) 
        ema20_ind = EMAIndicator(self.df['close'],20)
        ema50_ind = EMAIndicator(self.df['close'],50)
        psar_ind = PSARIndicator(self.df['high'], self.df['low'], (self.df['close']))

        self.df['bb_upper_band'] = bb_ind.bollinger_hband() 
        self.df['bb_lower_band'] = bb_ind.bollinger_lband()
        self.df['bb_moving_average'] = bb_ind.bollinger_mavg()

        self.df['atr'] = atr_ind.average_true_range()

        self.df['rsi'] = rsi_ind.rsi()
        self.df['stock_rsi'] = stock_rsi_ind.stochrsi()
        self.df['stock_rsi_d'] = stock_rsi_ind.stochrsi_d()
        self.df['stock_rsi_k'] = stock_rsi_ind.stochrsi_k()

        self.df['macd'] = macd_ind.macd() # green
        self.df['macd_diff'] = macd_ind.macd_diff() # macd_diff - histogram
        self.df['macd_signal'] = macd_ind.macd_signal() # blue
        self.df['last_macd'] = self.df['macd'].shift(1)

        self.df['ema20'] = ema20_ind.ema_indicator()
        self.df['last_ema20'] = self.df['ema20'].shift(1)
        self.df['ema50'] = ema50_ind.ema_indicator()

        self.df['psar'] = psar_ind.psar()
        self.df['psar_down'] = psar_ind.psar_down()
        self.df['psar_down_indicator'] = psar_ind.psar_down_indicator()
        self.df['psar_up'] = psar_ind.psar_up()
        self.df['psar_up_indicator'] = psar_ind.psar_up_indicator()

        self.df['stop_loss'] = self.df['close'] - self.df['atr'] * self.stop_multiplier
        self.df['stop_profit'] = self.df['close'] + self.df['atr'] * self.stop_multiplier

        self.df.ta.supertrend(append=True) # SUPERTd_7_3.0
        # self.df['SUPERTd_7_3.0'] = self.df['SUPERTd_7_3.0'].fillna(0)
        self.df['SUPERTd_7_3.0'] = self.df['SUPERTd_7_3.0'].fillna(0)
        self.df['last_SUPERTd_7_3.0'] = self.df['SUPERTd_7_3.0'].shift(1).fillna(0).astype(int)

        
    def getBalance(self):
        return self.balance

    def setBalance(self, value):
        self.balance = value
        return self.balance
        
    def bollinger_condition(self, row):
        # print(row['close'], row['high'], row['low'], row['bb_lower_band'], row['bb_upper_band'])
        if(row['close'] <= row['bb_lower_band']):
            return 'buy'
        elif(row['close'] >= row['bb_upper_band']):
            return 'sell'
        # if(row['high'] >= row['bb_lower_band'] and row['low'] <= row['bb_lower_band']):
        #     return 'buy'
        # elif(row['high'] >= row['bb_upper_band'] and row['low'] <= row['bb_upper_band']):
        #     return 'sell'
        else:
            return ''
        
    def supertrend_condition(self, row):
        # print(row['SUPERTd_7_3.0'])
        if(row['last_SUPERTd_7_3.0'] != row['SUPERTd_7_3.0'] and row['SUPERTd_7_3.0'] > 0):
            return 'buy'
        elif(row['SUPERTd_7_3.0'] < 0):
            return 'sell'
        else:
            return ''

    def rsi_condition(self, row):
        # print(row['rsi'])
        if(row['rsi'] <=30):
            return 'buy'
        elif(row['rsi'] >= 60):
            return 'sell'
        else:
            return ''

    def stock_rsi_condition(self, row):
        #stock_rsi_k = blue
        #stock_rsi_d = red
        # print(row['stock_rsi_k'], row['stock_rsi_d'])
        # if(row['stock_rsi'] <=10 and row['stock_rsi_k'] > row['stock_rsi_d']):
        #     return 'buy'
        # elif(row['stock_rsi'] >= 60 or row['stock_rsi_k'] <= row['stock_rsi_d']):
        #     return 'sell'
        if(row['stock_rsi_k'] <= 0.1 and row['stock_rsi_d'] <= 0.1 and row['stock_rsi_k'] > row['stock_rsi_d']): #
            return 'buy'
        elif(row['stock_rsi_k'] >= 0.95):#
            return 'sell'
        else:
            return ''

    def macd_condition(self, row): 
      #A prudent strategy may be to apply a filter to signal line crossovers to ensure that they have held up. An example of a price filter would be to buy if the MACD line 
      #breaks above the signal line and then remains above it for three days. As with any filtering strategy, 
      #this reduces the probability of false signals but increases the frequency of missed profit.
      #macd_diff = histogram
      #macd = blue/green
      #macd_signal = red
        # print(row['macd'], row['macd_signal'], row['macd_diff'])
        if(row['macd'] > row['macd_signal'] and row['macd_diff'] > 0):
            return 'buy'
        elif(row['macd'] <= row['macd_signal'] or row['macd_diff'] <= 0):
            return 'sell'
        else:
            return ''

    def psar_condition(self, row):
        if(math.isnan(row['psar_down']) and math.isnan(row['psar_down']) > 0):
            return 'buy'
        elif(math.isnan(row['psar_up']) and math.isnan(row['psar_up']) > 0):
            return 'sell'
        else:
            return ''

    def ema_20_50_condition(self, row):
        if(row['ema20'] > row['ema50'] and row['ema20'] > row['last_ema20']):
            return 'buy'
        elif(row['ema20'] <= row['ema50'] or row['ema20'] <= row['last_ema20']):
            return 'sell'
        else:
            return ''
    
    def ema_psar_macd_condition(self, row): 
        if(self.ema_20_50_condition(row) == 'buy'
           and self.psar_condition(row) == 'buy' 
           and self.macd_condition(row) == 'buy'):
            return 'buy'
        elif(self.ema_20_50_condition(row) == 'sell'
            or self.psar_condition(row) == 'sell' 
            or self.macd_condition(row) == 'sell'):
            return 'sell'

    def stoch_rsi_bb_condition(self, row): 
        if(self.bollinger_condition(row) == 'buy'
           and self.stock_rsi_condition(row) == 'buy'):
            return 'buy'
        elif(self.bollinger_condition(row) == 'sell'
           or self.stock_rsi_condition(row) == 'sell'):
            return 'sell'

    def stoch_rsi_macd_condition(self, row): 
        if(self.macd_condition(row) == 'buy'
           and self.stock_rsi_condition(row) == 'buy'):
            return 'buy'
        elif(self.macd_condition(row) == 'sell'
           or self.stock_rsi_condition(row) == 'sell'):
            return 'sell'   
            
    def stoch_rsi_ema_condition(self, row): 
        if(self.ema_20_50_condition(row) == 'buy'
           and self.stock_rsi_condition(row) == 'buy'):
            return 'buy'
        elif(self.ema_20_50_condition(row) == 'sell'
           or self.stock_rsi_condition(row) == 'sell'):
            return 'sell' 

    def stoch_rsi_psar_condition(self, row): 
        if(self.psar_condition(row) == 'buy'
           and self.stock_rsi_condition(row) == 'buy'):
            return 'buy'
        elif(self.psar_condition(row) == 'sell'
           or self.stock_rsi_condition(row) == 'sell'):
            return 'sell'  

    def supertrend_macd_condition(self, row): 
        if(self.supertrend_condition(row) == 'buy'
           and self.macd_condition(row) == 'buy'):
            return 'buy'
        elif(self.supertrend_condition(row) == 'sell'
           or self.macd_condition(row) == 'sell'):
            return 'sell' 

    def bollinger_rsi_condition(self, row): 
        if(self.bollinger_condition(row) == 'buy'
           and self.rsi_condition(row) == 'buy'):
            return 'buy'
        elif(self.bollinger_condition(row) == 'sell'
           or self.rsi_condition(row) == 'sell'):
            return 'sell'
    
    def psar_supertrend_condition(self, row): 
        if(self.psar_condition(row) == 'buy'
           and self.supertrend_condition(row) == 'buy'):
            return 'buy'
        elif(self.psar_condition(row) == 'sell'
           or self.supertrend_condition(row) == 'sell'):
            return 'sell'

    def psar_macd_condition(self, row): 
        if(self.psar_condition(row) == 'buy'
           and self.macd_condition(row) == 'buy'):
            return 'buy'
        elif(self.psar_condition(row) == 'sell'
           or self.macd_condition(row) == 'sell'):
            return 'sell'

    def reset_balance(self, balance):
        self.df['status'] = ''
        self.df['amount_bought'] = 0  
        self.df['gain'] = 0
        self.df['balance'] = 0
        self.balance = balance
        self.last_balance = balance
        self.amount_bought = 0
        self.cur_status = ''
        #print(self.balance, self.last_balance)
    
    def buy_order(self,index):
        self.df.loc[index,'status'] = 'bought'
        self.cur_status = 'bought'
        self.amount_bought = self.balance / self.df.loc[index,'close']
        self.last_balance = self.balance
        self.balance = 0
        self.df.loc[index,'amount_bought'] = self.amount_bought
        self.df.loc[index,'balance'] = self.balance
        # print(index, ' || (bought) ', 'amount: ',
        #               self.amount_bought, 'price: ',self.df.loc[index,'close'])
    
    def sell_order(self,index):
        self.df.loc[index,'status'] = 'sold'
        self.cur_status = 'sold'
        self.balance = self.amount_bought * self.df.loc[index,'close']
        gain = self.balance - self.last_balance 
        self.df.loc[index,'amount_bought'] = -self.amount_bought
        self.df.loc[index,'gain'] = gain
        self.df.loc[index,'balance'] = self.balance
        self.amount_bought = 0
        # print(index, ' || (sold) ','amount: ',
        #           -self.amount_bought, 'price: ',self.df.loc[index,'close'], 'gain: ',gain)

    def check_stop_loss(self, index, stop_loss):
        return stop_loss == True and self.df.loc[index,'close'] <= self.df.loc[index,'stop_loss']

    def check_stop_profit(self, index, stop_profit):
        return stop_profit == True and self.df.loc[index,'close'] >= self.df.loc[index,'stop_profit']
    
    def check_enforce_profit(self, index, enforce_profit):
        return enforce_profit == True and self.df.loc[index,'close'] >= self.df.loc[index,'enforce_profit']
    
    def check_daily_trend(self, index, daily_trend):
        return daily_trend == True and self.df.loc[index,'SUPERTd_7_3.0_daily'] > 0

    def handle_order(self, order_type, index, stop_loss=False, stop_profit=False, enforce_profit=False, daily_trend=False):
        if order_type== 'buy':
            self.buy_order(index)
            if stop_loss:
              self.df.loc[index:,'stop_loss'] = self.df.loc[index,'close'] - (self.stop_multiplier*self.df.loc[index,'atr'])
            if stop_profit:
              self.df.loc[index:,'stop_profit'] = self.df.loc[index,'close'] + (self.stop_multiplier*self.df.loc[index,'atr'])
            if enforce_profit:
              self.df.loc[index:,'enforce_profit'] = self.df.loc[index,'close']
        elif order_type== 'sell':
            self.sell_order(index)
#  and (not daily_trend or self.check_daily_trend(index, daily_trend))
    def backtest_handler(self, amount, condition_func, stop_loss=False, stop_profit=False, enforce_profit=False, daily_trend=False):
        self.reset_balance(amount)
        for index, row in self.df.iterrows():
            if(condition_func(row)=='buy' and self.cur_status != ('bought')):
                if (daily_trend and self.check_daily_trend(index, daily_trend)) or not daily_trend:
                    self.handle_order('buy', index, stop_loss, stop_profit, enforce_profit, daily_trend)
            elif(condition_func(row)=='sell' and self.cur_status == 'bought'):
                if (enforce_profit and self.check_enforce_profit(index, enforce_profit)) or not enforce_profit:
                    self.handle_order('sell', index)
            elif(self.check_stop_loss(index, stop_loss) or self.check_stop_profit(index, stop_loss)) and self.cur_status == 'bought':
                if (enforce_profit and self.check_enforce_profit(index, enforce_profit)) or not enforce_profit:
                    self.handle_order('sell', index)
        return self.backtest_stats(condition_func.__name__, stop_loss, stop_profit, enforce_profit, daily_trend)

    def backtest(self, amount, ta, stop_loss=False, stop_profit=False, enforce_profit=False, daily_trend=False):
        if ta == 'bb':
            return self.backtest_handler(amount, self.bollinger_condition, stop_loss, stop_profit, enforce_profit, daily_trend) 
        elif ta == 'st':
            return self.backtest_handler(amount, self.supertrend_condition, stop_loss, stop_profit, enforce_profit, daily_trend) 
        elif ta == 'rsi':
            return self.backtest_handler(amount, self.rsi_condition, stop_loss, stop_profit, enforce_profit, daily_trend) 
        elif ta == 'ema_psar_macd':
            return self.backtest_handler(amount, self.ema_psar_macd_condition, stop_loss, stop_profit, enforce_profit, daily_trend) 
        elif ta == 'stock_rsi':
            return self.backtest_handler(amount, self.stock_rsi_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'macd':
            return self.backtest_handler(amount, self.macd_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'psar':
            return self.backtest_handler(amount, self.psar_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'ema_20_50':
            return self.backtest_handler(amount, self.ema_20_50_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'st_macd':
            return self.backtest_handler(amount, self.supertrend_macd_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'bb_rsi':
            return self.backtest_handler(amount, self.bollinger_rsi_condition, stop_loss, stop_profit, enforce_profit, daily_trend)   
        elif ta == 'sar_st':
            return self.backtest_handler(amount, self.psar_supertrend_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'stoch_rsi_bb':
            return self.backtest_handler(amount, self.stoch_rsi_bb_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'stoch_rsi_macd':
            return self.backtest_handler(amount, self.stoch_rsi_macd_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'stoch_rsi_psar':
            return self.backtest_handler(amount, self.stoch_rsi_psar_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'stoch_rsi_ema':
            return self.backtest_handler(amount, self.stoch_rsi_ema_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
        elif ta == 'psar_macd':
            return self.backtest_handler(amount, self.psar_macd_condition, stop_loss, stop_profit, enforce_profit, daily_trend)
      
    def check_condition(self, ta, row):
        if ta == 'bb':
            return self.bollinger_condition(row) 
        elif ta == 'st':
            return self.supertrend_condition(row) 
        elif ta == 'rsi':
            return self.rsi_condition(row) 
        elif ta == 'ema_psar_macd':
            return self.ema_psar_macd_condition(row) 
        elif ta == 'stock_rsi':
            return self.stock_rsi_condition(row)
        elif ta == 'macd':
            return self.macd_condition(row)
        elif ta == 'psar':
            return self.psar_condition(row)
        elif ta == 'ema_20_50':
            return self.ema_20_50_condition(row)
        elif ta == 'st_macd':
            return self.supertrend_macd_condition(row)
        elif ta == 'bb_rsi':
            return self.bollinger_rsi_condition(row)
        elif ta == 'stoch_rsi_bb':
            return self.stoch_rsi_bb_condition(row)
        elif ta == 'stoch_rsi_macd':
            return self.stoch_rsi_bb_condition(row)
        elif ta == 'stoch_rsi_psar':
            return self.stoch_rsi_bb_condition(row)
        elif ta == 'stoch_rsi_ema':
            return self.stoch_rsi_bb_condition(row)
        elif ta == 'psar_macd':
            return self.psar_macd_condition(row)
        
    def backtest_stats(self, name, stop_loss, stop_profit, enforce_profit, daily_trend):
        pos_sales = self.df.loc[(self.df['status'] == 'sold') & (self.df['gain'] > 0),].count()[0]
        neg_sales = self.df.loc[(self.df['status'] == 'sold') & (self.df['gain'] < 0),].count()[0]
        total_sales = pos_sales + neg_sales
        pos_rate = (pos_sales/total_sales)*100
        gain = self.df['gain'].sum()
        balance = self.getBalance()
        # stats= pd.DataFrame([[name, stop_loss,stop_profit,pos_sales,neg_sales,total_sales,pos_rate,gain,balance]],
        #              columns=['name', 'stop_loss','stop_profit','pos_sales','neg_sales','total_sales','pos_rate','gain','balance']) 
        return [name, stop_loss,stop_profit,enforce_profit,daily_trend,pos_sales,neg_sales,total_sales,pos_rate,gain,balance]
        # print('[',name,'- stop loss: ',stop_loss,'- stop profit: ',stop_profit,']',' Pos: ',pos_sales, ' || Neg: ',neg_sales, ' || Sales: ', total_sales, ' || SuccessRate: ', pos_rate, ' || Gain: ',gain, ' || Balance: ', balance)
        
    def add_daywise_df(self, daywise_df):
        self.df['date'] = self.df.index.date
        daywise_df.ta.supertrend(append=True)
        self.df.date = pd.to_datetime(self.df.date) 
        self.df = pd.merge(
            self.df,
            daywise_df,
            how="left",
            left_on='date',
            right_index=True,
            sort=True,
            suffixes=("", "_daily"),
            copy=True,
            validate = "m:1"
        )

        

