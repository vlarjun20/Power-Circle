import time
import json
import requests
from flask import Flask, request, jsonify, render_template,Response
from web3 import Web3
import xgboost as xgb
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd

# Initialize Flask App
app = Flask(__name__)

# Blockchain Connection Setup (Polygon)
WEB3_PROVIDER = "https://polygon-rpc.com"
CONTRACT_ADDRESS = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
PRIVATE_KEY = "private key "
ABI = [
   {
  "constant": False,
  "inputs": [
    {"name": "to", "type": "address"},
    {"name": "value", "type": "uint256"}
  ],
  "name": "transfer",
  "outputs": [{"name": "", "type": "bool"}],
  "stateMutability": "nonpayable",
  "type": "function"
}
]  # Smart contract ABI

web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
contract = web3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

# Sample Data for AI Training (Simulated Data)
data = {
    "energy_generated": np.random.uniform(10, 100, 100),
    "energy_consumed": np.random.uniform(5, 80, 100),
    "demand_supply_ratio": np.random.uniform(0.5, 2, 100),
    "price_per_kWh": np.random.uniform(0.1, 0.5, 100)
}

# Create a DataFrame for simulation
df = pd.DataFrame(data)

# AI Model Setup (XGBoost for Dynamic Pricing)
X = df[["energy_generated", "energy_consumed", "demand_supply_ratio"]]
y = df["price_per_kWh"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = xgb.XGBRegressor()
model.fit(X_train, y_train)

def get_predicted_price(energy_units,total):
    demand_supply_ratio =  total-energy_units # Example calculation
    return model.predict([[energy_units,1,demand_supply_ratio]])[0]

# Blockchain Transaction Function
def trade_energy(producer, consumer, energy_units):
    predicted_price = get_predicted_price(energy_units)
    token_value = energy_units * predicted_price

    txn = contract.functions.transfer(
        web3.to_checksum_address(consumer),
        web3.toWei(token_value, 'ether')
    ).buildTransaction({
        'chainId': 137,
        'gas': 200000,
        'gasPrice': web3.toWei('30', 'gwei'),
        'nonce': web3.eth.getTransactionCount(web3.to_checksum_address(producer)),
    })

    signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = web3.eth.sendRawTransaction(signed_txn.rawTransaction)

    return predicted_price, web3.toHex(tx_hash)

# Gas Price Optimization
def get_gas_price():
    response = requests.get("https://rpc-mainnet.matic.network.")
    gas_data = response.json()
    return gas_data.get("standard", 100)  # Default to 100 if unavailable

def trade_with_gas_optimization(producer, consumer, energy_units):
    gas_price = get_gas_price()
    while gas_price > 100:  # Adjust threshold as needed
        print("High gas price. Waiting...")
        time.sleep(60)
        gas_price = get_gas_price()

    return trade_energy(producer, consumer, energy_units)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/trade", methods=["POST", "GET"])
def trade():
    if request.method == "POST":
        data = request.json
        producer = data["producer"]
        consumer = data["consumer"]
        energy_units = data["energy_units"]

        price, tx_hash = trade_with_gas_optimization(producer, consumer, energy_units)
        return jsonify({
            "predicted_price": price,
            "transaction_hash": tx_hash
        })
    return render_template("trade.html")

@app.route("/predict_price", methods=["POST", "GET"])
def predict_price():
    if request.method == "POST":
        energy_units = request.form.get("energy_units")
        total = request.form.get("total")
        print(energy_units)
        if not energy_units:
            return jsonify({"error": "Energy units are required"}), 400
        try:
            energy_units = float(energy_units)
            total=float(total)
        except ValueError:
            return jsonify({"error": "Invalid energy units. Must be a number."}), 400
        price = get_predicted_price(energy_units,total)
        return render_template("predict.html", price=price)

    return render_template("predict.html", price=None)

# @app.route("/about")
# def about():
#     return render_template("about.html")
@app.route("/dash")
def dash():
    return render_template("dashboard.html")

@app.route("/predict")
def predict():
    return render_template("predict.html")

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
