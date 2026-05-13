import json
import os
import tempfile
import datetime
from pathlib import Path

from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class AccessSpreadSheet:
    def __init__(self, 
                 spreadsheet_key: str
                 ) -> None:
        API_CONFIG_PATH = os.path.join(tempfile.gettempdir(), "api_config_secret.json")
        load_dotenv(verbose=True)
        dotenv_path = Path(dotenv_path).resolve().parents[3] / 'project_ctx/.env'
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
        SPREADSHEET_KEY = str(spreadsheet_key)
        try:
            gc_auth = gspread.authorize(creds)
            masterspreadsheet = gc_auth.open_by_key(SPREADSHEET_KEY)
            spreadsheet_index = 0
            self._spreadsheet = masterspreadsheet.get_worksheet(spreadsheet_index)
        except Exception as e:
            print(f"Spreadsheet access error, datetime : {datetime.datetime.now()}, error: {e}")
            self._spreadsheet = None

    @property
    def spreadsheet_obj(self):
        return self._spreadsheet


