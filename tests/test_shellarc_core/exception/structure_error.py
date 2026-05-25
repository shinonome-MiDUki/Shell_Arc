from datetime import datetime
from enum import Enum

from test_shellarc_core.exception.exceptions import SA_ExceptionType

class SA_ErrorCode(Enum):
    SA_4001 = "Cfg path not exist"
    SA_4002 = "Cfg request item key not exist"
    SA_4101 = "Spreadsheet map path not exist"
    SA_4102 = "Spreadsheet map unconfiged coord"
    SA_5001 = "DB unfound info"
    SA_5002 = "Non active index unspecified"
    SA_5003 = "Requsted status info dict not exist"
    SA_5004 = "Info range overflow"
    SA_5101 = "None file uploaded unexpectedly"
    SA_5201 = "Spreadsheet index is non natural num"
    SA_8000 = "Server local IO error"
    SA_8001 = "Communication error"
    SA_9000 = "Auth error"
        
class ShellArcErrorException(Exception):
    def __init__(self,
                 error_log: str,
                 error_type: SA_ExceptionType,
                 error_code: SA_ErrorCode,
                 is_fatal: bool
                 ):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_log = f"{now} : {error_type.value} - {error_code.name}({error_code.value}) - {error_log}"
        if is_fatal:
            error_log = "FATAL " + error_log
        super().__init__(error_log)
        self.frontend_msg = f"技術班にご連絡ください : {error_code.name}"

class SA_ProjStructError(ShellArcErrorException):
    def __init__(self, 
                 error_log: str, 
                 error_code: SA_ErrorCode
                 ):
        super().__init__(
            error_log=error_log, 
            error_type=SA_ExceptionType.STRUCT_ERROR, 
            error_code=error_code,
            is_fatal=True
            )
        
class SA_RequestItemError(ShellArcErrorException):
    def __init__(self, 
                 error_log: str, 
                 error_code: SA_ErrorCode
                 ):
        super().__init__(
            error_log=error_log, 
            error_type=SA_ExceptionType.SYS_REQUEST_ITEM_NOTEXIST, 
            error_code=error_code, 
            is_fatal=False
            )
        

class SA_CommunicationError(ShellArcErrorException):
    def __init__(self,
                 error_log: str, 
                 error_code: SA_ErrorCode
                 ):
        super().__init__(
            error_log=error_log, 
            error_type=SA_ExceptionType.COMMUN_ERROR,
            error_code=error_code, 
            is_fatal=True
            )

class SA_AuthError(ShellArcErrorException):
    def __init__(self, 
                 error_log: str, 
                 error_code: SA_ErrorCode
                 ):
        super().__init__(
            error_log=error_log, 
            error_type=SA_ExceptionType.AUTH_ERROR, 
            error_code=error_code, 
            is_fatal=True
            )
        
class SA_LocalIOError(ShellArcErrorException):
    def __init__(self, 
                 error_log, 
                 error_code
                 ):
        super().__init__(
            error_log=error_log, 
            error_type=SA_ExceptionType.LOCAL_IO_ERROR, 
            error_code=error_code, 
            is_fatal=True
            )