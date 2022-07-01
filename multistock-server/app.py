from flask import Flask,request,jsonify
import stocktwits
import marketWatch
import stocksUnder
import json
app = Flask(__name__)


@app.route('/')
def home():
    return "<h1> multistock-server is running go to  /api/stocktwits-trending/  or /api/stocktwits-suggested/ </h1>"


@app.route('/api/stocktwits-trending/')
def get_stockswits():
    trending = []
    trending.clear()
    _trending = stocktwits.stocktwits_trending()
    for symbols in _trending:
        trending.append(symbols['symbol'])
    return json.dumps(trending)




@app.route('/api/stocktwits-suggested/')
def get_stockswits_suggested():
    suggested = []
    suggested.clear()
    _suggested = stocktwits.stocktwits_suggested()
    for symbols in _suggested:
        suggested.append(symbols['symbol'])
    return json.dumps(suggested)



@app.route('/api/marketwatch/', methods=['POST'])
def marketwatch():
    payload = request.get_json()    
    posted_payload = marketWatch.get_stock(params =payload)
    return jsonify(posted_payload)




@app.route('/api/stocksunder/', methods=['POST'])
def stocksunder():
    payload = request.get_json()    
    posted_payload = stocksUnder.get_stocks_under_1(params_ =payload)
    return jsonify(posted_payload)



if __name__ == '__main__':
    # defult port is 5000
    app.run(host='0.0.0.0', port=5022, debug=True)
    
