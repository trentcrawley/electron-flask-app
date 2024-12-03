
#This is new verson to get scanner data from IB and then we use yfinance as ib difficult
import threading
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.scanner import ScannerSubscription


class ScannerApp(EWrapper, EClient):
    def __init__(self, scan_number, exchange):
        EClient.__init__(self, self)
        self.tickers = []
        self.scann_subscription_number = scan_number
        self.exchange = exchange
        self.data_event = threading.Event()  # Add an event to signal completion

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        symbol = contractDetails.contract.symbol
        self.tickers.append(symbol)

    def scannerDataEnd(self, reqId):
        print('Received all scanner data')
        print(self.tickers)
        self.cancelScannerSubscription(self.scann_subscription_number)
        self.disconnect()  # Properly disconnect after data is received
        self.data_event.set()  # Signal completion

    def nextValidId(self, orderId: int):
        print(f"Received next valid order ID: {orderId}")
        self.start()

    def start(self):
        subscription = ScannerSubscription()
        if self.exchange == "ASX":
            subscription.instrument = "STOCK.HK"
            subscription.locationCode = "STK.HK.ASX"
        elif self.exchange == "US":
            subscription.instrument = "STK"
            subscription.locationCode = "STK.US.MAJOR"

        subscription.numberOfRows = 500
        subscription.scanCode = "TOP_PERC_GAIN"  # Scanning for top percentage gainers
        subscription.marketCapAbove = 8
        subscription.abovePrice = 0.03
        print(f"Requesting scanner subscription {self.scann_subscription_number}")
        self.reqScannerSubscription(self.scann_subscription_number, subscription, [], [])

    def cancelScannerSubscription(self, reqId: int):
        print(f"Scanner subscription cancelled for {reqId}")
        super().cancelScannerSubscription(reqId)

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=''):
        print(f"Error. ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}, AdvancedOrderRejectJson: {advancedOrderRejectJson}")

def run_scanner(scan_number, exchange):
    app = ScannerApp(scan_number, exchange)
    app.connect("127.0.0.1", 7496, 12)
    # Start the client in a new thread to prevent blocking the main thread
    threading.Thread(target=app.run).start()

    # Wait until data has been received and processed
    app.data_event.wait()

    return app.tickers


def get_scanner_tickers(scan_number, exchange):
    tickers = run_scanner(scan_number, exchange)
    if tickers:
        print(f'Tickers from scanner: {tickers}')
        return tickers
    else:
        print('Error: No data received')
        return []


# Example usage
#tickers = get_scanner_tickers(scan_number=5, exchange="ASX")
