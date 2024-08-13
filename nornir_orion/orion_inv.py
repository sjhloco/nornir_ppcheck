from typing import Any, Dict, List
import argparse
import sys
import getpass
import yaml
import os

from rich.console import Console
from rich.theme import Theme

from orionsdk import SwisClient
from requests import HTTPError, ConnectionError
from requests.packages import urllib3

from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir import InitNornir
from nornir.core.filter import F
from nornir_rich.functions import print_inventory

# Needed so can find inventory plugin when is import into another script
sys.path.insert(0, "nornir_orion")
from plugins.inventory.orion_npm import OrionNpmInventory

# ----------------------------------------------------------------------------
# ORION ON/OFF: Use to toggle off orion and use static inventory of inventory/hosts.yml and inventory/groups.yml
# ----------------------------------------------------------------------------
no_orion = False


# ----------------------------------------------------------------------------
# LOAD_SETTINGS: Loads the inventory settings and tests that non are missing and formatted correctly
# ----------------------------------------------------------------------------
class LoadValInventorySettings:
    def __init__(self):
        self.rc = Console()
        self.error = False

    # ----------------------------------------------------------------------------
    # 1. LOAD_INV: Loads the inventory and runs test methods
    # ----------------------------------------------------------------------------
    def load_inv_settings(self, args: Dict[str, Any], filename: str) -> Dict[str, Any]:
        with open(filename) as f:
            inv_settings = yaml.load(f, Loader=yaml.SafeLoader)

        # If npm or device username set in env vars or at runtime adds them to the inventory settings
        if os.environ.get("NPM_SERVER") != None:
            inv_settings["npm"]["server"] = os.environ["NPM_SERVER"]

        if args.get("npm_user") != None:
            inv_settings["npm"]["user"] = args["npm_user"]
        elif os.environ.get("NPM_USERNAME") != None:
            inv_settings["npm"]["user"] = os.environ["NPM_USERNAME"]
        if os.environ.get("NPM_PASSWORD") != None:
            inv_settings["npm"]["pword"] = os.environ["NPM_PASSWORD"]

        if args.get("device_user") != None:
            inv_settings["device"]["user"] = args["device_user"]
        elif os.environ.get("DEVICE_USERNAME") != None:
            inv_settings["device"]["user"] = os.environ["DEVICE_USERNAME"]
        if os.environ.get("DEVICE_PASSWORD") != None:
            inv_settings["device"]["pword"] = os.environ["DEVICE_PASSWORD"]

        # Run test engine, exit or continue based on test engine result
        self.testing_engine(inv_settings)
        if self.error == True:
            sys.exit(1)
        else:
            return inv_settings

    # ----------------------------------------------------------------------------
    # 2. ENGINE: Test engine failsfast if missing parent or runs further test methods
    # ----------------------------------------------------------------------------
    def testing_engine(self, inv_settings) -> None:
        test_input = dict(
            npm=dict(server=str, user=str, ssl_verify=bool, select=list, where=str),
            device=dict(user=str),
            groups=dict(group=str, type=str, filter=list),
        )

        for setting_type in ["npm", "device", "groups"]:
            # 2a. If parent dictionary doesn't exist failfast
            if inv_settings.get(setting_type) == None:
                self.error = True
                self.rc.print(
                    f":x: {setting_type.upper()}: Missing this mandatory parent dictionary"
                )
            # 2b. If the parent dictionaries exist test child dictionaries:
            else:
                # If Groups iterate through list of groups calling test method to test group child dictionaries
                if setting_type == "groups":
                    if not isinstance(inv_settings[setting_type], list):
                        self.error = True
                        self.rc.print(
                            f":x: {setting_type.upper()}: This must be a list of groups"
                        )
                        tmp_err = []
                    else:
                        for each_grp in inv_settings[setting_type]:
                            grp_name = each_grp.get("group", "unknown")
                            tmp_err = self.testing_method(
                                f"groups {grp_name}",
                                each_grp,
                                test_input[setting_type],
                            )
                # If NPM or device call test method to test each child dictionary
                elif setting_type != "groups":
                    tmp_err = self.testing_method(
                        setting_type,
                        inv_settings[setting_type],
                        test_input[setting_type],
                    )
                # 2c. If errors run print method
                if len(tmp_err) != 0:
                    self.print_error(tmp_err, setting_type.upper())

    # ----------------------------------------------------------------------------
    # 3. TESTING: Checks contents to make sure exist and are correct type
    # ----------------------------------------------------------------------------
    def testing_method(
        self, setting_type: str, settings: Dict[str, Any], test_input: Dict[str, Any]
    ) -> None:
        tmp_err: dict = {}
        # 3a. Loop through the name of the child dictionary and expected type
        for attr_name, attr_type in test_input.items():
            # 3b. Make sure child dictionary exists and is of the right type
            if settings.get(attr_name) == None:
                self.error = True
                tmp_err[attr_name] = None
            elif settings.get(attr_name) != None:
                if not isinstance(settings[attr_name], attr_type):
                    self.error = True
                    tmp_err[attr_name] = attr_type
        return tmp_err

    # ----------------------------------------------------------------------------
    # 4. PRINT_ERR: Prints error message if any settings errors
    # ----------------------------------------------------------------------------
    def print_error(self, tmp_err: Dict[str, Any], dict_type: str) -> str:
        tmp_missing, tmp_wrong = ([] for i in range(2))

        # 4a. Group up missing child dictionaries or wrong setting type
        for attr_name, attr_err in tmp_err.items():
            if attr_err == None:
                tmp_missing.append(attr_name)
            else:
                attr_err = str(attr_err).split("'")[1]
                tmp_wrong.append(f"[i]{attr_name}[/i] should be a {attr_err}")
        # 4b. Print error messages
        if len(tmp_missing) != 0:
            missing = ", ".join(tmp_missing)
            self.rc.print(
                f":x: {dict_type} missing mandatory dictionaries: [i]{missing}[/i]"
            )
        if len(tmp_wrong) != 0:
            wrong = ", ".join(tmp_wrong)
            self.rc.print(f":x: {dict_type} dictionaries of wrong type: {wrong}")


# ----------------------------------------------------------------------------
# BUILD_INV: Builds the Nornir inventory from Orion NPM devices
# ----------------------------------------------------------------------------
class OrionInventory:
    def __init__(self):
        my_theme = {"repr.ipv4": "none", "repr.number": "none", "repr.call": "none"}
        self.rc = Console(theme=Theme(my_theme))

    # ----------------------------------------------------------------------------
    # 1. FLAGS: Optional runtime flags to filter inventory and overide usernames
    # ----------------------------------------------------------------------------
    def add_arg_parser(self) -> Dict[str, Any]:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-nu", "--npm_user", help="NPM username, overides hardcoded script variable"
        )
        parser.add_argument(
            "-du",
            "--device_user",
            help="Device username, overides hardcoded script variable",
        )
        parser.add_argument(
            "-n",
            "--hostname",
            help="Hosts that contain any of this string in their name",
        )
        parser.add_argument(
            "-g",
            "--group",
            nargs="+",
            help="Hosts in any of these groups (ios, iosxe, nxos, wlc, asa)",
        )
        parser.add_argument(
            "-l",
            "--location",
            nargs="+",
            help="Hosts in any of these locations (DC1, DC2, ET, FG)",
        )
        parser.add_argument(
            "-ll",
            "--logical",
            nargs="+",
            help="Hosts in any of these locical locations (WAN, WAN Edge, Core, Access, Services)",
        )
        parser.add_argument(
            "-t",
            "--type",
            nargs="+",
            help="Hosts in any of these device types (firewall, router, dc_switch, switch, wifi_controller)",
        )
        parser.add_argument(
            "-v",
            "--version",
            help="Hosts that contain any of this string in their software version",
        )
        parser.add_argument(
            "-s",
            "--show",
            action="store_true",
            help="Prints the inventory hosts matched by the filters",
        )
        parser.add_argument(
            "-sd",
            "--show_detail",
            action="store_true",
            help="Prints the inventory hosts matched by the filters including all their attributes",
        )
        return parser

    # ----------------------------------------------------------------------------
    # 2. NPM: Checks the NPM username and password are valid with a dummy object lookup
    # ----------------------------------------------------------------------------
    def test_npm_creds(self, npm: Dict[str, Any]) -> str:
        if npm.get("pword") == None:
            npm["pword"] = getpass.getpass("Enter npm password: ")
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            conn = SwisClient(npm["server"], npm["user"], npm["pword"])
            conn.query(
                "SELECT Status FROM IPAM.IPNode WHERE IPAddress = "
                + "'"
                + "169.254.1.1"
                + "'"
            )
            return npm["pword"]
        except ConnectionError as err:
            self.rc.print(
                f":x: [red]ConnectionError[/red]: Cannot connect to server [i b]{npm['server']}"
                "[/i b], ensure that the address is correct and it is reachable"
            )
            self.rc.print(err)
            sys.exit(1)
        except HTTPError as err:
            self.rc.print(
                f":x: [red]HTTPError[/red]: Cannot connect to [i b]{npm['server']}[/i b] "
                f"with username [i b]{npm['user']}[/i b], check username/password are correct"
            )
            self.rc.print(err)
            sys.exit(1)
        except Exception as err:
            self.rc.print(
                f":x: [red]Error[/red]: Cannot connect to [i b]{npm['server']}[/i b]"
                f"with [i b]{npm['user']}[/i b]"
            )
            self.rc.print(err)
            sys.exit(1)

    # ----------------------------------------------------------------------------
    # 3. LOAD_INV: Creates the inventory using Orion
    # ----------------------------------------------------------------------------
    def load_inventory(
        self, npm: Dict[str, Any], groups: List[Dict[str, Any]]
    ) -> "Nornir":
        InventoryPluginRegister.register("orion_npm", OrionNpmInventory)
        nr: "Nornir" = InitNornir(
            inventory=(
                dict(
                    plugin="orion_npm",
                    options=dict(
                        npm_server=npm["server"],
                        npm_user=npm["user"],
                        npm_pword=npm["pword"],
                        npm_select=npm["select"],
                        npm_where=npm["where"],
                        ssl_verify=npm["ssl_verify"],
                        all_groups=groups,
                    ),
                )
            )
        )

        return nr

    # TEST_LOAD_INV: Creates inventory from static files, used by pytest and to test with no orion
    def load_static_inventory(self, hosts: str, groups: str) -> "Nornir":
        nr: "Nornir" = InitNornir(
            inventory={
                "plugin": "SimpleInventory",
                "options": {"host_file": hosts, "group_file": groups},
            }
        )
        return nr

    # ----------------------------------------------------------------------------
    # 4 FILTER_INV: Filters the host in the inventory  based on any arguments passed
    # ----------------------------------------------------------------------------
    def filter_inventory(self, args: Dict[str, Any], nr: "Nornir") -> "Nornir":
        filters = []
        if args.get("hostname") != None:
            list_hosts = args["hostname"].split()
            for n in range(10 - len(list_hosts)):
                list_hosts.append("DUMMY")
            nr = nr.filter(
                F(name__contains=list_hosts[0])
                | F(name__contains=list_hosts[1])
                | F(name__contains=list_hosts[2])
                | F(name__contains=list_hosts[3])
                | F(name__contains=list_hosts[4])
                | F(name__contains=list_hosts[5])
                | F(name__contains=list_hosts[6])
                | F(name__contains=list_hosts[7])
                | F(name__contains=list_hosts[8])
                | F(name__contains=list_hosts[9])
            )
            filters.append(args["hostname"])
        if args.get("group") != None:
            nr = nr.filter(F(groups__any=args["group"]))
            filters.extend(args["group"])
        if args.get("location") != None:
            nr = nr.filter(F(Infra_Location__any=args["location"]))
            filters.extend(args["location"])
        if args.get("logical") != None:
            nr = nr.filter(F(Infra_Logical_Location__any=args["logical"]))
            filters.extend(args["logical"])
        if args.get("type") != None:
            nr = nr.filter(F(type__any=args["type"]))
            filters.extend(args["type"])
        if args.get("version") != None:
            nr = nr.filter(F(IOSVersion__contains=args["version"]))
            filters.append(args["version"])

        # Print and exit if show or show_detail flags set
        num_hosts = len(nr.inventory.hosts.items())
        if args.get("show", False) == True:
            self.rc.print("[blue]=[/blue]" * 70)
            self.rc.print(
                f"[i cyan]{num_hosts}[/i cyan] hosts have matched the filters [i cyan]'{', '.join(filters)}'[/i cyan]:"
            )
            for each_host, data in nr.inventory.hosts.items():
                self.rc.print(
                    f"[green]-Host: {each_host}[/green]\t[red]=[/red]  Hostname: {data.hostname}"
                )
            sys.exit(0)
        elif args.get("show_detail", False) == True:
            self.rc.print("[blue]=[/blue]" * 70)
            self.rc.print(
                f"[i cyan]{num_hosts}[/i cyan] hosts have matched the filters [i cyan]'{', '.join(filters)}'[/i cyan]:"
            )
            print_inventory(nr)
            sys.exit(0)
        else:
            return nr

    # ----------------------------------------------------------------------------
    # 4. DEFAULT_INV: Adds username and password to defaults of the inventory (all devices)
    # ----------------------------------------------------------------------------
    def inventory_defaults(self, nr: "Nornir", device: Dict[str, Any]) -> "Nornir":
        if device.get("pword") == None:
            device["pword"] = getpass.getpass("Enter device password: ")
        nr.inventory.defaults.username = device["user"]
        nr.inventory.defaults.password = device["pword"]

        return nr


# ----------------------------------------------------------------------------
# Engine that runs the methods from the script
# ----------------------------------------------------------------------------
def main(inv_settings: str, no_orion: bool = no_orion):
    # 1. Gets info input by user and stores in dictionary
    orion = OrionInventory()
    tmp_args = orion.add_arg_parser()
    args = vars(tmp_args.parse_args())

    # 2. Load and validates the orion inventory settings, adds any runtime usernames
    inv_validate = LoadValInventorySettings()
    inv_settings = inv_validate.load_inv_settings(args, inv_settings)

    # 3a. Tests username and password against orion
    if no_orion == False:
        orion.test_npm_creds(inv_settings["npm"])
        # 3b. Initialise Nornir inventory
        nr_inv = orion.load_inventory(inv_settings["npm"], inv_settings["groups"])
    # 3c. Uses static inventory instead of Orion (first checks locally, if not exist uses nornir_orion static inv)
    elif no_orion == True:
        if os.path.exists("inventory"):
            nr_inv = orion.load_static_inventory(
                "inventory/hosts.yml", "inventory/groups.yml"
            )
        else:
            nr_inv = orion.load_static_inventory(
                "nornir_orion/inventory/hosts.yml", "nornir_orion/inventory/groups.yml"
            )

    # 4. Filter the inventory based on the runtime flags
    nr_inv = orion.filter_inventory(args, nr_inv)
    # 5. add username and password to defaults
    nr_inv = orion.inventory_defaults(nr_inv, inv_settings["device"])

    return nr_inv


if __name__ == "__main__":
    main("inv_settings.yml")
