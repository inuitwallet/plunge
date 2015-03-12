__author__ = 'woolly_sammoth'

import hashlib
import requests
from binascii import unhexlify

b58_digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


class Base58Error(Exception):
    pass


class InvalidBase58Error(Base58Error):
    pass


def check_checksum(key):
    try:
        check_key = decode(key)
    except ValueError:
        return False
    checksum = check_key[-4:]
    hash = hashlib.sha256(hashlib.sha256(check_key[:-4]).digest()).digest()[:4]
    if hash == checksum:
        return True
    else:
        return False


def decode(s):
    if not s:
        return b''
    # Convert the string to an integer
    n = 0
    for c in s:
        n *= 58
        if c not in b58_digits:
            raise InvalidBase58Error('Character %r is not a valid base58 character' % c)
        digit = b58_digits.index(c)
        n += digit
    # Convert the integer to bytes
    h = '%x' % n
    if len(h) % 2:
        h = '0' + h
    res = unhexlify(h.encode('utf8'))
    # Add padding back.
    pad = 0
    for c in s[:-1]:
        if c == b58_digits[0]: pad += 1
        else: break
    return b'\x00' * pad + res


def get(url):
    r = requests.get(url)
    if r.status_code != requests.codes.OK:
        return {'error': True, 'code': r.status_code, 'message': r.reason}
    return r.json()