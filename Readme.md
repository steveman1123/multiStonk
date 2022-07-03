
This is a mirror implementation of the [main repo](https://github.com/steveman1123/multiStonk) to be used with robinhood. 

### This is experimental.

    required for login: - TOTPS and alpaca API keys 
    

Moved all stocks required for trading to  multistock-server which is running on a server and returns the data in a json format. This is done for maintenance reasons and to debug failing apis in the future.

For emailing alerts: use apple and yahoo. 


TODO:

- [-]   Add trading time from main repo.
- [x] Add support for robinhood and alpaca(used for market time and getting some data)
- [-] Implement all features of the main repo without re-writing code.


- [x] write createOrder function using limit order.
- [x] write sell function.
- [x] write buy function.

- [x] Add support for Docker for getting api server for future needs.
- [x] Do a pull requests 

- [x] prevent duplicate orders during limit orders.
- [x] fix limit orders and syncing issues. 
- [x] Tested limit orders.


- [ ] Fix issues with is_pending not updating.
- [ ] A Docker instance or create systemd background simple task for the server to run in the background. 
- [ ] The server is managing the watchlist and sending email alerts.
- [ ] write watchlist class function.
- [ ] write email class.
- [ ] Add support for watchlist.

- [ ] Add support emailing alerts and news.(emailing will be used for alerts and news)










notes:
Robinhood hours for trading has changed, keeping the original hours since we are not stupid enough to trade outside liquid hours.

graphql may help, but thats too much work. It is better to use the api directly instead of querying.

autopep8 -i convert-to-tabs.py