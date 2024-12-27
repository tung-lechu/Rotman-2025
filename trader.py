# This is a python example algorithm using DMA REST API for the RIT ALGO1 Case

import signal
import requests
from time import sleep
import base64

# this class definition allows us to print error messages and stop the program when needed
class ApiException(Exception):
    pass

# this signal handler allows for a graceful shutdown when CTRL+C is pressed
def signal_handler(signum, frame):
    global shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    shutdown = True

# this setup is required for the DMA REST API connection. Note that the server name, port, username and password are just placeholders.
API_ENDPOINT = "http://flserver.rotman.utoronto.ca:16621"
USERNAME = "MONU-3"
PASSWORD = "D16409"
AUTHORIZATION = {'Authorization': 'Basic ' + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()}

shutdown = False

# this helper method handles rate-limiting to pause for the next cycle.
def handle_rate_limit(response):
    if response.status_code == 429:
        wait_time = float(response.headers.get('Retry-After', response.json().get('wait', 1)))
        print(f"Rate limit exceeded. Waiting for {wait_time} seconds before retrying.")
        sleep(wait_time)
        return True
    return False

# this helper method handles authorization failure.
def handle_auth_failure(response):
    if response.status_code == 401:
        print("Authentication failed. Please check your username and password.")
        global shutdown
        shutdown = True
        return True
    return False

# this helper method compiles possible API responses and handlers. 
def api_request(session, method, endpoint, params=None):
    while True:
        url = f"{API_ENDPOINT}/{endpoint}"
        if method == 'GET':
            resp = session.get(url, params=params)
        elif method == 'POST':
            resp = session.post(url, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        if handle_auth_failure(resp):
            return None
        if handle_rate_limit(resp):
            continue
        if resp.ok:
            return resp.json()
        raise ApiException(f"API request failed: {resp.text}")

# this helper method returns the current 'tick' of the running case
def get_tick(session):
    response = api_request(session, 'GET', 'case')
    return response['tick'] if response else None

def get_trader(session):
    resp = api_request(session, 'GET', 'trader')
    return resp

# this helper method returns the bid and ask for a given security
def ticker_bid_ask(session, ticker):
    response = api_request(session, 'GET', 'securities/book', params={'ticker': ticker})
    if response:
        return response['bids'][0]['price'], response['asks'][0]['price']
    return None, None

def place_order(session, ticker, order_type, quantity, action):
    api_request(session, 'POST', 'orders', 
                params={'ticker': ticker, 'type': order_type, 'quantity': quantity, 'action': action})

def main():
    with requests.Session() as s:
        s.headers.update(AUTHORIZATION)
        # tick = get_tick(s)
        trader = get_trader(s)
        # while tick > 5 and tick < 295 and not shutdown:
            
        print(trader)
            # IMPORTANT to update the tick at the end of the loop to check that the algorithm should still run or not
            # tick = get_tick(s)

if __name__ == '__main__':
    # register the custom signal handler for graceful shutdowns
    signal.signal(signal.SIGINT, signal_handler)
    main()