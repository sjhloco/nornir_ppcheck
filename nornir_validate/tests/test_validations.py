"""
These unittests test the different os_type command validations using desired_actual_cmd.py
which holds the desired_state, cmd_output and actual_state which have per-os_type child dictionaires
"""

import pytest
import os
import yaml

from nornir import InitNornir
from nornir.core.task import Result
from nornir.core.filter import F

from .test_data import desired_actual_cmd
from nr_val import merge_os_types
from nr_val import template_task
from nr_val import input_task
from nr_val import actual_state_engine

# ----------------------------------------------------------------------------
# Directory that holds inventory files and load ACL dict (show, delete, wcard, mask, prefix)
# ----------------------------------------------------------------------------
test_inventory = os.path.join(os.path.dirname(__file__), "test_inventory")
test_data = os.path.join(os.path.dirname(__file__), "test_data")
template_dir = os.path.join(os.getcwd(), "templates/")

# ----------------------------------------------------------------------------
# Fixture to initialise Nornir and load inventory
# ----------------------------------------------------------------------------
# Used for unittest of the core of nornir_validate (general operation)
@pytest.fixture(scope="session", autouse=True)
def load_inv_and_data():
    global nr, input_vars
    nr = InitNornir(
        inventory={
            "plugin": "SimpleInventory",
            "options": {
                "host_file": os.path.join(test_inventory, "hosts_validations.yml"),
                "group_file": os.path.join(test_inventory, "groups.yml"),
            },
        },
        logging={"enabled": False},
    )

    with open(
        os.path.join(test_data, "input_data_validations.yml"), "r"
    ) as file_content:
        input_vars = yaml.load(file_content, Loader=yaml.FullLoader)


# ----------------------------------------------------------------------------
# 1. DESIRED_STATE: Tests the templated input_vars (desired_state) are formatted correctly
# ----------------------------------------------------------------------------
class TestDesiredState:
    # GET: Used by input tests to get 'desired_state' host_var from the nornir host
    def get_desired_state_task(self, task, input_data):
        task.run(task=input_task, input_data=input_data, template_task=template_task)
        return Result(host=task.host, result=task.host["desired_state"])

    # 1a. IOS_DESIRED_STATE
    def test_ios_desired_state_templating(self):
        err_msg = (
            "❌ input_task: IOS templating of desired_state (host_var) is incorrect"
        )
        desired_output = desired_actual_cmd.desired_state["ios"]
        task_nr = nr.filter(F(has_parent_group="ios"))
        actual_output = task_nr.run(
            task=self.get_desired_state_task,
            input_data=input_vars,
        )
        assert actual_output["TEST_IOS"][0].result == desired_output, err_msg

    # 1b. NXOS_DESIRED_STATE
    def test_nxos_desired_state_templating(self):
        err_msg = (
            "❌ input_task: NXOS templating of desired_state (host_var) is incorrect"
        )
        desired_output = desired_actual_cmd.desired_state["nxos"]
        task_nr = nr.filter(F(has_parent_group="nxos"))
        actual_output = task_nr.run(
            task=self.get_desired_state_task,
            input_data=input_vars,
        )
        assert actual_output["TEST_NXOS"][0].result == desired_output, err_msg

    # 1c. ASA_DESIRED_STATE
    def test_asa_desired_state_templating(self):
        err_msg = (
            "❌ input_task: ASA templating of desired_state (host_var) is incorrect"
        )
        desired_output = desired_actual_cmd.desired_state["asa"]
        task_nr = nr.filter(F(has_parent_group="asa"))
        actual_output = task_nr.run(
            task=self.get_desired_state_task,
            input_data=input_vars,
        )
        assert actual_output["TEST_ASA"][0].result == desired_output, err_msg

    # # 1d. WLC_DESIRED_STATE
    # def test_wlc_desired_state_templating(self):
    #     err_msg = (
    #         "❌ input_task: WLC templating of desired_state (host_var) is incorrect"
    #     )
    #     desired_output = desired_actual_cmd.desired_state["wlc"]
    #     task_nr = nr.filter(F(has_parent_group="wlc"))
    #     actual_output = task_nr.run(
    #         task=self.get_desired_state_task,
    #         input_data=input_vars,
    #     )
    #     assert actual_output["TEST_WLC"][0].result == desired_output, err_msg

    # # 1e. CKP_DESIRED_STATE
    # def test_asa_desired_state_templating(self):
    #     err_msg = "❌ input_task: Checkpoint templating of desired_state (host_var) is incorrect"
    #     desired_output = desired_actual_cmd.desired_state["ckp"]
    #     task_nr = nr.filter(F(has_parent_group="checkpoint"))
    #     actual_output = task_nr.run(
    #         task=self.get_desired_state_task,
    #         input_data=input_vars,
    #     )
    #     assert actual_output["TEST_CKP"][0].result == desired_output, err_msg


# ----------------------------------------------------------------------------
# 2. ACTUAL_STATE: Per-os_type testing that actual state is formatting commands properly
# ----------------------------------------------------------------------------
class TestActualState:
    # 2a. IOS_ACTUAL_STATE
    def test_ios_actual_state_formatting(self):
        err_msg = "❌ actual_state: IOS/IOS-XE formatting of '{}' by actual_state.py is incorrect"
        os_type = merge_os_types(nr.inventory.hosts["TEST_IOS"])
        for cmd_output, desired_output in zip(
            desired_actual_cmd.cmd_output["ios"].items(),
            desired_actual_cmd.actual_state["ios"].items(),
        ):
            actual_output = actual_state_engine(os_type, {cmd_output[0]: cmd_output[1]})
            assert actual_output == {
                desired_output[0]: desired_output[1]
            }, err_msg.format(desired_output[0])

    # 2b. NXOS_ACTUAL_STATE
    def test_nxos_actual_state_formatting(self):
        err_msg = (
            "❌ actual_state: NXOS formatting of '{}' by actual_state.py is incorrect"
        )
        os_type = merge_os_types(nr.inventory.hosts["TEST_NXOS"])
        for cmd_output, desired_output in zip(
            desired_actual_cmd.cmd_output["nxos"].items(),
            desired_actual_cmd.actual_state["nxos"].items(),
        ):
            actual_output = actual_state_engine(os_type, {cmd_output[0]: cmd_output[1]})
            assert actual_output == {
                desired_output[0]: desired_output[1]
            }, err_msg.format(desired_output[0])

    # 2c. ASA_ACTUAL_STATE
    def test_asa_actual_state_formatting(self):
        err_msg = (
            "❌ actual_state: ASA formatting of '{}' by actual_state.py is incorrect"
        )
        os_type = merge_os_types(nr.inventory.hosts["TEST_ASA"])

        for cmd_output, desired_output in zip(
            desired_actual_cmd.cmd_output["asa"].items(),
            desired_actual_cmd.actual_state["asa"].items(),
        ):
            actual_output = actual_state_engine(os_type, {cmd_output[0]: cmd_output[1]})
            assert actual_output == {
                desired_output[0]: desired_output[1]
            }, err_msg.format(desired_output[0])

    # # 2d. WLC_ACTUAL_STATE
    # def test_wlc_actual_state_formatting(self):
    #     err_msg = (
    #         "❌ actual_state: WLC formatting of '{}' by actual_state.py is incorrect"
    #     )
    #     os_type = merge_os_types(nr.inventory.hosts["TEST_WLC"])
    #     for cmd_output, desired_output in zip(
    #         desired_actual_cmd.cmd_output["wlc"].items(),
    #         desired_actual_cmd.actual_state["wlc"].items(),
    #     ):
    #         actual_output = actual_state_engine(os_type, {cmd_output[0]: cmd_output[1]})
    #         assert actual_output == {
    #             desired_output[0]: desired_output[1]
    #         }, err_msg.format(desired_output[0])

    # # 2e. CKP_ACTUAL_STATE
    # def test_ckp_actual_state_formatting(self):
    #     err_msg = "❌ actual_state: Checkpoint formatting of '{}' by actual_state.py is incorrect"
    #     os_type = merge_os_types(nr.inventory.hosts["TEST_CKP"])
    #     for cmd_output, desired_output in zip(
    #         desired_actual_cmd.cmd_output["ckp"].items(),
    #         desired_actual_cmd.actual_state["ckp"].items(),
    #     ):
    #         actual_output = actual_state_engine(os_type, {cmd_output[0]: cmd_output[1]})
    #         assert actual_output == {
    #             desired_output[0]: desired_output[1]
    #         }, err_msg.format(desired_output[0])
