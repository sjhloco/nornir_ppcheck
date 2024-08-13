# Nornir Validate

Uses Nornir (with ***nornir-netmiko***) to gather and format device output before feeding this into ***napalm-validate*** in the form of ***actual_state*** and ***desired_state*** to produce a ***compliance report***. The idea behind this project is to run pre and post checks on network devices based on an input file of the desired *device_state*.

As the name suggests I have not reinvented the wheel here, I just extended [*napalm_validate*](https://github.com/napalm-automation/napalm/blob/develop/napalm/base/validate.py) (importing the *napalm_validate compare* method) to validate on commands rather than getters to allow for the flexibility of validating any command output.

## Current Validations

| Validation | Strict | IOS/IOS-XE | NXOS | ASA | WLC | Palo
| ---------- | ------ | ---------- | ---- | --- | --- | ----------
| Image | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| Management ACL (SSH/SNMP/HTTP) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌
| Port-channel (membership & status) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| Interface brief (IP and status) | ❌ |  ✅  | ❌ | ❌ | ❌ | ❌
| CDP neighbors | ❌ |  ✅  | ❌ | ❌ | ❌ | ❌
| LLDP neighbors | ❌ |  ✅  | ❌ | ❌ | ❌ | ❌
| HSRP (priority and state) | ❌ |  ✅  | ❌ | ❌ | ❌ | ❌
| Switch stack (state and priority) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| VSS HA state | ❌ |  ✅  | ❌ | ❌ | ❌ | ❌
| Interface status (speed, duplex, status) | ❌ |  ✅  | ❌ | ❌ | ❌ | ❌
| Switchport (mode and vlan) | ❌ |  ✅  | ❌ | ❌ | ❌ | ❌
| VLANs (member interfaces) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| Spanning-Tree (FWD vlan interfaces) | ❌ |  ✅  | ❌ | ❌ | ❌ | ❌
| MAC address table (count) | ✅|  ✅  | ❌ | ❌ | ❌ | ❌
| MAB & DOT1X Auth Sessions (count) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| VRF (member interfaces) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| Route summary (total subnets) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| Routing table (route and strict next-hops) | ❌ |  ✅  | ❌ | ❌ | ❌ | ❌
| OSPF Interface (interfaces, area, cost) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| OSPF neighbors (neighbor, state) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| OSPF database (Total LSAs) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| EIGRP Interface | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| EIGRP neighbors | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| BGP peers (peer, asn, rcv_pfx) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| NVE VNI (L3VNI, VRF, BDI, state) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| NVE peer (L3VNI, peer, state) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌
| VPN (peer, interface, state) | ✅ |  ✅  | ❌ | ❌ | ❌ | ❌

- Management ACL: Validation of the allowed management addresses for SSH and HTTP on ASA or an extended ACL (IP and any port) on other platforms
- Routing table: Uses a string for a single next-hop or a list if there are multiple next-hops
- BGP peers: If peers have same the IP uses those from the upper address family (for example with MPLS VPN will ignore IPv4 and only use VPNv4 peer)

### Caveats

Due to the way that the *napalm_validate* matching works if can miss some similar numeric values. For example, with the number of routes if the desired number is 5 and the actual number is 15 this validation will pass as it 5 is in both. Not sure if this is by design, at end of the day I am using it for a more expanded purpose so need to look how it performs normally before seeing if I can fix it.

## Installation and Prerequisites

Clone the repository, create a virtual environment and install the required python packages

```bash
git clone https://github.com/sjhloco/nornir_validate.git
python -m venv ~/venv/nr_val
source ~/venv/nr_val/bin/activate
cd nornir_validate/
pip install -r requirements.txt
```

## Running nornir_validate

To generate a meaningful compliance report the following elements are needed:

- **input data (variables)**: Yaml file (default is *input_data.yml*) that holds the *host*, *group* and *all* data that describe the desired state of the network
- **desired_state template:** Jinja template (*desired_state.j2*) that is rendered with the input data to create the desired state
- **actual_state python logic:** Python method (*actual_state.py*) that creates a data structure from the command outputs to be used as a comparison against the desired state

*nornir_validate* can be run independently as a standalone script or imported to use a scripts existing nornir inventory.

### Standalone

When run as standalone *nornir_validate* creates its own nornir inventory (*config.yml*) looking in the *inventory* directory for *hosts.yml*, *groups.yml* and *defaults.yml*.

By default input data is gathered from *input_data.yml* and the compliance report not saved to file. Either of these can be changed in the variables section at the start of *nr_val.py* or overridden using runtime flags.

```python
input_data = "input_data.yml"
report_directory = None
```

| flag           | Description |
| -------------- | ----------- |
| `-f` or `--filename` | Override value set in *input_data* variable to manually define input data file |
| `-d` or `--directory` | Override value set in *directory* variable to save compliance reports to file |

Specifying anything other than *None* for the *report_directory* enables saving the compliance report in the format *hostname_compliance_report_YYYYMMDD-HHMM.json*

```python
python nr_val.py
```

If the validation fails a full compliance report will be printed to screen and the nornir task marked as failed.

<img src=https://user-images.githubusercontent.com/33333983/143948220-65f6745c-a67b-46ca-8791-39131f82ca32.gif  width="750" height="500">

### Imported

The ***validate_task*** function can be imported directly into a script to make use of an existing nornir inventory. When calling the imported function it is mandatory to specify the *input_data*, the *directory* is optional and only needed if you want to save the report to file.

```python
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_validate.nr_val import validate_task

nr = InitNornir(config_file="config.yml")
result = nr.run(task=validate_task, input_data="my_input_data.yml", directory='/Users/user1/reports')
print_result(result)
```

Rather than using a file the *input_data* can be a nested dictionary formatted in the same manner using *hosts*, *groups* and *all*.

```python
my_input_data = {"groups": {"ios": {"acl": [{"name": "TEST_SSH_ACCESS",
                                             "ace": [{"remark": "MGMT Access - VLAN10"},
                                                     {"permit": "10.17.10.0/24"}]}]}}}
result = nr.run(task=validate_task, input_data="my_input_data")
```

## Input Data

The input data structured around three dictionaries made up of features and the their desired state

- **hosts:** Dictionary of host names each holding dictionaries of host-specific features being validated
- **groups:** Dictionary of group names each holding dictionaries of group-specific features being validated
- **all**: Dictionaries of variables for the different features being validated across all hosts

The host or group name must be an exact match of the host or group name within the nornir inventory. If there is a confliction between the features, *groups* take precedence over *all* and *hosts* over *groups*.

The result of the below example will check the port-channel state and port membership of *all* devices, the image version for the *iosxe* group and the OSPF neighbors on host *HME-RTR01*.

```yaml
hosts:
  HME-RTR01:
    ospf_nbr:
      nbrs: [192.168.1.5, 2.2.2.2]
groups:
  iosxe:
    image: 16.6.2
all:
  port_channel:
    Po2:
      protocol: LACP
      members: [Gi0/15, Gi0/16]
```

## Desired State

The input file (***input_data.yml***) is rendered by a jinja template (***desired_state.j2***) to produce a YAML formatted list of dictionaries with the key being the command and the value the desired output. The top level Jinja condition is for the ***os_type*** got from nornir *platform* (*ios* and *iosxe* are the same) with ***feature*** matching the feature name within the input file to make the rendering conditional. Optionally, ***strict*** mode can be used to ensure of an exact match, no more, no less.

```jinja
{% if 'ios' in os_type |string %}
{% if feature == 'image' %}
- show version:
    image: {{ input_vars }}
{% elif feature == 'port_channel' %}
- show etherchannel summary:
{% for each_po_name, each_po_info in input_vars.items() %}
    {{ each_po_name }}:
      status: U
      protocol: {{ each_po_info.protocol }}
      members:
        _mode: strict
{% for each_member in each_po_info.members %}
        {{ each_member }}:
          mbr_status: P
{% endfor %}{% endfor %}
{% elif feature == 'ospf_nbr' %}
- show ip ospf neighbor:
    _mode: strict
{% for each_nbr in input_vars.nbrs %}
    {{ each_nbr }}:
      state: FULL
{% endfor %}
{% endif %}{% endif %}
```

Below is an example of the YAML output after rendering the template with the example input data.

```yaml
- show version: 
    image: 16.6.2
- show etherchannel summary:
    Po2:
      status: U
      protocol: LACP
      members:
        _mode: strict
        Gi0/15:
          mbr_status: P
        Gi0/16:
          mbr_status: P
- show ip ospf neighbor:
    _mode: strict
    192.168.255.1:
      state: FULL
    2.2.2.2:
      state: FULL
```

The resulting python object is generated by serialising the YAML output and is stored as a host_var (nornir *data* dictionary) called *desired_state*.

```python
{
    "show version": {"image": "16.6.2"},
    "show etherchannel summary": {
        "Po2": {
            "status": "U",
            "protocol": "LACP",
            "members": {
                "_mode": "strict",
                "Gi0/15": {"mbr_status": "P"},
                "Gi0/16": {"mbr_status": "P"},
            },
        }
    },
    "show ip ospf neighbor": {
        "192.168.255.1": {"state": "FULL"},
        "2.2.2.2": {"state": "FULL"},
        "_mode": "strict",
    },
}
```

## Actual State

Netmiko gathers command outputs creating TextFSM formatted data-models (using *[ntc-templates](https://github.com/networktocode/ntc-templates/tree/master/ntc_templates/templates)*) that are fed into ***actual_state.py*** and matched on *os_type* specific methods and commands to create a nested dictionary that matches the structure of the *desired_state*.

```python
def ios_format(
    cmd: str, output: List, tmp_dict: Dict[str, None], actual_state: Dict[str, None]
) -> Dict[str, Dict]:
    if "show version" in cmd:
        tmp_dict["image"] = output[0]["version"]
    elif "show etherchannel summary" in cmd:
        for each_po in output:
            tmp_dict[each_po["po_name"]]["status"] = each_po["po_status"]
            if each_po["protocol"] == "-":
                each_po["protocol"] = "NONE"
            tmp_dict[each_po["po_name"]]["protocol"] = each_po["protocol"]
            po_mbrs = {}
            for mbr_intf, mbr_status in zip(
                each_po["interfaces"], each_po["interfaces_status"]
            ):
                po_mbrs[mbr_intf] = {"mbr_status": mbr_status}
            tmp_dict[each_po["po_name"]]["members"] = po_mbrs
    elif "show ip ospf neighbor" in cmd:
        for each_nhbr in output:
            tmp_dict[each_nhbr["neighbor_id"]] = {
                "state": remove_char(each_nhbr["state"], "/")
            }
    actual_state[cmd] = dict(tmp_dict)
    return actual_state
```

The resulting *actual_state* is the same as the *desired_state* except for the absence of *'_mode': 'strict'*.

```python
{
    "show version": {"image": "16.6.2"},
    "show etherchannel summary": {
        "Po2": {
            "status": "U",
            "protocol": "LACP",
            "members": {
                "Gi0/15": {"mbr_status": "P"},
                "Gi0/16": {"mbr_status": "P"},
            },
        }
    },
    "show ip ospf neighbor": {
        "192.168.255.1": {"state": "FULL"},
        "2.2.2.2": {"state": "FULL"},
    },
}
```

For each command the formatting will be different as the captured data is different, however the principle is same in terms of the structure.

## Compliance Report

The *desired_state* and *actual_state* are fed into ***compliance_report.py*** and iterated through ***napalm_validate*** (***validate.compare*** method) to produces a per-command compliance report. The commands are grouped into an overall compliance report with the reports compliance status set to *false* if any of the individual commands failed compliance.

In this example compliance report the image and port-channel passed but the report failed due to a missing OSPF neighbor (*1.1.1.1*).

```python
{ 'complies': False,
  'show etherchannel summary': { 'complies': True,
                                 'extra': [],
                                 'missing': [],
                                 'present': { 'Po1': { 'complies': True,
                                                       'nested': True}}},
  'show ip ospf neighbor': { 'complies': False,
                             'extra': [],
                             'missing': ['1.1.1.1'],
                             'present': { '10.90.10.2': { 'complies': True,
                                                          'nested': True}}},
  'show version': { 'complies': True,
                    'extra': [],
                    'missing': [],
                    'present': {'image': {'complies': True, 'nested': False}}},
  'skipped': []}
  ```

## Validation Builder

 The *validation_builder* directory contains *val_builder.py* to assist with the building of new validations. The README within in this directory has more details on how to use this.

## TBC in the Future

Am still trialing this out, is a lot of work still to be done on adding differing platform commands and putting it through its paces in a real world environment. Like many of my other projects what seems like a great idea in my head could turn out in reality to not be much use in the real world. Only time will tell..........

I plan to do the following over the coming months:

- Add NXOS commands to cover the majority of what is done by IOS/IOS-XE with the addition of NXOS specific features. Not sure whether to use TextFSM or native NXOS JSON cmds, the idea will be to where possible use common python functions (*actual_state.py*) or jinja macros (*desired_state.py*) to keep it DRY
- Add ASA commands, will be interfaces, routing and VPN
- Add WLC commands, will be pretty limited with interfaces and APs as am guessing will soon be EO
- Add Palo commands, will be interfaces and routing rather than security policy based
- Possibly add support for genie, not sure where to put the toggle of whether to use netmiko or genie for a command
- Package it up, need to make it easy to extend (abstraction of actual_state.py and desired_state.j2) so will not be as much need to make changes to the base code

I may look into replacing or extending napalm-validate as would be good to add support for:

- Tolerances for the numeric values rather than the exact matches (also fix the mathcing caveat)
- Convert JSON report to HTML page something in the vain of the [Robot framework](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html)

To allow me to fudge it to be able to import it as a module (due to inheritance) I added the following to *nr_val.py* that I need to remember to remove when it gets packaged up and check the validation_builder (as effects inheritance), don't forget.....

```python
import os
import sys
sys.path.insert(0, "nornir_validate")

    if "nornir_validate" in os.getcwd():
        tmpl_path = "templates/"
    else:
       tmpl_path =  "nornir_validate/templates/"
```
