# MultiStonk

A stock trading program that uses multiple algorithms/strategies to trade.

Designed to use the the Alpaca API

Algorithm files are stored in ./algos

All user-modifiable settings can be found in ./stonkbot.config

The majority of settings are located in ```configs/multi.config```. The default settings will begin live trading. I highly recommend reading through the settings to see what does what and a basic run-through of how the program works in the first place (see also [the stonkbot readme](https://github.com/steveman1123/stonkBot/blob/master/README.md) for a similar setup and running process).  

To Run:

 - requires python 3, alpaca api account
 - API keys must be populated in the API key file
 - move the ```stockStuff``` folder up 1 directory (so it is a sibling rather than a child of multistonk/)
 - run ```python3 multistonk.py``` and let it go 24/7 (recommend using a raspberry pi)  
 
## Algo statuses as of 2021-06-07

### stocks
| algo | status|  
| ---: | ---: |
| accdis | not done |
| divs | done |  
| dj   | done |  
| earn | testing |  
| ema  | not done |  
| eom | not done |
| fda  | done |  
| fda2 | not done |  
| fda3 | done |  
| fib  | not done |  
| gapup| not done |  
| iped | testing |  
| ipos | not done |  
| meme | not done |  
| mfi | not done |
| movers | testing |  
| nvi | not done |
| obv | not done |
| rsi | not done |
| sema | not done |  
| split | not done |  
| vo | not done |
| vpt | not done |
| vwap | not done |



# Program Idea and Structure

```multistonk.py``` contains the main function to run until the portfolio value drops a certain % as well as support functions for that  
The functions in the file there use the config files to determine where files are located, various alpaca account settings, timing settings, and settings for each individual algorithm  
```otherfxns.py``` contains functions that don't require api keys - so strictly calculations or nasdaq api requests
```alpacafxns.py``` contains functions specifically for the alpaca.markets api
```algos/``` - contains the files for each algorithm
```configs/``` - contains the config files for the bot. Additional config files can be specified for the bot, provided they're formatted similarily to multi.config
```stockStuff/``` - contains historical data for stocks and api keys (the keys must be populated and the folder must be moved as specified above before running)
  
  
Each stock algo file must contain at least the following functions:  
 - ```init``` - initialize the algo with the proper config and settings
 - ```getList``` - return a dict of {symb:note} for stocks to buy for the given algo
 - ```goodSells``` - return a dict of {symb: t/f} whether a stock is a good one to sell or not
 - ```sellUp``` - high end trigger point
 - ```sellDn``` - low end trigger point
 - ```sellUpDn``` - return the value for the stock price to drop by after triggering as a goodSell

