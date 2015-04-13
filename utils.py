import json
import hashlib
from binascii import unhexlify

__author__ = 'woolly_sammoth'


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

    def get_active_exchanges(self):
        exchanges = []
        with open('api_keys.json') as api_keys_file:
            api_keys = json.load(api_keys_file)
        api_keys_file.close()
        for set in api_keys:
            exchange = set['exchange']
            if exchange in exchanges:
                continue
            else:
                exchanges.append(exchange)
        self.PlungeApp.logger.info("Got active exchanges - %s" % str(exchanges))
        return exchanges

    def get_active_currencies(self, exchange):
        currencies = self.PlungeApp.currencies
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