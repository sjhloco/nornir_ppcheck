
# Orion NPM Nornir Inventory

Uses the ***orionsdk*** python package to build a nornir inventory from Solarwinds Orion NPM.

- Gathers NPM devices filtering them based on SQL query logic (*FROM* and *WHERE*)
- NPM device attributes (*SELECT*) are stored in the nornir data dictionary as host_vars
- Based on NPM *MachineType* creates OS-type nornir *groups* with their associated nornir *platform*
- Provides customisable SQL query (*WHERE*) and device attribute collection (*SELECT*)
- The nornir inventory can be filtered at runtime using flags (arguments)

## SolarWinds Query Language (SWQL)

[SWQL](https://user-images.githubusercontent.com/33333983/119037187-8eb88100-b9a9-11eb-9417-106d21eb7591.gif) is a proprietary, read-only subset of SQL used by the inventory plugin to query the SolarWinds database for device information. It uses standard SQL query logic of ***SELECT … FROM … WHERE …*** with *SELECT* and *WHERE* set in the inventory settings (*npm.select* and *npm.where*) and *FROM* being an arbitrary value.

- **FROM:** Set to *'Orion.Nodes'* so SELECT attributes *'Caption'*, *'IPAddress'* and *'MachineType'* are always usable
- **SELECT:** An optional list of the device attributes to pull from Orion and add as host data dictionaries. *Caption*, *IPAddress* and *MachineType* are explicit options set in the background with *Caption* used as the nornir inventory host, *IPAddress* the hostname and *MachineType* defining group membership. Can SELECT based any pre-defined [schema](http://solarwinds.github.io/OrionSDK/schema/index.html) or custom property (must start with *Nodes.CustomProperties*)
- **WHERE:** A mandatory string used to filter the Nodes returned by the query. The string can contain multiple conditional elements, for example *"Vendor = 'Cisco' and Nodes.Status = 1"* matches all up Cisco devices

## Inventory settings

The inventory settings comprises of three parent dictionaries (***npm***, ***groups***, ***device***) holding the Orion and network device credentials as well as the SWQL parameters that filter the database.

| Parent | Variable | Type | Description |
| --- | -------- | -----| ----------- |
| npm | `server` | `string` | IP of the Orion NPM server, can be overridden with env var
| npm | `user` | `string` | Username for orion, can be overridden with env var or at runtime
| npm | `ssl_verify` | `boolean` | Disables CA certificate validation warnings
| npm | `select` | `list` | Device attributes added to the nornir inventory (can be empty list)
| npm | `where` | `string` | Filter to define which Orion nodes to gather attributes from
| groups | n/a | `list` | List of groups and filters that decide the group membership
| device | `user` | `string` | Nornir inventory device usernames, can be overridden with env var or at runtime

The default inventory settings file (*inv_settings.yml*) has the following SWQL values and resulting logic.

**Filter (WHERE):** Gather device attributes for Cisco and Checkpoint devices (*Vendor*) that are up (*1*).

```yaml
npm:
  where: (Vendor = 'Cisco' or Vendor ='Check Point Software Technologies Ltd') and Nodes.Status = 1
```

**Attributes (SELECT):** From each device gather the explicit attributes of *Caption*, *IPAddress* and *MachineType* (don't need specifying) as well as *IOSversion* (Cisco only) and custom attributes *Infra_Location* and *Infra_Logical_Location*.

```yaml
npm:
  select:
    - Nodes.CustomProperties.Infra_Logical_Location
    - IOSVersion
    - Nodes.CustomProperties.Infra_Location
```

**Groups:** Nornir groups are created using the *groups* list of dictionaries with group membership based around the device attribute *MachineTypes*.

- *Group*: Name of the group
- *type*: Host data dict to represent the device type for this group (router, switch, etc), replaces MachineType
- *filter*: A list of upto two filter objects (and logic) to match against SELECT MachineTypes to dictate group membership. If doesn't match on MachineTypes it will tray against Caption (name), if still no match adds to the group *unknown*
- *scrapli*: Optional 3rd party connection driver added to connection_options (platform)
- *netmiko*: Optional  3rd party connection driver added to connection_options (platform)
- *napalm*: Optional  3rd party connection driver added to connection_options (platform)

This will create the groups *ios*, *iosxe*, *nxos*, *wlc*, *asa*, *wlc*, *palo* and *checkpoint* with a *type* host_var and the *platform* set for any connection drivers defined.

```yaml
groups:
  - group: ios
    type: switch
    filter: [Catalyst, C9500]
    naplam: ios
    netmiko: cisco_ios
    scrapli: cisco_iosxe
  - group: iosxe
    type: router
    filter: [ASR, CSR]
    naplam: ios
    netmiko: cisco_iosxe
    scrapli: cisco_iosxe
  - group: nxos
    type: dc_switch
    filter: [Nexus]
    naplam: nxos_ssh
    netmiko: cisco_nxos_ssh
    scrapli: cisco_nxos
  - group: sdwan
    type: router
    # Matches on name as machine type is just Cisco (typical!!!!)
    filter: [SDW]
    naplam: ios
    netmiko: cisco_xe
    scrapli: cisco_iosxe
  - group: wlc
    type: wifi_controller
    filter: [WLC]
    netmiko: cisco_wlc_ssh
  - group: asa
    type: firewall
    filter: [ASA]
    netmiko: cisco_asa_ssh,
  - group: checkpoint
    type: firewall
    filter: [Checkpoint]
    netmiko: checkpoint_gaia_ssh
  - group: palo
    type: firewall
    filter: [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
    netmiko: paloalto_panos
 ```

## Installation and Prerequisites

Create your project, clone *nornir_orion* to its root and install the dependencies (*nornir*, *orionsdk*, *rich* etc).

```python
mkdir my_new_project
cd my_new_project
git clone https://github.com/sjhloco/nornir_orion.git
python -m venv ~/venv/new_project
source ~/venv/new_project/bin/activate
pip install -r nornir_orion/requirements.txt
```

## Environment Variables

The Orion NPM and device credentials can be set via environment variables rather than at runtime.

- `NPM_SERVER`
- `NPM_USERNAME`
- `NPM_PASSWORD`
- `DEVICE_USERNAME`
- `DEVICE_PASSWORD`

The below table shows how to add a temporary environment variable, they only last until the terminal session is closed.

| OS | Show all environment variables | Add an environment variables |
|----| ----------------- | -------------- |
| Mac | `printenv` | `export variable_name=variable_value` |
| Windows cmd | `set` | `set variable_name=variable_value` |
| Windows powershell | `ls env:` | `$env:variable_name = "variable_value"` |

## Using the Inventory

To use the inventory it needs importing and the *main* function called with the inventory settings. This will return the initialized nornir inventory ready to use.

```python
from nornir_orion import orion_inv

nr = orion_inv.main("inv_settings.yml")
```

It is possible to add a 2nd argument of *True* to the *main* function to force it to use static inventory instead of Orion. It looks for *hosts.yml* and *groups.yml* in */inventory*, if */inventory* doesn't exists it uses the files from */nornir_orion/inventory*.

```python
nr = orion_inv.main("inv_settings.yml", True)
```

### Runtime flags

The *npm* and *device* usernames specified in the inventory settings (*inv_settings.yml*) or environment variables can be overridden at runtime.

| flag           | Description |
| -------------- | ----------- |
| `-nu` or `--npm_user` | Overrides the value set by *NPM_USERNAME* and/or *npm.user* |
| `-du` or `--device_user` | Overrides the value set by *DEVICE_USERNAME* and/or *device.user* |

Runtime filters (flags) can be used in any combination to filter the inventory hosts that the tasks will be run against. Filters are sequential so the ordering is of importance. For example, a 2nd filter will only be run against hosts that have already matched the 1st filter. Words separate by special characters or whitespace need to be encased in brackets.

| filter            | method   | Options |
| ------------------| -------- | ------- |
| `-n` or `--hostname`  | contains | * (uses OR logic with upto 10 host names encased in "" separated by space |
| `-g` or `--group`     | any      | ios, iosxe, nxos, wlc, asa (includes ftd), checkpoint |
| `-l` or `--location`  | any      | Values got from *Nodes.CustomProperties.Infra_Location* |
| `-ll` or `--logical`  | any      | Values got from *Nodes.CustomProperties.Infra_Logical_Location* |
| `-t`  or `--type`     | any      | firewall, router, dc_switch, switch, wifi_controller |
| `-v`  or `--version`  | contains | * |

The *show* and *show_detail* flags can be used to help with the forming of filters by displaying what hosts the filtered inventory holds. If either of these are defined no actual inventory object is returned, so it prints the inventory and exits.

| flag | Description |
| ---- | ----------- |
| `-s` or `--show` | Prints all the hosts within the inventory |
| `-sd` or `--show_detail` | Prints all the hosts within the inventory including their host_vars |

All hosts in the groups *ios*\
`python example_basic.py -s -g ios`

All hosts in groups *ios* or *iosxe* that have *WAN* in their name\
`python example_basic.py -s -g ios iosxe -n WAN`

All hosts (including host_vars) in group *ios* running version *16.9.6* at locations *DC* or *AZ*\
`python example_basic.py -sd -g iosxe -v "16.9.6" -l DC AZ`

![run_example_basic](https://user-images.githubusercontent.com/33333983/145107911-951922f0-3c5c-4cb7-a32b-046c74d215df.gif)

### Adding additional flags to the Inventory

This other example (*example_adv.py*) takes it one step further and adds additional runtime flags to those used by *nornir_orion*. The new class (*NewProject*) gathers the arguments (flags) from *OrionInventory.add_arg_parser* and adds its own additional arguments (*filename* and *apply*).

```python
from nornir_orion import orion_inv

no_orion = True

class NewProject:
    def __init__(self, orion):
        self.orion = orion

    def add_arg_parser(self):
        args = self.orion.add_arg_parser()
        args.add_argument("-f", "--filename", help="Name of the Yaml file containing ACL variables")
        args.add_argument("-a", "--apply", action="store_false", help="Apply changes to devices, by default only 'dry run'")
        return args
```

The *OrionInventory.main* method is copied from *nornir_orion* but instead of calling *OrionInventory.add_arg_parser* directly it calls *NewProject.add_arg_parser*. The rest of the function is the same, with all the arguments parsed and the inventory generated.

```python
def main(inv_settings: str, no_orion: bool = no_orion):
    orion = orion_inv.OrionInventory()
    my_project = NewProject(orion)
    inv_validate = orion_inv.LoadValInventorySettings()

    tmp_args = my_project.add_arg_parser()
    args = vars(tmp_args.parse_args())
    inv_settings = inv_validate.load_inv_settings(args, inv_settings)

    if no_orion == False:
        orion.test_npm_creds(inv_settings["npm"])
        nr_inv = orion.load_inventory(inv_settings["npm"], inv_settings["groups"])
    elif no_orion == True:
        nr_inv = orion.load_static_inventory("inventory/hosts.yml", "inventory/groups.yml")

    nr_inv = orion.filter_inventory(args, nr_inv)
    nr_inv = orion.inventory_defaults(nr_inv, inv_settings["device"])
    return nr_inv

if __name__ == "__main__":
    main("inv_settings.yml")
```
