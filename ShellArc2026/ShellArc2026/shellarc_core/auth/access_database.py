import os
import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

class AccessDB:
    def __init__(self):
        load_dotenv(verbose=True)
        dotenv_path = Path(dotenv_path).resolve().parents[3] / 'project_ctx/.env'
        load_dotenv(dotenv_path)
        service_account_info = {
            "type": os.environ.get("firebase_type"),
            "project_id": os.environ.get("firebase_project_id"),
            "private_key_id": os.environ.get("firebase_private_key_id"),
            "private_key": os.environ.get("firebase_private_key").replace('\\n', '\n'),
            "client_email": os.environ.get("firebase_client_email"),
            "client_id": os.environ.get("firebase_client_id"),
            "auth_uri": os.environ.get("firebase_auth_uri"),
            "token_uri": os.environ.get("firebase_token_uri"),
            "auth_provider_x509_cert_url": os.environ.get("firebase_auth_provider_x509_cert_url"),
            "client_x509_cert_url": os.environ.get("firebase_client_x509_cert_url"),
            "universe_domain": os.environ.get("firebase_universe_domain")   
        }
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


