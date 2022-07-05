from flask import Flask,request,jsonify
import stocktwits
import marketWatch
import stocksUnder
import syncWatchlist
import time
try:
    import buyhold
except Exception as e:
    print(e)
    


app = Flask(__name__)


@app.route('/')
def home():
    return "<h1> multistock-server is running </h1>"


@app.route('/api/stocktwits-trending/')
def get_stockswits():
    _trending = stocktwits.stocktwits_trending()
    # trending = list(dict.fromkeys(_trending))
    return jsonify(_trending)




@app.route('/api/stocktwits-suggested/')
def get_stockswits_suggested():
    _suggested = stocktwits.stocktwits_suggested()
    # suggested = list(dict.fromkeys(_suggested))
    return jsonify(_suggested)



@app.route('/api/marketwatch/', methods=['POST'])
def marketwatch():
    payload = request.get_json()    
    posted_payload = marketWatch.get_stock(params =payload)
    # market_watch_ = list(dict.fromkeys(posted_payload))
    return jsonify(posted_payload)



@app.route('/api/stocksunder/', methods=['POST'])
def stocksunder():
    payload = request.get_json()    
    posted_payload = stocksUnder.get_stocks_under_1(params_ =payload)
    # stocksunder_ = list(dict.fromkeys(posted_payload))
    return jsonify(posted_payload)








@app.route('/api/make_watchlist/', methods=['POST'])
def makewatchlist():
    payload = request.get_json()    
    posted_payload = syncWatchlist.make_watchlist(token =payload['token'],wl_name= payload['wl_name'])
    # stocksunder_ = list(dict.fromkeys(posted_payload))
    return jsonify(posted_payload)



@app.route('/api/buyholdsell/')
def buyholdselling():
    buyhold_data = buyhold.bsholddata()
    return jsonify(buyhold_data)






if __name__ == '__main__':
    # defult port is 5000
    app.run(host='0.0.0.0', port=80, debug=True)
    
