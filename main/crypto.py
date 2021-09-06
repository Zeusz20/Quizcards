from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64decode
from decouple import config
from os.path import isfile


class Crypto:
    RSA_KEY = config('RSA_KEY')

    def __init__(self, size):
        passphrase = config('RSA_PASSPHRASE')

        # generate keypair if doesn't exist
        if not isfile(Crypto.RSA_KEY):
            keypair = RSA.generate(size)
            with open(Crypto.RSA_KEY, 'wb') as file:
                key = keypair.export_key(passphrase=passphrase)
                file.write(key)

        self.keypair = RSA.import_key(open(Crypto.RSA_KEY).read(), passphrase=passphrase)

    def decrypt(self, encrypted_text):
        encrypted_text = b64decode(encrypted_text)
        cipher = PKCS1_v1_5.new(self.keypair)
        size = self.keypair.size_in_bits() // 8
        sentinel = Random.new().read(size)
        plaintext = cipher.decrypt(encrypted_text, sentinel)
        return plaintext.decode()

    def public_key(self):
        return self.keypair.public_key().export_key().decode()


crypto = Crypto(2048)
