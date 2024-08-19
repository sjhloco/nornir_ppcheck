import pytest
import os
import yaml
from nornir import InitNornir
import logging
import shutil

from . import orion_inv
from main import InputValidate
from main import NornirCommands


# ----------------------------------------------------------------------------
# Directory that holds inventory files
# ----------------------------------------------------------------------------
test_dir = os.path.dirname(__file__)
test_inventory = os.path.join(test_dir, "test_inventory")
input_dir = os.path.join(test_dir, "test_files")
output_dir = os.path.join(test_dir, "output")


# ----------------------------------------------------------------------------
# Fixture to initialise Nornir and load inventory
# ----------------------------------------------------------------------------
@pytest.fixture(scope="class")
def load_input_validate():
    global input_val
    input_val = InputValidate()


@pytest.fixture(scope="class")
def load_nornir_inventory():
    global input_data, nr_inv, nr_cmd
    with open(os.path.join(input_dir, "input_cmd.yml"), "r") as file_content:
        input_data = yaml.load(file_content, Loader=yaml.FullLoader)
    nr_inv = InitNornir(
        inventory={
            "plugin": "SimpleInventory",
            "options": {
                "host_file": os.path.join(test_inventory, "hosts.yml"),
                "group_file": os.path.join(test_inventory, "groups.yml"),
            },
        }
    )
    nr_cmd = NornirCommands(nr_inv)
    # creates a temp folder to save output files
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    yield output_dir
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)


# ----------------------------------------------------------------------------
# 1. FILE_VAL: Testing of inventory settings validation
# ----------------------------------------------------------------------------
@pytest.mark.usefixtures("load_input_validate")
class TestInputValidate:

    # 1a. Testing method for adding extra arguments to argparser
    def test_add_arg_parser(self):
        err_msg = "❌ add_arg_parser: Addition of extra argparse arguments failed"
        orion = orion_inv.OrionInventory()
        tmp_args = input_val.add_arg_parser(orion)
        actual_result = vars(tmp_args.parse_args(["--print", "TEST"]))
        desired_result = {
            "compare": None,
            "detail_save": None,
            "device_user": None,
            "group": None,
            "hostname": None,
            "location": None,
            "logical": None,
            "npm_user": None,
            "post_test": None,
            "pre_test": None,
            "print": "TEST",
            "show": False,
            "show_detail": False,
            "type": None,
            "validate": None,
            "version": None,
            "vital_save": None,
        }
        assert actual_result == desired_result, err_msg

    # 1b. Testing method for checking input file exist check and loaded correctly
    def test_dir_file_exist(self, capsys):
        err_msg = "❌ dir_file_exist: No input file exist check failed"
        desired_result = (
            "❌ The 'validate' input file test_path/test_file.yml does not exist\n"
        )
        try:
            input_val.dir_file_exist("validate", "test_path/test_file.yml", "test.yml")
        except SystemExit:
            pass
        assert capsys.readouterr().out == desired_result, err_msg

        err_msg = "❌ dir_file_exist: Input file load check failed"
        desired_result = {
            "input_data": {
                "all": {"cmd_print": ["show etherchannel summary"]},
                "groups": {"ios": {"cmd_print": ["show clock"]}},
                "hosts": {"HME-SWI-VSS01": {"cmd_print": ["show ip ospf neighbor"]}},
            },
            "input_file": "/Users/mucholoco/Documents/Coding/Nornir/code/nornir_checks/test/test_files/input_cmd.yml",
            "output_dir": None,
        }
        test_file = os.path.join(input_dir, "input_cmd.yml")
        actual_result = input_val.dir_file_exist("print", test_file, "test.yml")
        assert actual_result == desired_result, err_msg

    # 1c. Testing method for getting run_type flag and file path
    def test_get_run_type(self):
        args = {
            "compare": None,
            "detail_save": None,
            "device_user": None,
            "group": None,
            "hostname": None,
            "location": None,
            "logical": None,
            "npm_user": None,
            "post_test": None,
            "pre_test": "TEST_DIR",
            "print": None,
            "show": False,
            "show_detail": False,
            "type": None,
            "validate": None,
            "version": None,
            "vital_save": None,
        }
        err_msg = "❌ get_run_type: Get run_type flag failed"
        assert input_val.get_run_type(args) == ("pre_test", "TEST_DIR"), err_msg

    # 1d. Testing method for top-level (hosts, groups, all) input file format
    def test_val_input_file(self, capsys):
        err_msg = "❌ val_input_file: Empty input file check failed"
        desired_result = "❌ The 'print' input file test_path is empty\n"
        try:
            input_val.val_input_file("print", "test_path", None)
        except SystemExit:
            pass
        assert capsys.readouterr().out == desired_result, err_msg

        err_msg = "❌ val_input_file: Missing hosts/groups/all input file check failed"
        desired_result = (
            "❌ test_path must have at least one hosts, groups or all dictionary\n"
        )
        try:
            input_val.val_input_file("print", "test_path", {"host": {}})
        except SystemExit:
            pass
        assert capsys.readouterr().out == desired_result, err_msg

        err_msg = "❌ val_input_file: hosts/groups/all not dict input file check failed"
        desired_result = (
            "❌ test_path must have at least one hosts, groups or all dictionary\n"
        )
        try:
            input_val.val_input_file("print", "test_path", {"groups": []})
        except SystemExit:
            pass
        assert capsys.readouterr().out == desired_result, err_msg


# ----------------------------------------------------------------------------
# 2. NR_CMDs: Testing of Nornir interactions
# ----------------------------------------------------------------------------
# @pytest.mark.usefixtures("load_nornir_inventory")
# class TestNornirCommands:

#     # 2a Testing method for to getting list of print commands
#     def test_organise_cmds_print(self):
#         err_msg = "❌ organise_cmds: Creating a list of print commands failed"
#         desired_result = ["show history", "show hosts", "show run | in hostn"]
#         actual_result = nr_inv.run(
#             task=nr_cmd.organise_cmds, input_data=input_data, cmd_dict="cmd_print"
#         )
#         assert actual_result["TEST_HOST"].result == desired_result, err_msg

#     # 2b Testing method for to getting list of print commands
#     def test_organise_cmds_vital(self):
#         err_msg = "❌ organise_cmds: Creating a list of vital commands failed"
#         desired_result = ["show flash", "show vrf", "show arp"]
#         actual_result = nr_inv.run(
#             task=nr_cmd.organise_cmds, input_data=input_data, cmd_dict="cmd_vital"
#         )
#         assert actual_result["TEST_HOST"].result == desired_result, err_msg

#     # 2c Testing method for to getting list of print commands
#     def test_organise_cmds_detail(self):
#         err_msg = "❌ organise_cmds: Creating a list of detail commands failed"
#         desired_result = ["show history", "show run", "show boot"]
#         actual_result = nr_inv.run(
#             task=nr_cmd.organise_cmds, input_data=input_data, cmd_dict="cmd_detail"
#         )
#         assert actual_result["TEST_HOST"].result == desired_result, err_msg

#     # 2d Testing method for gathering command output to print to screen
#     def test_run_cmds_print(self):
#         err_msg = "❌ run_cmds: Nornir running 'print' commands failed"
#         desired_result = "hostname HME-C3560-SWI01"
#         actual_result = nr_inv.run(
#             name=f"{'print'.capitalize()} command output",
#             task=nr_cmd.run_cmds,
#             sev_level=logging.INFO,
#             data=dict(input_data=input_data),
#             run_type="print",
#         )
#         assert actual_result["TEST_HOST"][3].result == desired_result, err_msg

#     # 2e Testing method for gathering vital command output to save to file
#     def test_run_cmds_vital(self, capsys):
#         err_msg = "❌ run_cmds: Nornir running 'vital' commands failed"
#         desired_result = "✅ Created command output file '/Users/mucholoco/Documents/Coding/Nornir/code/nornir_checks/test/output/TEST_HOST_"
#         actual_result = nr_inv.run(
#             name=f"{'vital'.capitalize()} command output",
#             task=nr_cmd.run_cmds,
#             sev_level=logging.DEBUG,
#             data=dict(input_data=input_data, output_dir=output_dir),
#             run_type="vital",
#         )
#         assert (
#             actual_result["TEST_HOST"][0].result.split("vital")[0] == desired_result
#         ), err_msg
