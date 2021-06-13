[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/taharushain/ParabolicTraderBot/blob/main/LICENSE)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/taharushain/ParabolicTraderBot/issues)


# Parabolic Trader Bot

There are two bots that need to be used simultaneously.

- Trader Bot (bot.py)
- TelegramBot (TelegramBot.py)

## Getting Started

1. Install python libraries as mentioned in requirements.txt file
2. update config file with appropriate keys
3. once deployed, execute following to initialize db

```
python db_init.py
```
*This project uses sqlite which is sufficient at this scale.*

### StrategyTesting

The StrategyTesting class is where the legwork is done and contains the required Technical Analysis indicators. Currently, there is support for the following basic indicators.

 - Bollinger Bands
 - Super Trend
 - RSI
 - MACD
 - PSAR
 - EMA 20 and 50
 - and some combinations of the above

### Notebook
A notebook is provided that uses the StrategyClass to backtest different currency pairs, use it throughly before deciding any strategy to trade on. 

*This notebook uses Coinbase for historical data and the trader currently is used for Binance, which is not apples to apples comparison and some currency pairs may not be found*

### Feel free to contribute
This project is under development and requires contribution, feel free to send your PR if you make any improvements.

### Final Note and Disclaimer
This project is for education purpose only and is under development, use it at your own risk. Also make sure to backtest any strategy that you wish to deploy on a live account.

***Provided technical indicators are very basic and if used carelessly may result in loss***