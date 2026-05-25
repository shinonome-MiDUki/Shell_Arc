import pytest
import importlib
import sys
from pathlib import Path

from test_shellarc_core.exception.structure_error import (
    SA_ProjStructError, SA_RequestItemError, SA_AuthError,
    SA_CommunicationError, SA_LocalIOError
)
from test_shellarc_core.exception.user_exception import (
    SA_DataNotExist, SA_InvalidUserQuery, SA_InvalidRequestObj,
    SA_EditingRejection
)

def test_shellarc(testcase):
    test_id = testcase["id"]
    test_description = testcase["description"]

    test_module_path = testcase["testing_module"].split("/")
    module_path = test_module_path[0]
    module_class = test_module_path[1]
    module_func = test_module_path[2]
    test_module = importlib.import_module(module_path)
    TestModuleClass = getattr(test_module, module_class)

    instance_var = testcase.get("make_instance", {})
    instance_var = {k : v[0] for k, v in instance_var.items()}
    test_instance = TestModuleClass(**instance_var)

    test_func = getattr(TestModuleClass, module_func)
    func_var = testcase.get("input", {})
    func_var = {k : v[0] for k, v in func_var.items()}
    print(f"TESTING : {test_id}")
    print(f"EXPLAIN : {test_description}")
    print("********************")
    if testcase["expected_exception"] is None:
        assert test_func(test_instance, **func_var) == testcase["expected_output"]["value"]
    else:
        exception_class_name = testcase["expected_exception"]["exception_type"]
        exception_class = globals().get(exception_class_name)
        if exception_class is None:
            pytest.fail(f"expected error class {exception_class_name} not exist")
        with pytest.raises(exception_class) as e:
            test_func(test_instance, **func_var)
        
        assert e.value.frontend_msg == testcase["expected_exception"]["frontend_msg"]


"""
for f in /Users/shiinaayame/Documents/Shell_Arc_discordbot/tests/test_cases/reviewing_cases/*.json; do pytest /Users/shiinaayame/Documents/Shell_Arc_discordbot/tests/test_cases/tester.py -vv --testcase "$f"; done
for f in /Users/shiinaayame/Documents/Shell_Arc_discordbot/tests/test_cases/uploader_cases/*.json; do pytest /Users/shiinaayame/Documents/Shell_Arc_discordbot/tests/test_cases/tester.py -vv --testcase "$f"; done
for f in /Users/shiinaayame/Documents/Shell_Arc_discordbot/tests/test_cases/requesting_cases/*.json; do pytest /Users/shiinaayame/Documents/Shell_Arc_discordbot/tests/test_cases/tester.py -vv --testcase "$f"; done
"""