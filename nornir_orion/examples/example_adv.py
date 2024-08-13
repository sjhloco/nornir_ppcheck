"""Example script to use nornir_orion as the inventory.
It NewProject method is used to add additional flags to those of orion_inv

To use:
-Create a directory for new project and copy nornir_orion into there
-Move this file into the new directories root
-Create a virtual environment and install pip requirements
-Run 'python example_adv.py' with any of the below flags, no flags just returns inventory

The optional runtime flags for the script:
-nu: Overrides the value set in npm.user
-du: Overrides the value set in device.user
-h: Filter the inventory based on the hostname
-g: Filter based on group (ios, iosxe, nxos, wlc, asa (includes ftd), checkpoint)
-l: Filter based on physical location (DC1, DC2, DCI (Overlay), ET, FG)
-ll: Filter based on physical location (WAN, WAN Edge, Core, Access, Services)
-t:Filter based on device type (firewall, router, dc_switch, switch, wifi_controller)
-v: Filter based on OS version (Cisco only)
-s: Prints all the hosts within the filtered inventory
-sd: Prints all the hosts within the filtered inventory including their host_vars
-f: Specifies name of the Yaml file containing ACL variables
-a: Applies changes to devices, by default only 'dry run'
"""


from nornir_orion import orion_inv

# ----------------------------------------------------------------------------
# ORION ON/OFF: Use to toggle off orion and use static inventory of inventory/hosts.yml and inventory/groups.yml
# ----------------------------------------------------------------------------
no_orion = True

# ----------------------------------------------------------------------------
# Class to add extra runtime flags (arguments) to nornir_orion flags
# ----------------------------------------------------------------------------
class NewProject:
    def __init__(self, orion):
        self.orion = orion

    def add_arg_parser(self):
        # Adds OrionInventory parser arguments
        args = self.orion.add_arg_parser()
        # Adds additional arguments to the OrionInventory parser arguments
        args.add_argument(
            "-f", "--filename", help="Name of the Yaml file containing ACL variables"
        )
        args.add_argument(
            "-a",
            "--apply",
            action="store_false",
            help="Apply changes to devices, by default only 'dry run'",
        )
        return args


# ----------------------------------------------------------------------------
# Engine that runs the methods from the script
# ----------------------------------------------------------------------------
def main(inv_settings: str, no_orion: bool = no_orion):
    orion = orion_inv.OrionInventory()
    my_project = NewProject(orion)
    inv_validate = orion_inv.LoadValInventorySettings()

    # 1. Gets info input by user by calling local method that calls remote method
    tmp_args = my_project.add_arg_parser()
    args = vars(tmp_args.parse_args())
    # 2. Load and validates the orion inventory settings, adds any runtime usernames
    inv_settings = inv_validate.load_inv_settings(args, inv_settings)
    # 3a. Tests username and password against orion
    if no_orion == False:
        orion.test_npm_creds(inv_settings["npm"])
        # 3b. Initialise Nornir inventory
        nr_inv = orion.load_inventory(inv_settings["npm"], inv_settings["groups"])
    # 3c. Uses static inventory instead of Orion
    elif no_orion == True:
        nr_inv = orion.load_static_inventory(
            "inventory/hosts.yml", "inventory/groups.yml"
        )
    # 4. Filter the inventory based on the runtime flags
    nr_inv = orion.filter_inventory(args, nr_inv)
    # 5. add username and password to defaults
    nr_inv = orion.inventory_defaults(nr_inv, inv_settings["device"])
    return nr_inv


if __name__ == "__main__":
    main("inv_settings.yml")
