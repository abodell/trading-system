from brokers.alpaca_broker import AlpacaBroker

def main():
    broker = AlpacaBroker(paper = True)

    print("Account summary:")
    print(broker.get_account_summary())

    print("\nOpen positions:")
    print(broker.get_positions())

if __name__ == "__main__":
    main()