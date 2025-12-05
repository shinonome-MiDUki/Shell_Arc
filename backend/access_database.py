import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

class AccessDB:
    def __init__(self):
        gcp_secrets = st.secrets["firebase"]
        service_account_info = {
            "type": gcp_secrets["type"],
            "project_id": gcp_secrets["project_id"],
            "private_key_id": gcp_secrets["private_key_id"],
            "private_key": gcp_secrets["private_key"].replace('\\n', '\n'),
            "client_email": gcp_secrets["client_email"],
            "client_id": gcp_secrets["client_id"],
            "auth_uri": gcp_secrets["auth_uri"],
            "token_uri": gcp_secrets["token_uri"],
            "auth_provider_x509_cert_url": gcp_secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": gcp_secrets["client_x509_cert_url"],
            "universe_domain": gcp_secrets["universe_domain"]
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

