import json
import mstarpy
import datetime
from collections import defaultdict

# Function to load transaction data from a JSON file
def load_transactions(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        print("Loaded transactions:", data)  # Debugging line
        return data

# Function to calculate the total portfolio value and gain
def calculate_portfolio(transactions):
    folio_data = defaultdict(lambda: defaultdict(list))
    total_gain = 0

    # Process transactions
    for trxn in transactions:
        folio = trxn['folio']
        scheme_name = trxn['schemeName']
        isin = trxn['isin']
        units = float(trxn['trxnUnits'])
        purchase_price = float(trxn['purchasePrice'])
        
        # Add the transaction to folio data
        folio_data[folio][isin].append({
            'units': units,
            'purchase_price': purchase_price,
            'trxnDate': trxn['trxnDate']
        })

    # Calculate current NAV for each fund
    for folio, schemes in folio_data.items():
        for isin, transactions in schemes.items():
            fund = mstarpy.Funds(term=isin, country="in")
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=365)
            history = fund.nav(start_date=start_date, end_date=end_date, frequency="daily")

            # Check if history is in expected format
            if isinstance(history, list) and len(history) > 0:
                # Assuming the last entry has the most recent NAV
                current_nav = history[-1]['nav']  # Accessing the NAV directly from the last entry
            else:
                print(f"No NAV data available for ISIN: {isin}")
                continue

            total_units = 0
            total_acquisition_cost = 0
            
            # Calculate total units and total acquisition cost using FIFO
            for trxn in transactions:
                if trxn['units'] > 0:  # Buy transaction
                    total_units += trxn['units']
                    total_acquisition_cost += trxn['units'] * trxn['purchase_price']
                elif trxn['units'] < 0:  # Sell transaction
                    total_units -= abs(trxn['units'])
                    # Calculate cost for sold units
                    units_to_sell = abs(trxn['units'])
                    while units_to_sell > 0 and transactions:
                        buy_units = transactions[0]['units']
                        if buy_units > units_to_sell:
                            total_acquisition_cost += units_to_sell * transactions[0]['purchase_price']
                            transactions[0]['units'] -= units_to_sell
                            units_to_sell = 0
                        else:
                            total_acquisition_cost += buy_units * transactions[0]['purchase_price']
                            units_to_sell -= buy_units
                            transactions.pop(0)  # Remove the transaction if all units are sold

            # Calculate portfolio value and gain
            current_value = total_units * current_nav
            total_gain += (current_value - total_acquisition_cost)

            print(f"Scheme: {scheme_name}, Folio: {folio}, Units: {total_units}, Current Value: {current_value:.2f}, Total Gain: {total_gain:.2f}")

    return total_gain

# Main execution
if __name__ == "__main__":
    # Path to the JSON file containing transaction details
    transactions_file_path = 'C:/Users/Acer/OneDrive/Desktop/Test/transaction_detail.json'
    
    # Load transactions from the specified JSON file
    transactions = load_transactions(transactions_file_path)
    
    # Calculate total gain from the portfolio
    total_gain = calculate_portfolio(transactions)
    
    # Print total portfolio gain
    print(f"Total Portfolio Gain: {total_gain:.2f}")
