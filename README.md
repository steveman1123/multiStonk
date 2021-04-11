# MultiStonk

A stock trading program that uses multiple algorithms/strategies to trade.

Designed to use the the Alpaca API with plans to incorporate the ETrade API

Algorithm files are stored in ./algos

All user-modifiable settings can be found in ./stonkbot.config

To Run:

 - requires python 3, alpaca api account
 - API keys must be populated in the API key file
 - run ```python3 multistonk.py``` and let it go 24/7 (recommend using a raspberry pi)

## Algo statuses as of 2021-04-10

### stocks
| algo | status|  
| ---: | ---: |
| divs | testing |  
| dj   | done |  
| earn | not done |  
| ema  | ready to test |  
| fda  | done |  
| fda2 | not done |  
| fda3 | ready to test |  
| fib  | not done |  
| gapup| not done |  
| hivol| not done |  
| ipos | not done |  
| movers | not done |  
| reddit | not done |  
| sema | not done |  
| split| not done |  

### forex
| algo | status|  
| ---: | ---: |  
| fib  | not done |  
| hs   | not done |  
  
https://www.forex.com/en-us/education/education-themes/trading-strategies/  


# Program Idea and Structure

multistonk.py contains the main function to run until the portfolio value drops a certain % as well as support functions for that  
The functions in the file there use the config files to determine where files are located, various alpaca account settings, timing settings, and settings for each individual algorithm  
otherfxns.py contains functions that don't require api keys - so strictly calculations or nasdaq api requests
alpacafxns.py contains functions specifically for the alpaca.markets api
forexfxns.py contains functions specifically for the forex.com api
multiForex.py contains a similar setup to multiStonk, but using the forex market instead

Each stock algo file must contain at least the following functions:  
 - getList
 - goodSell
 - sellUpDn
 - sellUp
 - sellDn

At least until further notice.  
