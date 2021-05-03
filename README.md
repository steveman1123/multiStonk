# MultiStonk

A stock trading program that uses multiple algorithms/strategies to trade.

Designed to use the the Alpaca API with plans to incorporate the ETrade API

Algorithm files are stored in ./algos

All user-modifiable settings can be found in ./stonkbot.config

To Run:

 - requires python 3, alpaca api account
 - API keys must be populated in the API key file
 - run ```python3 multistonk.py``` and let it go 24/7 (recommend using a raspberry pi)

## Algo statuses as of 2021-05-01

### stocks
| algo | status|  
| ---: | ---: |
| accdis | not done |
| divs | done |  
| dj   | done |  
| earn | not done |  
| ema  | not done |  
| eom | not done |
| fda  | done |  
| fda2 | not done |  
| fda3 | done |  
| fib  | not done |  
| gapup| not done |  
| ipos | not done |  
| mfi | not done |
| movers | not done |  
| nvi | not done |
| obv | not done |
| reddit | not done |  
| rsi | not done |
| sema | not done |  
| split| not done |  
| vo | not done |
| vpt | not done |
| vwap | not done |



# Program Idea and Structure

```multistonk.py``` contains the main function to run until the portfolio value drops a certain % as well as support functions for that  
The functions in the file there use the config files to determine where files are located, various alpaca account settings, timing settings, and settings for each individual algorithm  
```otherfxns.py``` contains functions that don't require api keys - so strictly calculations or nasdaq api requests
```alpacafxns.py``` contains functions specifically for the alpaca.markets api


Each stock algo file must contain at least the following functions:  
 - ```init``` - initialize the algo with the proper config and settings
 - ```getList``` - return a dict of {symb:note} for stocks to buy for the given algo
 - ```goodSells``` - return a dict of {symb: t/f} whether a stock is a good one to sell or not
 - ```sellUpDn``` - return the value for the stoc price to drop by after triggering as a goodSell
 - ```sellUp``` - high end trigger point
 - ```sellDn``` - low end trigger point

