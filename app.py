from flask import Flask, render_template, request, jsonify
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, Payment
from datetime import datetime, timezone

app = Flask(__name__,
    template_folder='templates',  # Correct template folder reference
    static_folder='static'
)

# Stellar setup
server = Server("https://horizon-testnet.stellar.org")

# Define Stellar keys
Public_Key = "GCLFID6YRVLV6XHID4TWTOOYV2LEFBJBXEGSXL6V3L3DKDWA4NVU73WX"
Secret_Key = "SBAPPZ5XCQ6KSFOCYQ3UEJSMMC76HM6IAF7N4OH5YK3M4HCIA7V4RLTX"

# In-memory campaigns storage
campaigns = []

def create_campaign(title, description, target, wallet):
    if not (wallet.startswith('G') and len(wallet) == 56):
        raise ValueError("Invalid Stellar wallet address. Must start with 'G' and be 56 characters long.")
    return {
        "title": title,
        "description": description,
        "target": target,
        "wallet": wallet,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

def contribute_to_campaign(destination_wallet, amount):
    source_keypair = Keypair.from_secret(Secret_Key)
    source_account = server.load_account(source_keypair.public_key)
    transaction = (
        TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=100
        )
        .add_text_memo("Contribution")
        .add_operation(
            Payment(
                destination=destination_wallet,
                asset=Asset.native(),
                amount=str(amount)
            )
        )
        .set_timeout(30)
        .build()
    )
    transaction.sign(source_keypair)
    return server.submit_transaction(transaction)

def get_campaign_data(wallet):
    try:
        payments = server.payments().for_account(wallet).limit(10).order("desc").call()
        return [
            {
                "from": record["from"],
                "amount": record["amount"],
                "timestamp": record["created_at"]
            }
            for record in payments["_embedded"]["records"]
            if record["type"] == "payment"
        ]
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html', campaigns=campaigns)

@app.route('/campaign', methods=['POST'])
def create_new_campaign():
    campaign = create_campaign(
        request.form['title'],
        request.form['description'],
        request.form['target'],
        request.form['wallet']
    )
    campaigns.append(campaign)
    return render_template('index.html', campaigns=campaigns)

@app.route('/contribute', methods=['POST'])
def contribute():
    try:
        campaign_id = int(request.form['campaign_id'])
        response = contribute_to_campaign(
            campaigns[campaign_id]['wallet'],
            request.form['amount']
        )
        return jsonify({"message": "Contribution successful!", "response": response})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/campaign/<int:campaign_id>')
def view_campaign(campaign_id):
    data = get_campaign_data(campaigns[campaign_id]['wallet'])
    return render_template('campaign.html', campaign=campaigns[campaign_id], data=data)

if __name__ == '__main__':
    app.run(debug=True)
