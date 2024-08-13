import pytest
import getpass
import os

from orion_inv import OrionInventory
from orion_inv import LoadValInventorySettings

# Directory that holds inventory files
test_inventory = os.path.join(os.path.dirname(__file__), "test_inventory")


# ----------------------------------------------------------------------------
# Fixture to initialise Nornir and load inventory
# ----------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def load_nornir_inventory():
    # rc: "Rich" = Console()
    global orion, nr_inv, inv_validate
    inv_validate = LoadValInventorySettings()
    orion = OrionInventory()
    nr_inv = orion.load_static_inventory(
        os.path.join(test_inventory, "hosts.yml"),
        os.path.join(test_inventory, "groups.yml"),
    )


# ----------------------------------------------------------------------------
# 1. FILE_VAL: Testing of inventory settings validation
# ----------------------------------------------------------------------------
class TestLoadValInventorySettings:

    # 1a. Testing printout error messages
    def test_print_error(self, capsys):
        err_msg = "❌ print_error: Print out of missing mandatory dictionaries failed"
        tmp_err = dict(
            server=None,
            user=None,
            ssl_verify=None,
            select=None,
            where=None,
            group=None,
            type=None,
            filter=None,
        )
        desired_result = "❌ GROUPS missing mandatory dictionaries: server, user, ssl_verify, select, \nwhere, group, type, filter\n"
        try:
            inv_validate.print_error(tmp_err, "GROUPS")
        except SystemExit:
            pass
        assert capsys.readouterr().out == desired_result, err_msg

        err_msg = "❌ print_error: Print out of dictionaries that are wrong type failed"
        tmp_err = dict(
            server="<class 'str'>",
            user="<class 'str'>",
            ssl_verify="<class 'bool'>",
            select="<class 'list'>",
            where="<class 'str'>",
            group="<class 'str'>",
            type="<class 'str'>",
            filter="<class 'list'>",
        )
        desired_result = (
            "❌ NPM dictionaries of wrong type: server should be a str, user should be a str,\n"
            "ssl_verify should be a bool, select should be a list, where should be a str, \ngroup "
            "should be a str, type should be a str, filter should be a list\n"
        )
        try:
            inv_validate.print_error(tmp_err, "NPM")
        except SystemExit:
            pass
        assert capsys.readouterr().out == desired_result, err_msg

    # 1b. Testing test method for validating inventory settings
    def test_testing_method(self):
        err_msg = "❌ testing_method: Validation of child dict presence and type failed"
        desired_result = {"server": None, "user": str}
        actual_result = inv_validate.testing_method(
            "npm", {"user": 1}, {"server": str, "user": str}
        )
        assert actual_result == desired_result, err_msg

    # 1c. Testing test engine for running testing_method and print_error
    def test_testing_engine(self, capsys):
        err_msg = "❌ testing_engine: Validation of mandatory parent dictionary presence or groups type list failed"
        desired_result = (
            "❌ NPM: Missing this mandatory parent dictionary\n"
            "❌ DEVICE: Missing this mandatory parent dictionary\n"
            "❌ GROUPS: This must be a list of groups\n"
        )
        try:
            inv_validate.testing_engine(dict(groups={}))
        except SystemExit:
            pass
        assert capsys.readouterr().out == desired_result, err_msg


# ----------------------------------------------------------------------------
# 2. FILTER: Checks filtering of Nornir inventory with runtime args
# ----------------------------------------------------------------------------
class TestFilterInventory:
    # 2a. Tests hostname filter one at a time
    def test_hostname_filter(self):
        args = dict(hostname="WAN ASA")
        desired_result = [
            "HME-ASR-WAN01",
            "DC-ASA-XNET01",
            "DC-ASR-WAN01",
            "AZ-ASR-WAN01",
            "AZ-ASA-VPN01",
        ]
        err_msg = f"❌ filter_inventory: '{list(args.keys())[0]}' runtime inventory filter failed"
        actual_result = []
        tmp_actual_result = orion.filter_inventory(args, nr_inv)
        for each_host in tmp_actual_result.inventory.hosts.keys():
            actual_result.append(each_host)
        assert actual_result == desired_result, err_msg

    # 2b. Tests group filter one at a time
    def test_group_filter(self):
        args = dict(group=["wlc", "nxos"])
        desired_result = ["HME-WLC-AIR01", "DC-N9K-SWI01"]
        err_msg = f"❌ filter_inventory: '{list(args.keys())[0]}' runtime inventory filter failed"
        actual_result = []
        tmp_actual_result = orion.filter_inventory(args, nr_inv)
        for each_host in tmp_actual_result.inventory.hosts.keys():
            actual_result.append(each_host)
        assert actual_result == desired_result, err_msg

    # 2c. Tests location filter one at a time
    def test_location_filter(self):
        args = dict(location=["AZ"])
        desired_result = [
            "AZ-ASR-WAN01",
            "AZ-FPR-FTD01",
            "AZ-ASA-VPN01",
            "AZ-UBT-SVR01",
        ]
        err_msg = f"❌ filter_inventory: '{list(args.keys())[0]}' runtime inventory filter failed"
        actual_result = []
        tmp_actual_result = orion.filter_inventory(args, nr_inv)
        for each_host in tmp_actual_result.inventory.hosts.keys():
            actual_result.append(each_host)
        assert actual_result == desired_result, err_msg

    # 2d. Tests logical filter one at a time
    def test_logical_filter(self):
        args = dict(logical=["Core", "Compute"])
        desired_result = [
            "HME-SWI-VSS01",
            "HME-UBT-SVR01",
            "DC-N9K-SWI01",
            "DC-UBT-SVR01",
            "AZ-UBT-SVR01",
        ]

        err_msg = f"❌ filter_inventory: '{list(args.keys())[0]}' runtime inventory filter failed"
        actual_result = []
        tmp_actual_result = orion.filter_inventory(args, nr_inv)
        for each_host in tmp_actual_result.inventory.hosts.keys():
            actual_result.append(each_host)
        assert actual_result == desired_result, err_msg

    # 2e. Tests type filter one at a time
    def test_type_filter(self):
        args = dict(type=["dc_switch"])
        desired_result = ["DC-N9K-SWI01"]
        err_msg = f"❌ filter_inventory: '{list(args.keys())[0]}' runtime inventory filter failed"
        actual_result = []
        tmp_actual_result = orion.filter_inventory(args, nr_inv)
        for each_host in tmp_actual_result.inventory.hosts.keys():
            actual_result.append(each_host)
        assert actual_result == desired_result, err_msg

    # 2f. Tests version filter one at a time
    def test_version_filter(self):
        args = dict(version="6.3.0")
        desired_result = ["AZ-FPR-FTD01"]
        err_msg = f"❌ filter_inventory: '{list(args.keys())[0]}' runtime inventory filter failed"
        actual_result = []
        tmp_actual_result = orion.filter_inventory(args, nr_inv)
        for each_host in tmp_actual_result.inventory.hosts.keys():
            actual_result.append(each_host)
        assert actual_result == desired_result, err_msg

    # 2g. Tests no filter one at a time
    def test_no_filter(self):
        args = dict(no_filter="")
        desired_result = [
            "HME-ASR-WAN01",
            "HME-SWI-VSS01",
            "HME-WLC-AIR01",
            "HME-SWI-ACC01",
            "HME-UBT-SVR01",
            "DC-ASR-XNET01",
            "DC-ASA-XNET01",
            "DC-ASR-WAN01",
            "DC-N9K-SWI01",
            "DC-9300-SWI01",
            "DC-UBT-SVR01",
            "AZ-ASR-WAN01",
            "AZ-FPR-FTD01",
            "AZ-ASA-VPN01",
            "AZ-UBT-SVR01",
        ]
        err_msg = f"❌ filter_inventory: '{list(args.keys())[0]}' runtime inventory filter failed"
        actual_result = []
        tmp_actual_result = orion.filter_inventory(args, nr_inv)
        for each_host in tmp_actual_result.inventory.hosts.keys():
            actual_result.append(each_host)
        assert actual_result == desired_result, err_msg

    # 2h. Tests all filters at the same time
    def test_all_filters(self):
        err_msg = "❌ filter_inventory: 'xxx' runtime inventory filter failed"
        args = dict(
            hostname="01",
            group=["ios", "iosxe"],
            location=["DC"],
            type=["router"],
            version="16.9.6",
        )
        actual_result: "Nornir" = orion.filter_inventory(args, nr_inv)
        assert (
            str(actual_result.inventory.hosts)
            == "{'DC-ASR-XNET01': Host: DC-ASR-XNET01}"
        ), err_msg

    ## 2i. Tests printed output
    def test_show_output(self, capsys):
        err_msg = "❌ filter_inventory: 'show' output of inventory filter failed"
        args = dict(filename="dummy_file", hostname="XNET", show=True)
        desired_result = (
            "=" * 70
            + "\n2 hosts have matched the filters 'XNET':\n-Host: DC-ASR-XNET01      "
            "-Hostname: 10.20.20.101\n-Host: DC-ASA-XNET01      -Hostname: 10.20.20.102\n"
        )

        try:
            orion.filter_inventory(args, nr_inv)
        except SystemExit:
            pass
        assert capsys.readouterr().out == desired_result, err_msg

    # 2j. Tests printed detailed output
    def test_show_detail_output(self, capsys):
        err_msg = "❌ filter_inventory: 'show_detail' output of inventory filter failed"
        args = dict(filename="dummy_file", hostname="AZ-ASA-VPN01", show_detail=True)
        desired_result = (
            "=" * 70
            + "\n1 hosts have matched the filters 'AZ-ASA-VPN01':\n-Host: AZ-ASA-VPN01   "
            "-   Hostname: 10.30.20.101, Groups: asa, \nInfra_Logical_Location: Services, "
            "MachineType: Cisco ASAv, IOSVersion: \n9.12(4)13, Infra_Location: AZ, type: firewall\n"
        )
        try:
            orion.filter_inventory(args, nr_inv)
        except SystemExit:
            pass
        assert capsys.readouterr().out == desired_result, err_msg


# ----------------------------------------------------------------------------
# 3. DEFAULTS: Checks adding username and password to Nornir inventory defaults
# ----------------------------------------------------------------------------
def test_inventory_defaults(monkeypatch):
    monkeypatch.setattr(getpass, "getpass", lambda x: "test_pword")
    nr_defaults: "Nornir" = orion.inventory_defaults(nr_inv, {"user": "test_user"})
    assert (
        nr_defaults.inventory.defaults.username == "test_user"
    ), "❌ inventory_defaults: Setting defaults username failed"
    assert (
        nr_defaults.inventory.defaults.password == "test_pword"
    ), "❌ inventory_defaults: Setting defaults password failed, check 'device_pword' is not set"
