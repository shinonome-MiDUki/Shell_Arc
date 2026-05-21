import json
from pathlib import Path

import keyring
from cryptography.fernet import Fernet

def get_creds(
        service: str
        ) -> dict:
    token_file = Path(__file__).resolve().parent / "token.bin"

    with open(token_file, "rb") as f:
        token = f.read()

    key = keyring.get_password("shellarc", "shellarc")
    f = Fernet(key.encode("utf-8"))
    bin_json = f.decrypt(token)
    asc_json = bin_json.decode("utf-8")
    dict_json = json.loads(asc_json)

    return dict_json[service]
