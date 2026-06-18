import os
import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

from ..keys.decoder import get_creds

class AccessDB:
    def __init__(self) -> None:
        service_account_info = get_creds(service="Firebase")
        cred = credentials.Certificate(service_account_info)
        try:
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            self._database = firestore.client()
        except Exception as e:
            print(f"Firestore access error, datetime : {datetime.datetime.now()}, error: {e}")
            self._database = None

    @property
    def database(self):
        return self._database


