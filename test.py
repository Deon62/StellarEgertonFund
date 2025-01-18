from stellar_sdk import Keypair

# Generate a new Stellar keypair
keypair = Keypair.random()
print("Public Key (Wallet Address):", keypair.public_key)
print("Secret Key:", keypair.secret)
