from flask import Flask,request,jsonify
import stocktwits
import marketWatch
import stocksUnder
app = Flask(__name__)


@app.route('/')
def home():
    return "<h1> multistock-server is running </h1>"


@app.route('/api/stocktwits-trending/')
def get_stockswits():
    _trending = stocktwits.stocktwits_trending()
    trending = list(dict.fromkeys(_trending))
    return jsonify(trending)




@app.route('/api/stocktwits-suggested/')
def get_stockswits_suggested():
    _suggested = stocktwits.stocktwits_suggested()
    suggested = list(dict.fromkeys(_suggested))
    return jsonify(suggested)



@app.route('/api/marketwatch/', methods=['POST'])
def marketwatch():
    payload = request.get_json()    
    posted_payload = marketWatch.get_stock(params =payload)
    market_watch_ = list(dict.fromkeys(posted_payload))
    return jsonify(market_watch_)



@app.route('/api/stocksunder/', methods=['POST'])
def stocksunder():
    payload = request.get_json()    
    posted_payload = stocksUnder.get_stocks_under_1(params_ =payload)
    stocksunder_ = list(dict.fromkeys(posted_payload))
    return jsonify(stocksunder_)



app.route('/api/ping/', methods=['GET'])
def ping():
    
    
    return jsonify({"ping": "pong"})





if __name__ == '__main__':
    # defult port is 5000
    app.run(host='0.0.0.0', port=80, debug=True)
    
