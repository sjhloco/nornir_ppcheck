"""Example script to use nornir_orion as the inventory. To use:
-Create a directory for new project and copy nornir_orion into there
-Move this file into the new directories root
-Create a virtual environment and install pip requirements
-Run 'python example_basic.py' with any of the below flags, no flags just returns inventory

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
"""

from nornir_orion import orion_inv

# Run using Orion as the inventory
nr = orion_inv.main("inv_settings.yml")

# Run using static inventory files (sets no_orion to True)
# nr = orion_inv.main("inv_settings.yml", True)
