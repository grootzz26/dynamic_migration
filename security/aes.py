import hashlib
import base64
import logging
from Crypto import Random
from Crypto.Cipher import AES
import gzip

IV = AES.block_size * '\x00'

BS = AES.block_size

pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[:-ord(s[len(s)-1:])]

# pad = lambda s: s + bytes([(BS - len(s) % BS)] * (BS - len(s) % BS))
def encrypt(key, plain_text, iv=None):
    breakpoint()
    try:
        if not iv:
            iv = IV
        iv = iv.encode("utf-8")
        breakpoint()
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        encrypted_text = encryptor.encrypt(pad(plain_text).encode("utf-8"))
        return base64.b64encode(encrypted_text).decode("utf-8")
    except Exception as e:
        print("Exception: while encrypt the data :%s",e)
        return None


def decrypt(key, plain_text, iv=None):
    try:
        if not iv:
            iv = IV
        iv = iv.encode("utf-8")
        plain_text = str(plain_text).replace('%2b','+').replace("%2B", "+")
        decryptor = AES.new(key, AES.MODE_CBC, iv)
        response = decryptor.decrypt(base64.b64decode(plain_text))
        return unpad(response)
    except Exception as e:
        print("Exception: while decrypt the data :%s",e)
        return None

def compressed_data(data):
    compressed_data = gzip.compress(data.encode('utf-8'))
    encoded_data = base64.b64encode(compressed_data).decode('utf-8')
    return encoded_data