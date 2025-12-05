import json
import os
import tempfile

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class AccessSpreadSheet:
    def __init__(self, spreadsheet_key):
        API_CONFIG_PATH = os.path.join(tempfile.gettempdir(), "api_config_secret.json")
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


