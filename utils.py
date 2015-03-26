__author__ = 'woolly_sammoth'

import hashlib
import requests
from binascii import unhexlify


class utils:

    def __init__(self, PlungeApp):
        self.PlungeApp = PlungeApp
        self. b58_digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

    class Base58Error(Exception):
        pass

    class InvalidBase58Error(Base58Error):
        pass

    def check_checksum(self, key):
        try:
            check_key = self.decode(key.strip().replace(' ', ''))
        except ValueError:
            return False
        checksum = check_key[-4:]
        hash = hashlib.sha256(hashlib.sha256(check_key[:-4]).digest()).digest()[:4]
        if hash == checksum:
            return True
        else:
            return False

    def decode(self, s):
        if not s:
            return b''
        # Convert the string to an integer
        n = 0
        for c in s:
            n *= 58
            if c not in self.b58_digits:
                raise self.InvalidBase58Error('Character %r is not a valid base58 character' % c)
            digit = self.b58_digits.index(c)
            n += digit
        # Convert the integer to bytes
        h = '%x' % n
        if len(h) % 2:
            h = '0' + h
        res = unhexlify(h.encode('utf8'))
        # Add padding back.
        pad = 0
        for c in s[:-1]:
            if c == self.b58_digits[0]: pad += 1
            else: break
        return b'\x00' * pad + res

    def get(self, url):
        # self.PlungeApp.logger.info("Request sent to %s" % url)
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != requests.codes.OK:
                return {'error': True, 'code': r.status_code, 'message': r.reason}
            return r.json()
        except requests.exceptions.Timeout:
            return {'error': True, 'code': 408, 'message': 'timeout'}
        except requests.exceptions.ConnectionError:
            return {'error': True, 'code': 500, 'message': 'connection refused'}

    def post(self, url, data={}):
        # self.PlungeApp.logger.info("Request sent to %s with data %s" % (url, str(data)))
        try:
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            r = requests.post(url, data=data, headers=headers, timeout=10)
            if r.status_code != requests.codes.OK:
                return {'error': True, 'code': r.status_code, 'message': r.reason}
            return r.json()
        except requests.exceptions.Timeout:
            return {'error': True, 'code': 408, 'message': 'timeout'}
        except requests.exceptions.ConnectionError:
            return {'error': True, 'code': 500, 'message': 'connection refused'}

    def get_active_exchanges(self):
        exchanges = []
        for exchange in self.PlungeApp.exchanges:
            if self.PlungeApp.config.getint('exchanges', exchange) > 0:
                exchanges.append(exchange)
        self.PlungeApp.logger.info("Got active exchanges - %s" % str(exchanges))
        return exchanges

    def get_active_currencies(self, exchange):
        currencies = []
        for currency in self.PlungeApp.currencies:
            if self.PlungeApp.config.getdefaultint(exchange, currency, 0) > 0:
                currencies.append(currency)
        self.PlungeApp.logger.info("Got active currencies - %s" % str(currencies))
        return currencies

    def get_currency_prices(self):
        prices = {}
        for currency in self.PlungeApp.currencies:
            price = self.get("http://%s:%s/price/%s" %
                             (self.PlungeApp.config.get('server', 'host'),
                              self.PlungeApp.config.get('server', 'port'), currency))
            price['currency'] = 0
            if 'price' in price:
                prices[currency] = price['price']
        self.PlungeApp.logger.info("Got active prices - %s" % str(prices))
        return prices