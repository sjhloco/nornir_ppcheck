"""
These unittests test the operation of nornir_validate (nr_val.py), they do not intensively test each validation.
Use test_validations.py to test the different os_type command validations (desired_state, cmd_output, actual_state)
"""

import pytest
import os
import yaml
from datetime import datetime
import json

from nornir import InitNornir
from nornir.core.task import Result

from nr_val import merge_os_types
from nr_val import template_task
from nr_val import input_task
from nr_val import actual_state_engine
from compliance_report import report
from compliance_report import report_file

# ----------------------------------------------------------------------------
# Directory that holds inventory files and load ACL dict (show, delete, wcard, mask, prefix)
# ----------------------------------------------------------------------------
test_inventory = os.path.join(os.path.dirname(__file__), "test_inventory")
test_data = os.path.join(os.path.dirname(__file__), "test_data")
template_dir = os.path.join(os.getcwd(), "templates/")

# ----------------------------------------------------------------------------
# Fixture to initialise Nornir and load inventory
# ----------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def load_inv_and_data():
    global nr, input_vars
    nr = InitNornir(
        inventory={
            "plugin": "SimpleInventory",
            "options": {
                "host_file": os.path.join(test_inventory, "hosts.yml"),
                "group_file": os.path.join(test_inventory, "groups.yml"),
            },
        },
        logging={"enabled": False},
    )
    with open(os.path.join(test_data, "input_data.yml"), "r") as file_content:
        input_vars = yaml.load(file_content, Loader=yaml.FullLoader)


# ----------------------------------------------------------------------------
# Tests all the methods within nornir_validate.py
# ----------------------------------------------------------------------------
@pytest.mark.usefixtures("load_inv_and_data")
class TestNornirValidate:

    # OS_TYPE: Checks merging of nornir platforms (device types)
    def test_merge_os_types(self):
        err_msg = "❌ merge_os_types: Merging of Nornir platforms failed"
        desired_output = ["cisco_ios", "cisco_iosxe", "ios"]
        actual_output = merge_os_types(nr.inventory.hosts["TEST_HOST"])
        assert actual_output == desired_output, err_msg

    # 1. TEMPLATE: Checks nornir-template rendered data is converted into a dictionary of commands
    def test_template_task(self):
        err_msg = "❌ template_task: Individual Nornir template task failed"
        desired_output = {}
        actual_output = {
            "show ip ospf neighbor": {
                "_mode": "strict",
                "192.168.255.1": {"state": "FULL"},
                "2.2.2.2": {"state": "FULL"},
            }
        }
        nr.run(
            task=template_task,
            tmpl_path=template_dir,
            input_vars=input_vars["hosts"]["TEST_HOST"],
            desired_state=desired_output,
        )
        assert actual_output == desired_output, err_msg

    # 2a. INPUT: Used by input tests to get host_var info
    def input_task_nr_task(self, task, input_data):
        task.run(task=input_task, input_data=input_data, template_task=template_task)
        return Result(host=task.host, result=task.host["desired_state"])

    # 2b. INPUT_FILE: Tests templated input_vars is assigned as a host_var (is testing templates from input file)
    def test_input_task_file(self):
        err_msg = (
            "❌ input_task: Input task to create desired_state host_var from file failed"
        )
        desired_output = {
            "show ip ospf neighbor": {
                "_mode": "strict",
                "192.168.255.1": {"state": "FULL"},
                "2.2.2.2": {"state": "FULL"},
            }
        }
        actual_output = nr.run(
            task=self.input_task_nr_task,
            input_data=os.path.join(test_data, "input_data.yml"),
        )
        assert actual_output["TEST_HOST"][0].result == desired_output, err_msg

    # 2c. INPUT_VAR: Tests templated input_vars is assigned as a group_var (is testing templates from input var)
    def test_input_task_var(self):
        err_msg = "❌ input_task: Input task to create desired_state group_var from variable failed"
        desired_output = {
            "show ip ospf neighbor": {
                "_mode": "strict",
                "192.168.255.1": {"state": "FULL"},
                "2.2.2.2": {"state": "FULL"},
            }
        }
        input_data = {
            "groups": {"ios": {"ospf_nbr": {"nbrs": ["192.168.255.1", "2.2.2.2"]}}}
        }
        actual_output = nr.run(
            task=self.input_task_nr_task,
            input_data=input_data,
        )
        assert actual_output["TEST_HOST"][0].result == desired_output, err_msg

    # 2d. INPUT_FILE: Tests empty input_data is caught and an nornir exception raised
    def test_input_task_file_err(self):
        err_msg = "❌ input_task: Input task to catch bad input file (no hosts, groups or all) failed"
        desired_output = "⚠️  No validations were performed as no desired_state was generated, check input file and template"
        actual_output = nr.run(
            task=self.input_task_nr_task,
            input_data=os.path.join(test_data, "bad_input_data.yml"),
        )
        assert actual_output.failed == True
        assert actual_output["TEST_HOST"][1].result == desired_output

    # 3. ACTUAL_STATE: Tests that empty command outputs are picked up on
    def test_actual_state_engine(self):
        err_msg = "❌ actual_state_engine: Task to catch empty command output failed"
        actual_output = actual_state_engine(["ios"], {"show ip ospf neighbor": None})
        assert actual_output == {"show ip ospf neighbor": {}}, err_msg

    # 4. VALIDATE: Decided not worth testing this as out of it is is only sending cmds that is not already tested
    def test_validate_task(self):
        pass


# ----------------------------------------------------------------------------
# Tests all the methods within nornir_validate.py
# ----------------------------------------------------------------------------
class TestComplianceReport:

    # 5a. COMPL_REPORT: Tests compliance report pass and ignoring empty outputs
    def test_report(self):
        state = {
            "show ip ospf neighbor": {"192.168.255.1": {"state": "FULL"}},
            "show version": None,
        }
        desired_output = {
            "failed": False,
            "result": "✅ Validation report complies, desired_state and actual_state match.",
            "report": {
                "complies": True,
                "show ip ospf neighbor": {
                    "complies": True,
                    "present": {"192.168.255.1": {"complies": True, "nested": True}},
                    "missing": [],
                    "extra": [],
                },
                "skipped": [],
            },
            "report_text": "",
        }
        actual_output = report(state, state, "TEST_HOST", None)
        assert (
            actual_output == desired_output
        ), "❌ compliance_report: Report for a compliance of true failed"

    # 5b. COMPL_REPORT_MULTI_CMD: Tests compliance report fail when combining the compliance from multiple commands
    def test_report_multi_cmd(self):
        desired_state = {
            "show ip ospf neighbor": {
                "_mode": "strict",
                "192.168.255.1": {"state": "FULL"},
            },
            "show etherchannel summary": {
                "Po3": {
                    "members": {"Gi0/15": {"mbr_status": "P"}},
                    "protocol": "LACP",
                    "status": "U",
                }
            },
        }
        actual_state = {
            "show ip ospf neighbor": {
                "192.168.255.1": {"state": "FULL"},
                "2.2.2.2": {"state": "FULL"},
            },
            "show etherchannel summary": {
                "Po3": {
                    "members": {"Gi0/15": {"mbr_status": "P"}},
                    "protocol": "LACP",
                    "status": "U",
                }
            },
        }
        actual_output = report(desired_state, actual_state, "TEST_HOST", None)
        desired_output = {
            "failed": True,
            "result": {
                "show ip ospf neighbor": {
                    "complies": False,
                    "present": {"192.168.255.1": {"complies": True, "nested": True}},
                    "missing": [],
                    "extra": ["2.2.2.2"],
                },
                "show etherchannel summary": {
                    "complies": True,
                    "present": {"Po3": {"complies": True, "nested": True}},
                    "missing": [],
                    "extra": [],
                },
                "complies": False,
                "skipped": [],
            },
            "report": {
                "complies": False,
                "show ip ospf neighbor": {
                    "complies": False,
                    "present": {"192.168.255.1": {"complies": True, "nested": True}},
                    "missing": [],
                    "extra": ["2.2.2.2"],
                },
                "show etherchannel summary": {
                    "complies": True,
                    "present": {"Po3": {"complies": True, "nested": True}},
                    "missing": [],
                    "extra": [],
                },
                "complies": False,
                "skipped": [],
            },
            "report_text": "",
        }
        assert (
            actual_output == desired_output
        ), "❌ compliance_report: Combining report of comply true and false failed"

    # 6a. REPORT_FILE: Test saving a report to file, validate the contents
    def test_report_file(self):
        report = {
            "show ip ospf neighbor": {
                "complies": True,
                "present": {"192.168.255.1": {"complies": True, "nested": True}},
                "missing": [],
                "extra": [],
            }
        }
        report_file("TEST_HOST", test_data, report, True, [])
        filename = os.path.join(
            test_data,
            "TEST_HOST"
            + "_compliance_report_"
            + datetime.now().strftime("%Y%m%d-%H%M")
            + ".json",
        )
        assert (
            os.path.exists(filename) == True
        ), "❌ report_file: Creation of saved report failed"
        os.remove(filename)

    # 6b. REPORT_FILE_CONTENT: Validate the contents of report file
    def test_report_file_content(self):
        desired_output = {
            "complies": True,
            "skipped": [],
            "show ip ospf neighbor": {
                "complies": True,
                "present": {"192.168.255.1": {"complies": True, "nested": True}},
                "missing": [],
                "extra": [],
            },
        }
        report = {
            "show ip ospf neighbor": {
                "complies": True,
                "present": {"192.168.255.1": {"complies": True, "nested": True}},
                "missing": [],
                "extra": [],
            }
        }
        report_file("TEST_HOST", test_data, report, True, [])
        filename = os.path.join(
            test_data,
            "TEST_HOST"
            + "_compliance_report_"
            + datetime.now().strftime("%Y%m%d-%H%M")
            + ".json",
        )
        with open(filename, "r") as file_content:
            report_from_file = json.load(file_content)
        assert (
            report_from_file == desired_output
        ), "❌ report_file: Saved report contents are incorrect"
        os.remove(filename)

    # 6c. REPORT_FILE: Updating existing file and compliance state
    def test_report_file_update(self):
        report = {
            "show ip ospf neighbor": {
                "complies": True,
                "present": {"192.168.255.1": {"complies": True, "nested": True}},
                "missing": [],
                "extra": [],
            }
        }
        report_file("TEST_HOST", test_data, report, True, [])
        report = {
            "show etherchannel summary": {
                "complies": False,
                "present": {"Po3": {"complies": True, "nested": True}},
                "missing": [],
                "extra": [],
            }
        }
        report_file("TEST_HOST", test_data, report, False, [])
        filename = os.path.join(
            test_data,
            "TEST_HOST"
            + "_compliance_report_"
            + datetime.now().strftime("%Y%m%d-%H%M")
            + ".json",
        )
        desired_output = {
            "complies": False,
            "skipped": [],
            "show ip ospf neighbor": {
                "complies": True,
                "present": {"192.168.255.1": {"complies": True, "nested": True}},
                "missing": [],
                "extra": [],
            },
            "show etherchannel summary": {
                "complies": False,
                "present": {"Po3": {"complies": True, "nested": True}},
                "missing": [],
                "extra": [],
            },
        }
        with open(filename, "r") as file_content:
            report_from_file = json.load(file_content)
        assert (
            report_from_file == desired_output
        ), "❌ report_file: Extending report and updating compliance failed"
        os.remove(filename)
