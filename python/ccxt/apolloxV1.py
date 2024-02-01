import requests
import hmac
import hashlib
import time
from decimal import Decimal


class ApolloxV1:
    EXCHANGE_ID = 'apolloxv1'
    NETWORK_ID = 'bsc'
    BASE_URL = 'https://fapi.apollox.finance'

    def __init__(self, *args, **kwargs):
        self.api_key = kwargs['apiKey']
        self.api_secret = kwargs['secret']
        self.exchange_password = kwargs['password']
        self.markets = self.load_markets_raw()


    def __repr__(self):
        return f"<ApolloX(api_key={self.api_key}, api_secret={self.api_secret})>"


    def fetch_ticker(self, symbol, **kwargs):
        """
        Fetch all trading symbols from the exchange.

        Returns:
        - list: List of symbol dictionaries.
        :param **kwargs:
        """
        endpoint = '/fapi/v1/ticker/price'
        response = requests.get(self.BASE_URL + endpoint, params={'symbol': symbol})

        # Ensure the response is valid before returning the data
        response.raise_for_status()

        return response.json()


    def fetch_balances(self):
        """
        Fetch the futures account balance.

        Returns:
        - list: List of balance dictionaries.
        """

        endpoint = '/fapi/v2/balance'
        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'
        signature = hmac.new(bytes(self.api_secret, 'latin-1'), msg=bytes(query_string, 'latin-1'), digestmod=hashlib.sha256).hexdigest()

        params = {
            'timestamp': timestamp,
            'signature': signature
        }

        response = requests.get(self.BASE_URL + endpoint, headers=headers, params=params)

        # Ensure the response is valid before returning the data
        response.raise_for_status()

        return response.json()


    def change_leverage(self, symbol, leverage):
        headers = {
            "X-MBX-APIKEY": self.api_key
        }

        timestamp = int(time.time() * 1000)  # Timestamp in milliseconds

        data = {
            'symbol': symbol,
            'leverage': leverage,
            'timestamp': timestamp
        }

        # Generate signature
        data_str = '&'.join(f"{k}={v}" for k, v in data.items())
        signature = hmac.new(bytes(self.api_secret, 'latin-1'), msg=bytes(data_str, 'latin-1'), digestmod=hmac._hashlib.sha256).hexdigest()
        data['signature'] = signature

        response = requests.post(self.BASE_URL + '/fapi/v1/leverage', headers=headers, params=data)

        return response.json()


    def cancel_order(self, id, symbol=None) -> dict:
        # Ensure either id or symbol is provided
        if not (id or symbol):
            raise ValueError("Either orderId or symbol must be provided.")

        data = {
            'timestamp': int(time.time() * 1000)  # current timestamp in milliseconds
        }

        if id:
            data['orderId'] = id
        if symbol:
            data['symbol'] = symbol

        # Generate signature
        data_str = '&'.join(f"{k}={v}" for k, v in data.items())
        signature = hmac.new(bytes(self.api_secret, 'latin-1'), msg=bytes(data_str, 'latin-1'), digestmod=hmac._hashlib.sha256).hexdigest()
        data['signature'] = signature

        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        response = requests.delete(self.BASE_URL + '/fapi/v1/order', headers=headers, params=data)

        # Handle response here, and potentially raise exceptions on errors
        data = response.json()

        response.raise_for_status()

        # Return the order status
        return data


    def create_order(self, symbol, side, amount, price=None, **params):
        '''
        :param symbol: market symbol to deploy on
        :param side: trade direction
        :param amount: units are in USDT, $10 == 10.00, etc
        :param price: when specified, creates limit order
        :param params: include extra options, such as leverage
        :return:
        '''
        headers = {
            "X-MBX-APIKEY": self.api_key
        }

        if not params.get('leverage'):
            params['leverage'] = 1.0

        print(self.change_leverage(symbol, leverage=params['leverage']))

        timestamp = int(time.time() * 1000)  # Timestamp in milliseconds
        data = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': amount,
            'timestamp': timestamp,
            'leverage': params['leverage']
        }
        if price:
            data['type'] = 'LIMIT'
            data['price'] = str(price)
            data['timeInForce'] = 'GTC'

        # Generate signature
        data_str = '&'.join(f"{k}={v}" for k, v in data.items())
        signature = hmac.new(bytes(self.api_secret, 'latin-1'), msg=bytes(data_str, 'latin-1'), digestmod=hmac._hashlib.sha256).hexdigest()
        data['signature'] = signature

        response = requests.post(self.BASE_URL + '/fapi/v1/order', headers=headers, params=data)

        response.raise_for_status()

        return response.json()


    def load_markets(self):
        """
        Fetch all trading symbols from the exchange.

        Returns:
        - list: List of symbol dictionaries.
        """
        endpoint = '/fapi/v1/exchangeInfo'
        response = requests.get(self.BASE_URL + endpoint)

        # Ensure the response is valid before returning the data
        response.raise_for_status()

        symbols_info = response.json()
        symbols = symbols_info.get('symbols')
        new_symbols_list = []
        if symbols:
            for s in symbols:
                new_symbols_list.append(s['symbol'])

        return new_symbols_list


    def fetch_order(self, id=None, symbol=None) -> dict:
        # Ensure either id or symbol is provided
        if not (id or symbol):
            raise ValueError("Either orderId or symbol must be provided.")

        data = {
            'timestamp': int(time.time() * 1000)  # current timestamp in milliseconds
        }

        if id:
            data['orderId'] = id
        if symbol:
            data['symbol'] = symbol

        # Generate signature
        data_str = '&'.join(f"{k}={v}" for k, v in data.items())
        signature = hmac.new(bytes(self.api_secret, 'latin-1'), msg=bytes(data_str, 'latin-1'), digestmod=hmac._hashlib.sha256).hexdigest()
        data['signature'] = signature

        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        response = requests.get(self.BASE_URL + '/fapi/v1/order', headers=headers, params=data)

        # Handle response here, and potentially raise exceptions on errors
        data = response.json()

        response.raise_for_status()

        # Return the order status
        return data


    def fetch_trades(self, symbol):
        headers = {
            "X-MBX-APIKEY": self.api_key
        }

        timestamp = int(time.time() * 1000)  # Timestamp in milliseconds

        data = {
            'symbol': symbol,
            'timestamp': timestamp
        }

        # Generate signature
        data_str = '&'.join(f"{k}={v}" for k, v in data.items())
        signature = hmac.new(bytes(self.api_secret, 'latin-1'), msg=bytes(data_str, 'latin-1'), digestmod=hmac._hashlib.sha256).hexdigest()

        data['signature'] = signature

        response = requests.get(self.BASE_URL + '/fapi/v1/userTrades', headers=headers, params=data)

        response.raise_for_status()

        return response.json()


    def fetch_positions(self, symbols=None):
        """
        Fetch all opened positions from the exchange for a specific symbol or all symbols.

        Parameters:
        - symbol (str, optional): The specific trading pair symbol (e.g., 'BTCUSDT').

        Returns:
        - list: List of opened position dictionaries.
        """
        endpoint = '/fapi/v2/positionRisk'

        # Prepare the headers for the authenticated request
        timestamp = int(time.time() * 1000)
        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        # Prepare the signature for the request
        query_string = f'timestamp={timestamp}'
        # if symbols:
        #     query_string += f'&symbol={symbols}'

        signature = hmac.new(bytes(self.api_secret, 'latin-1'), msg=bytes(query_string, 'latin-1'), digestmod=hashlib.sha256).hexdigest()

        # Append the signature to the endpoint
        url = self.BASE_URL + endpoint + '?' + query_string + '&signature=' + signature

        # Make the GET request
        response = requests.get(url, headers=headers)

        # Ensure the response is valid before returning the data
        response.raise_for_status()

        construct_positions_list = []
        if not symbols:
            construct_positions_list = response.json()
        else:
            # filter through symbols args
            for p in response.json():
                for s in symbols:
                    position_amount = p.get('positionAmt')
                    try:
                        position_amount = Decimal(str(position_amount))
                    except Exception as e:
                        raise Exception(e)
                    if p.get('symbol') == s and position_amount:
                        construct_positions_list.append(p)

        # Return the list of opened positions
        return construct_positions_list


    def load_markets_raw(self):
        """
        Fetch all trading symbols from the exchange.

        Returns:
        - list: List of symbol dictionaries.
        """
        endpoint = '/fapi/v1/exchangeInfo'
        response = requests.get(self.BASE_URL + endpoint)

        # Ensure the response is valid before returning the data
        response.raise_for_status()

        symbols_info = response.json()
        return symbols_info.get('symbols')


    def fetch_order_book(self, symbol, limit=5):
        """
        Fetch the order book depth for a specific symbol.

        Parameters:
        - symbol (str): The trading pair symbol.
        - limit (int, optional): Number of levels in the order book. Default is 5.

        Returns:
        - dict: Order book depth with 'bids' and 'asks'.
        """

        endpoint = '/fapi/v1/depth'
        params = {
            'symbol': symbol,
            'limit': limit
        }

        response = requests.get(self.BASE_URL + endpoint, params=params)

        # Ensure the response is valid before returning the data
        response.raise_for_status()

        return response.json()


    def fetch_all_orders(self, symbol, id=None, startTime=None, endTime=None, limit=500):
        """
        Fetch all account orders: active, canceled, or filled.

        Parameters:
        - symbol (str): Symbol to fetch orders for.
        - orderId (int, optional): Get orders >= that orderId. Defaults to None.
        - startTime (int, optional): Start time in ms. Defaults to None.
        - endTime (int, optional): End time in ms. Defaults to None.
        - limit (int, optional): Max number of orders to return. Defaults to 500.

        Returns:
        - list: List of order dictionaries.
        """

        endpoint = '/fapi/v1/allOrders'
        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        timestamp = int(time.time() * 1000)
        query_string = f'symbol={symbol}&timestamp={timestamp}'

        if id:
            query_string += f'&orderId={id}'
        if startTime:
            query_string += f'&startTime={startTime}'
        if endTime:
            query_string += f'&endTime={endTime}'
        if limit:
            query_string += f'&limit={limit}'

        signature = hmac.new(bytes(self.api_secret, 'latin-1'), msg=bytes(query_string, 'latin-1'), digestmod=hashlib.sha256).hexdigest()

        params = {
            'symbol': symbol,
            'timestamp': timestamp,
            'signature': signature
        }
        if id:
            params['orderId'] = id
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        if limit:
            params['limit'] = limit

        response = requests.get(self.BASE_URL + endpoint, headers=headers, params=params)

        # Ensure the response is valid before returning the data
        response.raise_for_status()

        return response.json()


    def fetch_all_open_orders(self, symbol=None):
        """
        Fetch all open orders.

        Parameters:
        - symbol (str, optional): Symbol to fetch orders for. If not provided, fetches for all symbols.

        Returns:
        - list: List of open order dictionaries.
        """

        endpoint = '/fapi/v1/openOrders'
        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'
        if symbol:
            query_string += f'&symbol={symbol}'

        signature = hmac.new(bytes(self.api_secret, 'latin-1'), msg=bytes(query_string, 'latin-1'), digestmod=hashlib.sha256).hexdigest()

        params = {
            'timestamp': timestamp,
            'signature': signature
        }
        if symbol:
            params['symbol'] = symbol

        response = requests.get(self.BASE_URL + endpoint, headers=headers, params=params)

        # Ensure the response is valid before returning the data
        response.raise_for_status()

        return response.json()


class_names = [name for name, obj in locals().items() if isinstance(obj, type)]
__all__ = class_names