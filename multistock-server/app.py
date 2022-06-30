from flask import Flask
import stocktwits 
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



if __name__ == '__main__':
    # defult port is 5000
    app.run(host='0.0.0.0', port=80, debug=True)
    
