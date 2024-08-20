import pytest
import os
import yaml
from nornir import InitNornir
import logging
import shutil
from unittest.mock import patch
import nornir_inv
from main import InputValidate
from main import NornirCommands


# ----------------------------------------------------------------------------
# Directory that holds inventory files
# ----------------------------------------------------------------------------
test_directory = os.path.dirname(__file__)
test_inventory = os.path.join(test_directory, "test_inventory")
working_dir = os.path.join(test_directory, "test_files")
output_fldr = os.path.join(working_dir, "output")
input_file = os.path.join(working_dir, "input_cmd.yml")


# ----------------------------------------------------------------------------
# Fixture to initialise Nornir and load inventory
# ----------------------------------------------------------------------------
@pytest.fixture(scope="class")
def load_input_validate():
    global input_val
    input_val = InputValidate(test_directory)


# @pytest.fixture(scope="class")
# def load_nornir_inventory():
#     global input_data, nr_inv, nr_cmd
#     with open(os.path.join(input_fldr, "input_cmd.yml"), "r") as file_content:
#         input_data = yaml.load(file_content, Loader=yaml.FullLoader)
#     nr_inv = InitNornir(
#         inventory={
#             "plugin": "SimpleInventory",
#             "options": {
#                 "host_file": os.path.join(test_inventory, "hosts.yml"),
#                 "group_file": os.path.join(test_inventory, "groups.yml"),
#             },
#         }
#     )
#     nr_cmd = NornirCommands(nr_inv)
#     # creates a temp folder to save output files
#     if not os.path.exists(output_fldr):
#         os.mkdir(output_fldr)
#     yield output_fldr
#     if os.path.exists(output_fldr):
#         shutil.rmtree(output_fldr)


# ----------------------------------------------------------------------------
# 1. FILE_VAL: Testing of inventory settings validation
# ----------------------------------------------------------------------------
@pytest.mark.usefixtures("load_input_validate")
class TestInputValidate:

    # 1a. Testing method for checking input file exist check and loaded correctly
    def test_dir_exist_get_paths(self, capsys):
        # Test it creates a dict with print filename in it
        err_msg = "❌ dir_exist_get_paths: 'Print' input file variable creation failed"
        desired_result = None, None, input_file
        actual_result = input_val.dir_exist_get_paths("print", input_file)
        assert actual_result == desired_result, err_msg
        # Test if missing directory raises an error
        err_msg = "❌ dir_exist_get_paths: No working directory exist check failed"
        desired_result = f"❌ The 'pre' working directory {test_directory}/missing_working_dir does not exist"
        try:
            input_val.dir_exist_get_paths("pre", "missing_working_dir")
        except SystemExit:
            pass
        assert capsys.readouterr().out.replace("\n", "") == desired_result, err_msg
        # Test it creates a dict with working_dir, output_fldr and input_file
        err_msg = "❌ dir_exist_get_paths: Dict of working_dir and file path variable creation failed"
        desired_result = (working_dir, output_fldr, input_file)
        actual_result = input_val.dir_exist_get_paths("pre", "test_files")
        assert actual_result == desired_result, err_msg
        # Test it creates output directory
        err_msg = "❌ dir_exist_get_paths: Output folder creation failed"
        assert os.path.exists(output_fldr) == True, err_msg

    # 1b. Testing method for raising error if files missing (input or compare)
    def test_err_missing_files(self, capsys):
        err_msg = "❌ err_missing_files: Missing file raise error test failed"
        desired_result = f"❌ The 'cmp' file test_file1, test_file2 does not exist"
        try:
            input_val.err_missing_files("cmp", ["test_file1", "test_file2"])
        except SystemExit:
            pass
        assert capsys.readouterr().out.replace("\n", "") == desired_result, err_msg

    # 1c. Testing method for raising error if input file contents are not in the correct format
    def test_val_input_file(self, capsys):
        # Test for empty input file
        err_msg = "❌ val_input_file: Test raising error if input file is empty"
        desired_result = f"❌ The 'pos' input file {input_file} is empty"
        try:
            input_val.val_input_file("pos", input_file, None)
        except SystemExit:
            pass
        assert capsys.readouterr().out.replace("\n", "") == desired_result, err_msg
        # Test for input file without a hosts, groups or all dictionary
        err_msg = "❌ val_input_file: Test raising error if input file doesn't have one of hosts, groups or all dicts"
        desired_result = (
            f"❌ {input_file} must have at least one hosts, groups or all dictionary"
        )
        try:
            input_val.val_input_file("pos", input_file, {"hst": {}, "grp": {}, "a": {}})
        except SystemExit:
            pass
        assert capsys.readouterr().out.replace("\n", "") == desired_result, err_msg
        # Test for input file without hosts, groups or all holding a dictionary
        err_msg = "❌ val_input_file: Test raising error if input file doesn't have one of hosts, groups or all dicts"
        desired_result = (
            f"❌ {input_file} must have at least one hosts, groups or all dictionary"
        )
        try:
            input_val.val_input_file("pos", input_file, {"hosts": []})
        except SystemExit:
            pass
        assert capsys.readouterr().out.replace("\n", "") == desired_result, err_msg

    # 1d. Testing method for adding extra arguments to argparser
    def test_add_arg_parser(self):
        err_msg = "❌ add_arg_parser: Addition of extra argparse arguments failed"
        build_inv = nornir_inv.BuildInventory()
        tmp_args = input_val.add_arg_parser(build_inv)
        actual_result = vars(tmp_args.parse_args(["--print", "TEST"]))
        desired_result = {
            "compare": None,
            "detail_save": None,
            "username": None,
            "group": None,
            "hostname": None,
            "location": None,
            "logical": None,
            "post_test": None,
            "pre_test": None,
            "print": "TEST",
            "show": False,
            "show_detail": False,
            "type": None,
            # "validate": None,
            "version": None,
            "vital_save": None,
        }
        assert actual_result == desired_result, err_msg

    # 1e. Testing method for getting username and password
    @patch("getpass.getpass")
    def test_get_user_pass(self, getpass):
        getpass.return_value = "test_pass"
        err_msg = "❌ dir_get_user_pass: Test to get username and/or password failed"
        desired_result = dict(user="test_user", pword="test_pass")
        actual_result = input_val.get_user_pass(dict(username="test_user"))
        assert actual_result == desired_result, err_msg

    # 1f. Testing method for running script to validate with compare arg
    def test_val_compare_arg(self, capsys):
        # Test errors if compare files are missing
        err_msg = (
            "❌ dir_val_compare_arg: Test to error on missing compare files failed"
        )
        desired_result = f"❌ The 'cmp' file {os.path.join(working_dir, 'miss_cmp_file1')}, {os.path.join(working_dir, 'miss_cmp_file2')} does not exist"
        try:
            input_val.val_compare_arg(
                "cmp", ["test_files", "miss_cmp_file1", "miss_cmp_file2"]
            )
        except SystemExit:
            pass
        assert capsys.readouterr().out.replace("\n", "") == desired_result, err_msg
        # Test returns dict of compare full file path
        err_msg = "❌ dir_get_user_pass: Creation of compare file paths failed"
        desired_result = dict(
            cmp_file1=os.path.join(working_dir, "cmp_file1.txt"),
            cmp_file2=os.path.join(working_dir, "cmp_file2.txt"),
            output_fldr=output_fldr,
        )
        actual_result = input_val.val_compare_arg(
            "cmp", ["test_files", "cmp_file1.txt", "cmp_file2.txt"]
        )
        assert actual_result == desired_result, err_msg

    # 1g. Testing method for running script to validate with any arg other than compare
    def test_val_noncompare_arg(self, capsys):
        # Test errors if input file is missing
        err_msg = (
            "❌ dir_val_noncompare_arg: Test to error on missing input files failed"
        )
        desired_result = f"❌ The 'pre' file {os.path.join(test_directory, 'test_output/input_cmd.yml')} does not exist"
        try:
            input_val.val_noncompare_arg("pre", "test_output")
        except SystemExit:
            pass
        assert capsys.readouterr().out.replace("\n", "") == desired_result, err_msg
        # Test returns dict of compare full file path
        err_msg = "❌ dir_get_user_pass: Creation of input file paths and data failed"
        with open(os.path.join(working_dir, "input_cmd.yml"), "r") as file_content:
            input_data = yaml.load(file_content, Loader=yaml.FullLoader)
        desired_result = dict(
            input_data=input_data,
            input_file=os.path.join(working_dir, "input_cmd.yml"),
            output_fldr=output_fldr,
        )
        actual_result = input_val.val_noncompare_arg("pre", "test_files")
        assert actual_result == desired_result, err_msg


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
#             data=dict(input_data=input_data, output_fldr=output_fldr),
#             run_type="vital",
#         )
#         assert (
#             actual_result["TEST_HOST"][0].result.split("vital")[0] == desired_result
#         ), err_msg
