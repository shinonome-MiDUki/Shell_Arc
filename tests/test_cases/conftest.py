import pytest
import os
import json

def pytest_addoption(parser):
    parser.addoption(
        "--testcase",
        action="store",
        default="",
        help="set testcase json file"
    )

@pytest.fixture
def testcase(request):
    testcase_path = request.config.getoption("--testcase")
    if not os.path.exists(testcase_path):
        pytest.fail("testcase json path not specified")
    with open(testcase_path, "r", encoding="utf-8") as f:
        testcase = json.load(f)
    return testcase