import hashlib
import typing

from cryptography.fernet import Fernet


class CryptographyManager:
    _fernet: Fernet
    _key: bytes
    _key_path: str = 'envs/cryptography.key'

    def __init__(self) -> None:
        self._key = self.get_key()
        self._fernet = Fernet(self._key)

    @classmethod
    def generate_key(cls) -> None:
        key = Fernet.generate_key()

        with open(cls._key_path, 'wb') as file:
            file.write(key)

    @classmethod
    def get_key(cls) -> bytes:
        with open(cls._key_path, 'rb') as file:
            return file.read()

    def encrypt(self, data: str) -> bytes:
        return self._fernet.encrypt(data.encode())

    def decrypt(self, data: bytes) -> bytes:
        return self._fernet.decrypt(data)

    def hash(self, data: typing.Union[str, int, bytes]) -> bytes:
        if isinstance(data, int):
            data = str(data)

        if isinstance(data, str):
            data = data.encode()

        return hashlib.pbkdf2_hmac(
            hash_name='sha256',
            password=data,
            salt=self._key,
            iterations=100_000,
            dklen=256,
        )


cryptography_manager = CryptographyManager()
