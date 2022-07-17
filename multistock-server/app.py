from flask import Flask,request,jsonify
import stocktwits
import marketWatch
import stocksUnder
import syncWatchlist
import time
import json
import os
try:
    import buyhold
except ImportError:
    raise ImportError('this is a private api. Sorry.')

    


app = Flask(__name__)


@app.route('/')
def home():
    is_online = {
        'status': 'online'
    }
    return jsonify(is_online)



@app.route('/api/stocktwits-trending/')
def get_stockswits():
    _trending = stocktwits.stocktwits_trending()
    return jsonify(_trending)




@app.route('/api/stocktwits-suggested/')
def get_stockswits_suggested():
    _suggested = stocktwits.stocktwits_suggested()
    return jsonify(_suggested)



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








@app.route('/api/make_watchlist/', methods=['POST'])
def makewatchlist():
    payload = request.get_json()    
    posted_payload = syncWatchlist.make_watchlist(token =payload['token'],wl_name= payload['wl_name'])
    return jsonify(posted_payload)



@app.route('/api/buyholdsell/')
def buyholdselling():
    buyhold_data = buyhold.bsholddata()
    return jsonify(buyhold_data)



@app.route('/api/post_ngrok_address/', methods=['POST'])
def post_ngrok():
    posted_payload = request.get_json()
    with open('ngrok_address.txt', 'w') as f:
        json.dump(posted_payload, f)
    return jsonify(posted_payload)



@app.route('/api/get_ngrok_address/')
def get_ngrok():
    with open('ngrok_address.txt', 'r') as f:
        _address = json.load(f)
        tcp_address = _address['tcp']

    return jsonify(tcp_address)



#TODO: rethink this route
@app.route('/api/post_ml_requests/', methods=['POST'])
def ml_requests():
    ml_req = request.get_json() 
    with open('ml_requests.txt', 'w') as f:
        json.dump(ml_req, f)
    return jsonify(ml_req)

    
@app.route('/api/get_ml_requests/')
def get_ml_requests():
    with open('ml_requests.txt', 'r') as f:
        predict_ = json.load(f)
        # delete the file
        os.remove('ml_requests.txt')
    return jsonify(predict_)

    




if __name__ == '__main__':
    # defult port is 5000
    app.run(host='0.0.0.0', port=80, debug=True)
    
