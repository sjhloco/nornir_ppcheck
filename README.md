# Nornir Checks

Builds the Nornir inventory from Orion or a static inventory using runtime arguments to perform one of the following 3 pre/post-check actions:

- **Print commands to screen (prt):** Runs a list of commands and prints the output to screen
- **Save vital commands to file (vtl):** Runs a list of vital commands and saves the output to file
- **Save detail commands to file (dtl):** Runs a list of detail commands and saves the output to file
- **compare (com):** Compare the two specified files creating a *.html* file
- **Nornir-validate(val):** Runs a list of commands and validates actual state against the desired state
- **pre-test(pre):** Runs *print, *save vital* and *save_detail*
- **post-test(pos):** Runs *print*, *save vital* and *compare* against last two vital files (and running config if enabled)

The idea is that print is used for commands you want to eyeball the state of before the change, vital for commands you want to compare after the change and detail for if you have issues and need to check the state of things before the change. Compare can either compare specified files or as part of pre-test will compare the two newest vital files.

## Input files

There are two types of input files that can be used with the script, one to print or save command output (*input_cmd.yml*) and the other for validation (*input_val.yml*). Both files are structured around 3 optional dictionaries, you must have at least 1 of them:

- **hosts:** Specify commands or desired state validations on a per-host basis
- **groups:** Specify commands or desired state validations on a per-group basis
- **all**: Specify commands or desired state validations for all hosts

### Input commands *(input_cmd.yml)*

Holds the commands to print (*cmd_print*), vital commands to save (*cmd_vital*) and detail commands to save (*cmd_detail*) with each set merged into a per-host list at run time. For example, if *HME-SWI-VSS01* was a member of *ios* it would run all commands from *hosts*, *groups* and *all*.

It is also possible to save the *running config* to file by adding *run_cfg: True*. The only time this will be ignored is if print is run with a direct file location (rather than working directory) as there will be no output directory to save the file.

```yaml
hosts:
  HME-SWI-VSS01:
    run_cfg: True
    cmd_print:
      - show ip ospf neighbor
      - show ip int brief
    cmd_vital:
      - show version
      - show run
    cmd_detail:
     - show ospf database
groups:
  ios:
    cmd_print:
      - show clock
    cmd_vital:
      - show ntp associations
    cmd_detail:
     - show status
all:
  acl:
    cmd_print:
      - show etherchannel summary
    cmd_vital:
      - show ip route summary
    cmd_detail:
      - show ip route summary
```

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
```

## Runtime flags and files

If the *npm* user is not defined (`-nu`) a static inventory (*/inventory/hosys.yml*) is used. The *device* username and password can be specified at runtime (`-du`) or within the inventory settings (*inv_settings.yml*).

The first thing you want to do is refine the filters to limit the inventory to only the required hosts. Run it with `-s` or `-sd` and the appropriate filter arguments to display what hosts the filtered inventory holds (it will not run any commands against the hosts).

| flag    | Description |
| ------- | -------------|
| `-n` | Match any ***hostnames*** that contains this string. Uses OR logic with upto 10 host names encased in "" separated by space
| `-g` | Match a ***group*** or combination of groups *(ios, iosxe, nxos, wlc, asa (includes ftd), checkpoint* |
| `-l` | Match a ***physical location*** or combination of them *(DC1, DC2, DCI (Overlay), ET, FG)* |
| `-ll` | Match a ***logical location*** or combination of them *(WAN, WAN Edge, Core, Access, Services)* |
| `-t` | Match a ***device type*** or combination of them *(firewall, router, dc_switch, switch, wifi_controller)* |
| `-v` | Match any ***Cisco OS version*** that contains this string |
| `-s` | Prints (***show***) hostname and host for all the hosts within the filtered inventory |
| `-sd` | Prints (***show detail***) all the hosts within the inventory including their host_vars |

When using any flags except for *print* (`-ptr`) it is mandatory to specify the working directory for the input files and to save output files.

```python
$ python main.py -n HME-SWI-VSS -vtl CH002
❌ The 'vital_save' working directory /Users/user1/Documents/nornir_checks/CH002 does not exist
```

Print (`-ptr`) can be run with an input file in the working directory (*/CH002/input/input_cmd.yml*) or by specifying the direct path to input file (*.yml* or *.yaml* extension) as you may not always need a directory if no output is saved to file.

| flag           | Description |
| -------------- | ----------- |
| `-nu` | Overrides the ***NPM username*** set with *npm.user* in *inv_settings.yml* |
| `-du` | Overrides the ***Network device username*** set with *device.user* in *inv_settings.yml* |
| `-prt` | ***Prints*** command outputs (*cmd_print*), requires name of the change directory or direct path to file |
| `-vtl` | ***Saves vital*** command outputs (*cmd_vital*) to file, requires name of the change directory |
| `-dtl` | ***Saves detail*** command outputs (*cmd_detail*) to file, requires name of the change directory |
| `-com` | ***Compares*** 2 files to create a HTML file, requires name of the change directory and 2 file names (in input_dir) |
| `-val` | Creates a compliance report and saves to file, requires name of the change directory |
| `-pre` | Runs *print, *save vital* and *save_detail* |
| `-pos` | Runs *print*, *save vital* and *compare* |

If the *input* or *output* directories do not exist within the working directory they will be automatically created. The script will still fail if an input file does not exist in the input directory.

```python
$ python main.py -n HME-SWI-VSS -pre CH002
✅ Created the directory /Users/user1/Documents/nornir_checks/CH002/output
✅ Created the directory /Users/user1/Documents/nornir_checks/CH002/input_files
❌ The 'pre_test' input file /Users/user1/Documents/nornir_checks/CH002/input_files/input_cmd.yml does not exist
```

The default parent directory location, directory names and filenames can be changed using the variables at the start of the script. By default the *working_directory is nornir_checks.

```python
working_directory = os.path.dirname(__file__)
output_directory = "output"
input_directory = "input_files"
input_cmd_file = "input_cmd.yml"
input_val_file = "input_val.yml"
```

## Installation and Prerequisites

Clone the repository, create a virtual environment and install the required python packages
!!!! add note about need to clone sub packages, need to test !!!!!

git clone https://github.com/sjhloco/nornir_check.git
python -m venv ~/venv/nr_chk
source ~/venv/nr_chk/bin/activate
cd nornir_check/
pip install -r requirements.txt

## Running the script

First make sure my filters are correct, this will filter it down to the one device named *HME-SWI-VSS*

```python
$ python main.py -n ET-6509E-VSS01 -s
======================================================================
1 hosts have matched the filters 'ET-6509E-VSS01':
-Host: ET-6509E-VSS01      -Hostname: 10.30.20.101
```

**Print command outputs to screen:** This can reference a directory holding the input file or be the full path to the input file (as in this case)

```python
$ python main.py -n ET-6509E-VSS01 -prt /Users/user1/Documents/input_cmd.yml
PRINT command output************************************************************
* ET-6509E-VSS01 ** changed : False ********************************************
vvvv PRINT command output ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
---- show bgp all summary ** changed : False ----------------------------------- INFO
% BGP not active

---- show int status ** changed : False ---------------------------------------- INFO

Port      Name               Status       Vlan       Duplex  Speed Type
Gi0/0                        connected    routed     a-full   auto RJ45
Gi0/1                        connected    1          a-full   auto RJ45
Gi0/2                        connected    1          a-full   auto RJ45
Gi0/3                        connected    1          a-full   auto RJ45
^^^^ END PRINT command output ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

**Save command outputs to file:** Must define the change directory that holds the input file and where the output will be saved. Within the file each command output is separated by a new line and a row of *===* containing the command. The running configuration will also be saved to file if *run_cfg: True* is defined.

```python
$ python main.py -n ET-6509E-VSS01 -vtl CH002
✅ Created the directory /Users/user1/Documents/nornir_checks/CH002/output
VITAL command output************************************************************
* ET-6509E-VSS01 ** changed : True *********************************************
vvvv VITAL command output ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
✅ Created command output file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_running-config_20220517-0751.txt'
✅ Created command output file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_vital_20220517-0751.txt'
^^^^ END VITAL command output ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

$ python main.py -n ET-6509E-VSS01 -dtl CH002
DETAIL command output***********************************************************
* ET-6509E-VSS01 ** changed : True *********************************************
vvvv DETAIL command output ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
✅ Created command output file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_running-config_20220517-0752.txt'
✅ Created command output file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_detail_20220517-0752.txt'
^^^^ END DETAIL command output ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

**Compare files:** Get the differences between the 2 specified files (looks in input directory of working directory) saving the result in a HTML file.

```python
$ python main.py -n ET-6509E-VSS01 -cmp CH002 ET-6509E-VSS01_vital_20220517-0751.txt ET-6509E-VSS01_vital_20220517-0755.txt
COMPARE command output**********************************************************
* ET-6509E-VSS01 ** changed : False ********************************************
vvvv COMPARE command output ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
✅ Created compare HTML file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_diff_vital.html'
^^^^ END COMPARE command output ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

**Pre-test:** Prints command output to screen and saves to file the running-config, vital and detail commands. If any of the input dictionaries are not defined (*run_cfg, cmd_print, cmd_vital, cmd_detail*) those tests will not be run (will display *⚠️  There were no commands to run for: xxx*)

```python
(nr_chk) macoloco:nornir_checks (main)$python main.py -n ET-6509E-VSS01 -pre CH002
PRE_TEST command output*********************************************************
* ET-6509E-VSS01 ** changed : True *********************************************
vvvv PRE_TEST command output ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
✅ Created command output file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_running-config_20220517-0819.txt'
✅ Created command output file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_vital_20220517-0819.txt'
✅ Created command output file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_detail_20220517-0819.txt'
---- show bgp all summary ** changed : False ----------------------------------- INFO
% BGP not active

---- show int status ** changed : False ---------------------------------------- INFO

Port      Name               Status       Vlan       Duplex  Speed Type
Gi0/0                        connected    routed     a-full   auto RJ45
Gi0/1                        connected    1          a-full   auto RJ45
Gi0/2                        connected    1          a-full   auto RJ45
Gi0/3                        connected    1          a-full   auto RJ45
^^^^ END PRE_TEST command output ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

**Post-test:** Prints command output to screen, saves to file running-config and vital as well as comparing the last 2 vital and running-config files. If any of the input dictionaries are not defined (*run_cfg, cmd_print, cmd_vital, cmd_detail*) those tests will not be run (will display *⚠️  There were no commands to run for: xxx*)

```python
$ python main.py -n ET-6509E-VSS01 -pos CH002
POST_TEST command output********************************************************
* ET-6509E-VSS01 ** changed : True *********************************************
vvvv POST_TEST command output ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
✅ Created command output file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_running-config_20220517-0825.txt'
✅ Created command output file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_vital_20220517-0825.txt'
✅ Created compare HTML file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_diff_vital.html'
✅ Created compare HTML file '/Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_diff_running-config.html'
---- show bgp all summary ** changed : False ----------------------------------- INFO
% BGP not active

---- show int status ** changed : False ---------------------------------------- INFO

Port      Name               Status       Vlan       Duplex  Speed Type
Gi0/0                        connected    routed     a-full   auto RJ45
Gi0/1                        connected    1          a-full   auto RJ45
Gi0/2                        connected    1          a-full   auto RJ45
Gi0/3                        connected    1          a-full   auto RJ45
^^^^ END POST_TEST command output ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

**validate:** Creates a compliance report that is saved in the output directory. If compliance fails the report will also be be printed to screen

```python
$ python main.py -n ET-6509E-VSS01 -val CH002
validate_task*******************************************************************
* HME-SWI-VSS01 ** changed : False *********************************************
vvvv validate_task ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
✅ Validation report complies, desired_state and actual_state match. The report can be viewed using:
   cat /Users/user1/Documents/nornir_checks/CH002/output/ET-6509E-VSS01_compliance_report_20220517-08:41.json | python -m json.tool
^^^^ END validate_task ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```
