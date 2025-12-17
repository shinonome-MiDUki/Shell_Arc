import json
import os
import tempfile

import gspread
from oauth2client.service_account import ServiceAccountCredentials

class AccessSpreadSheet:
    def __init__(self, spreadsheet_key):
        API_CONFIG_PATH = os.path.join(tempfile.gettempdir(), "api_config_secret.json")
        try:
            import streamlit as st
            gcp_secrets = st.secrets["GCP"]
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
        except:
            from dotenv import load_dotenv
            load_dotenv(verbose=True)
            dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
            load_dotenv(dotenv_path)
            service_account_info = {
                "type": os.environ.get("GCP_type"),
                "project_id": os.environ.get("GCP_project_id"),
                "private_key_id": os.environ.get("GCP_private_key_id"),
                "private_key": os.environ.get("GCP_private_key").replace('\\n', '\n'),
                "client_email": os.environ.get("GCP_client_email"),
                "client_id": os.environ.get("GCP_client_id"),
                "auth_uri": os.environ.get("GCP_auth_uri"),
                "token_uri": os.environ.get("GCP_token_uri"),
                "auth_provider_x509_cert_url": os.environ.get("GCP_auth_provider_x509_cert_url"),
                "client_x509_cert_url": os.environ.get("GCP_client_x509_cert_url"),
                "universe_domain": os.environ.get("GCP_universe_domain")   
            }
        SCOPE = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        with open(API_CONFIG_PATH, mode="wt", encoding="utf-8") as f:
            json.dump(service_account_info, f, ensure_ascii=False)
        creds = ServiceAccountCredentials.from_json_keyfile_name(API_CONFIG_PATH, SCOPE)
        os.unlink(API_CONFIG_PATH)
        gc = gspread.authorize(creds)
        SPREADSHEET_KEY = str(spreadsheet_key)
        masterspreadsheet = gc.open_by_key(SPREADSHEET_KEY)
        spreadsheet_index = 0
        self._spreadsheet = masterspreadsheet.get_worksheet(spreadsheet_index)

    @property
    def spreadsheet_obj(self):
        return self._spreadsheet


