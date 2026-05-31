import json
import os
import tempfile
import datetime
from pathlib import Path

from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from shellarc_core.exception.structure_error import SA_AuthError, SA_ErrorCode

class AccessSpreadSheet:
    def __init__(self, 
                 spreadsheet_key: str
                 ) -> None:
        API_CONFIG_PATH = os.path.join(tempfile.gettempdir(), "api_config_secret.json")
        load_dotenv(verbose=True)
        project_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
        dotenv_path = project_ctx_dir / ".env"
        if not dotenv_path.exists():
            raise SA_AuthError(
                error_log=f"dotenv_path {dotenv_path} not exist",
                error_code=SA_ErrorCode.SA_9001
            )
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
            self.masterspreadsheet = gc_auth.open_by_key(SPREADSHEET_KEY)
        except Exception as e:
            self._spreadsheet = None
            raise SA_AuthError(
                error_log=f"Auth error in Firebase [{e}]",
                error_code=SA_ErrorCode.SA_9000
            )

    def spreadsheet_obj(self,
                        page_idx: int
                        ) -> gspread.Worksheet:
        ws = self.masterspreadsheet.get_worksheet(page_idx)
        return ws
    


