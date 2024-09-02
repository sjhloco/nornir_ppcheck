# Nornir Pre/Post Checks

The idea behind this project is to gather the facts (command outputs) about the network state before and after a change and compare the results. There are 3 different command outputs that we are interested in for this purpose:

- **Print:** Outputs printed to screen so we can eyeball the network state before the change
- **vital:** Outputs to compare after the change, will likely be some overlap with the print commands
- **detail:** Outputs only really needed if we have issues after a change (for example full ARP or MAC table)

*Nornir* is used to gather the command output with the scope of devices based on a static inventory with pre-built filters. The inventory is defined in its own module (*nornir_inv.py*) with the idea being that it will make it easier to swap out for a dynamic inventory plugin if need be.

## Installation and Prerequisites

Clone the repository, create a virtual environment and install the required python packages

```python
git clone https://github.com/sjhloco/nornir_ppcheck.git
python -m venv ~/venv/nr_ppchk
source ~/venv/nr_ppchk/bin/activate
cd nornir_ppcheck/
pip install -r requirements.txt
```

- **Path locations:** By default the nornir inventory (*inventory/group.yml* & *inventory/hosts.yml*) and project folders (to store commands and outputs) are in *nornir_ppcheck*, this can be changed with hardcoded variables or environment variables
- **Credentials:** Username and password can be passed in at run time (username runtime flag and password dynamically prompted) or set in environment variables. It is also possible to hardcode the username variable

Environment variables take precedence over hardcoded variables which in turn take precedence over runtime values. The one exception is username where the runtime variable take precedence over all. Environment variables that can be set on the local machine are as follows:

```none
WORKING_DIRECTORY="/user/home"
INVENTORY="inventory"
DEVICE_USER="test_user"
DEVICE_PWORD="blahblah"
```

Hardcoded variables can be found at the start of *main.py*:

```python
working_directory = os.path.dirname(__file__)
inventory = inventory
default_user = test_user
```

## Input commands *(input_cmd.yml)*

The input command file is structured around 3 optional dictionaries (must have at least 1 of them) to specify commands on a per-host (*hosts*) and per-group basis (*groups*) as well as for all hosts (*all*). Each dictionary can hold the commands to print to screen (***cmd_print***) and save to file (***cmd_vital*** and ***cmd_detail***) with all commands merged into a per-host list at runtime.

It is also possible to save the running config to file by adding ***run_cfg: true***, this will be compared along with the vital commands as part of the post-change. Below is an example of inheritance where as *R1* is member of *ios* it will run all commands from *hosts*, *groups* and *all* as well as gathering the running config.

```yaml
hosts:
  R1:
    run_cfg: True
    cmd_print:
      - show ip int brief
    cmd_vital:
      - show ip int brief
      - show ip arp brief
      - show ip route brief
    cmd_detail:
     - show ospf database
     - show ip arp
     - show ip route
groups:
  ios:
    cmd_print:
    - show ip ospf neighbor
    cmd_vital:
    - show ip ospf neighbor
    - show ip ospf database database-summary
    cmd_detail:
     - show ip ospf database 
all:
  cmd_print:
    - show clock
    - show version
  cmd_vital:
    - show ntp associations
```

## Runtime flags

The first thing to do is refine the filters to limit the inventory to only the required hosts. Run with `-s` or `-sd` and the appropriate filter flags to display what hosts the filtered inventory holds (it will not connect to any hosts).

| filter | Description |
| ---------- | ------------|
| `-s` | Prints host and hostname for all the hosts within the filtered inventory (***show***) |
| `-sd` | Same as *-s* but also includes the *host_vars* (***show detail***) |
| `-n` | Match ***hostname*** containing this string (OR logic upto 10 hosts encased in "" separated by space) |
| `-g` | Match a ***group*** or combination of groups *(ios, iosxe, nxos, wlc, asa, checkpoint, paloalto)* |
| `-l` | Match a ***physical location*** or combination of them *(DC1, DC2, campus, etc)* |
| `-ll` | Match a ***logical location*** or combination of them *(WAN, WAN Edge, Core, Access, Services)* |
| `-t` | Match a ***device type*** or combination of them *(firewall, router, dc_switch, switch, wifi_controller)* |
| `-v` | Match any ***Cisco OS version*** that contains this string |

For all runtime flags except *print* (`-ptr`) it is mandatory to specify the name of the change directory (automatically joined onto the *working_directory*) where the input file is located and output files will be saved. Print can be run with an input file in the working directory (*working_directory/input_cmd.yml*) or by specifying the direct path to input file (*.yml* or *.yaml* extension).

| runtime          | Description |
| -------------- | ----------- |
| `-du` | Overrides the ***Network device username*** set by env vars and/or hardcoded variables |
| `-prt` | ***Prints*** command outputs (*cmd_print*), requires name of the change directory or files full path |
| `-vtl` | ***Saves vital*** command outputs (*cmd_vital*) to file, requires name of the change directory |
| `-dtl` | ***Saves detail*** command outputs (*cmd_detail*) to file, requires name of the change directory |
| `-com` | ***Compares*** 2 files to create a HTML file, requires name of the change directory and two file names (that are located in the change directory) |
| `-pre` | Runs *print, *save vital* and *save_detail* |
| `-pos` | Runs *print*, *save vital* and *compare* |

A few xamples of the command structure for filtering and runtime flags.

```python
python main.py -g iosxe -l DC -sd
python main.py -n AZ-ASR-WAN01 -prt /Users/user1/Documents/print_cmds.yml
python main.py -cmp CH001 cmp_file1.txt cmp_file2.txt
python main.py -n AZ-ASR-WAN01 -pre CH001
python main.py -n AZ-ASR-WAN01 -pos CH001
```

## Example outputs

- **Filters:** Filter down to specific hosts or collection of hosts based on *hostname, group, logical location, etc*
  
  ![filter1](https://github.com/user-attachments/assets/62fa8a7c-e54d-47c6-a083-c5694ab19b2f)
  
- **Print commands to screen (prt):** Runs a list of commands and prints the output to screen

  ![print1](https://github.com/user-attachments/assets/78a3909f-64a7-4e23-b617-641aee9a1f06)

- **pre-test(pre):** Runs *print*, *save vital* and *save_detail* (and saves *running config* if enabled)

  ![pre-check1](https://github.com/user-attachments/assets/9b24f7aa-2c1b-453e-855c-703b075d0934)
  
- **post-test(pos):** Runs *print*, *save vital* and *compare* against last two vital files (and *running config* if enabled)

  ![pos-check1](https://github.com/user-attachments/assets/f04416b5-cc69-4aaf-a244-d82efffc7155)
\
  ![diff1](https://github.com/user-attachments/assets/c6fbc575-0b6e-492c-9a48-a189073eef34)

## Unit testing

Pytest unit testing is split into two classes to test inventory settings validation and Nornir interactions

```python
pytest test/test_main.py::TestInputValidate -v
pytest test/test_main.py::TestNornirCommands -v
pytest test/test_main.py -v
```

<!-- | `-val` | Creates a compliance report and saves to file, requires name of the change directory

## Input files

There are two types of input files that can be used with the script, one to print or save command output (*input_cmd.yml*) and the other for validation (*input_val.yml*).

 ### Input validate *(input_val.yml)*

If there are any conflicts between the objects *groups* takes precedence over *all* and *hosts* takes precedence over *groups*. This example validates port-channels on all devices, ACLs on all IOS devices and OSPF neighbors just on HME-SWI-VSS01.

```yaml
hosts:
  HME-SWI-VSS01:
    ospf:
      nbrs: [192.168.255.1]
groups:
  ios:
    acl:
      - name: TEST_SSH_ACCESS
        ace:
          - { remark: MGMT Access - VLAN10 }
          - { permit: 10.17.10.0/24 }
          - { remark: Citrix Access }
          - { permit: 10.10.10.10/32 }
          - { deny: any }
all:
  po:
    - name: Po3
      mode: LACP
      members: [Gi0/15, Gi0/16]

**validate:** Creates a compliance report that is saved in the output directory. If compliance fails the report will also be be printed to screen

``` -->
