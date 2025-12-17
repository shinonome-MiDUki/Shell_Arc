import os

import firebase_admin
from firebase_admin import credentials, firestore

class AccessDB:
    def __init__(self):
        try:
            import streamlit as st
            firebase_secrets = st.secrets["firebase"]
            service_account_info = {
                "type": firebase_secrets["type"],
                "project_id": firebase_secrets["project_id"],
                "private_key_id": firebase_secrets["private_key_id"],
                "private_key": firebase_secrets["private_key"].replace('\\n', '\n'),
                "client_email": firebase_secrets["client_email"],
                "client_id": firebase_secrets["client_id"],
                "auth_uri": firebase_secrets["auth_uri"],
                "token_uri": firebase_secrets["token_uri"],
                "auth_provider_x509_cert_url": firebase_secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": firebase_secrets["client_x509_cert_url"],
                "universe_domain": firebase_secrets["universe_domain"]
            }
        except:
            from dotenv import load_dotenv
            load_dotenv(verbose=True)
            dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
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
        except:
            st.write("Database access error")

        self._database = firestore.client()

    @property
    def database(self):
        return self._database


