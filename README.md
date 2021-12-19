# MultiStonk Extended for Robinhood:
### Disclimer: robinhood doesn't support continuous multiple calls to its endpoints.


This is a mirror implementation of the [main repo](https://github.com/steveman1123/multiStonk)
    clone the branch: 

    git clone -b robinhood https://github.com/Nllii/multiStonk.git


install required packages from requirements.txt ```pip install -r requirements.txt```

Enter account information in ```robinhood_config.toml``` 

All preferences are in ```robinhood_config.toml```
You will need to enable TOTPS(mfa_code) in your robinhood account or type in your username and password in the console each time.

[need more algos](https://github.com/steveman1123/multiStonk/tree/main/algos) put your algos in ```./user_algorithms/``` 

TODO: 
- [x] get sell and buy function working on robinhood:
- [ ] fix cng frm cls
- [ ] Fix sell all function
- [ ] unrealized_intraday_plpc needs to fix 
  - Testing: Total percent change:
  - Testing: Today's Return 
  - 
- [ ] catch all errors when robinhood random stops working during trading hours.
- 
## Testing is required: Monday/12/2021


##
A stock trading program that uses multiple algorithms/strategies to trade.

Designed to use the the Alpaca API

Algorithm files are stored in ./algos

All user-modifiable settings should be found in ```./configs/multi.config``` and ```./config/other.config```

The majority of settings are located in ```configs/multi.config```. The default settings will begin live trading, this can be adjusted to paper trading if desired. I highly recommend reading through these settings to see what does what and a basic run-through of how the program works in the first place (see also [the stonkbot readme](https://github.com/steveman1123/stonkBot/blob/master/README.md) for a similar setup and running process).  

To Run:

 - requires python 3, alpaca api account
 - API keys must be populated in the API key file (located in ```./stockStuff/apikeys/keys.txt```)
 - move the ```stockStuff/``` folder up 1 directory (so it is a sibling rather than a child of ```multistonk/```)
 - run ```python3 multistonk.py``` and let it go 24/7 (recommend using a raspberry pi)  
 


# Program Idea and Structure

```multistonk.py``` contains the main function to run until the portfolio value drops a certain % as well as support functions for that  
The functions in the file there use the config files to determine where files are located, various alpaca account settings, timing settings, and settings for each individual algorithm  
```otherfxns.py``` contains functions that don't require api keys - so strictly calculations or nasdaq api requests
```alpacafxns.py``` contains functions specifically for the alpaca.markets api
```algos/``` - contains the files for each algorithm
```configs/``` - contains the config files for the bot. Additional config files can be specified for the bot, provided they're formatted similarily to ```multi.config```
```stockStuff/``` - contains historical data for stocks and api keys (the keys must be populated and the folder must be moved as specified above before running)
  
  
Each stock algo file must contain at least the following functions (as these are what are directly called from ```multistonk.py```):  
 - ```init``` - initialize the algo with the proper config and settings
 - ```getList``` - return a dict of {symb:note} for stocks to buy for the given algo
 - ```goodSells``` - return a dict of {symb: t/f} whether a stock is a good one to sell or not
 - ```sellDn``` - low end trigger point (stop loss % relative to price bought)
 - ```sellUp``` - high end trigger point (trigger point % relative to price bought)
 - ```sellUpDn``` - return the value for the stock price to drop by after triggering as a goodSell (trailing stop loss % relative to max price since bought)




<!-- git update-index --no-assume-unchanged robinhood_config.toml -->
<!-- git commands -->
<!-- Trusting git will not push my auth to the public lol -->
<!-- git update-index --assume-unchanged robinhood_config.toml -->
<!-- git ls-files -v|grep '^h' -->

<!-- http://git-scm.com/docs/git-update-index -->