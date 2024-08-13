# Validation Builder

This is designed to help with the building of new validations, so the creation of the ***desired_state*** templates and ***actual_state*** python logic. Within this directory there are five files:

- **input_data.yml:** Dictionaries of the features to be validated stored under *all*, *groups* and *hosts* dictionaries
- **desired_state.j2:** Template of per-feature jinja logic used to render the input data to create the desired state
- **desired_state.yml:** The desired state which is the result of the rendered template
- **actual_state.py:** Python file of the per-command python logic used to create the actual state from the command output
- **actual_state.json:** The actual state which is the result of the actual state python logic

*desired_state.yml* and *actual_state.json* are static files of what we are trying to achieve by either rendering the template or formatting the command output returned by a device. *input_data.yml* and *desired_state.j2* hold the code we are trying to create that will eventually be used to dynamically create the first two files.

Even if a file is empty or not used all of these files must be present. The file names and location can be changed in the script variables.

```python
input_file = "input_data.yml"
desired_state = "desired_state.yml"
desired_state_tmpl = "desired_state.j2"
actual_state = "actual_state.json"
actual_state_tmpl = "actual_state.py"
```

Differing runtime flags are used to assist with the different stages of the validation file build process. If no flag is specified the compliance report is created based on the *input_data.yml* and *desired_state.j2*, so is the equivalent of running *nornir_validate*.

| flag           | Description |
| -------------- | ----------- |
| `-di` or `--discovery` | Runs the *desired_state* commands on a device printing the TextFSM data-modeled output
| `-as` or `--actual_state` | Runs the *desired_state* commands printing the JSON formatted *actual_state*
| `-ds` or `--desired_state` | Renders the contents of the *desired_state.j2* template and prints the YAML and JSON formatted output
| `-rds` or `--report_desired_state` | Builds and prints a compliance report using the dynamically created *desired_state* and static *actual_state.json* file
| `-ras` or `--report_actual_state` |  Builds and prints a compliance report using the dynamically created *actual_state* and static *desired_state.yml* file
| None | Builds and prints a compliance report using dynamically created *desired_state* and *actual_state*

By default the inventory *groups* and *defaults* (username and password) are used from *nornir_validate/inventory* (*parent_dir*) and the inventory *hosts* from *nornir_validate/validation_builder/inventory* (*current_dir*). Any of these can be changed by swapping out *parent_dir* and *current_dir* in the *engine* method.

```python
    def engine(self) -> Result:
        nr = InitNornir(
            inventory={
                "plugin": "SimpleInventory",
                "options": {
                    "host_file": os.path.join(currentdir, "inventory/hosts.yml"),
                    "group_file": os.path.join(parentdir, "inventory/groups.yml"),
                    "defaults_file": os.path.join(parentdir, "inventory/defaults.yml"),
                },
            }
        )
```

The following steps walk you through the process of creating a new validation using the validate builder.

### 1. Discovery (di): Gather command output from devices

Within the *desired_state.yml* define a list of dictionaries with the key being the command and the value the desired state. At this stage of the process the desired state is an empty dictionary as the sole purpose of the file is to define the commands that will be run against a device.

```yaml
- show ip ospf neighbor: {}
```

`-di` returns the command output as a list formatted into a *ntc-templates* based TextFSM data model. The command must have already have been defined by [NTC](https://github.com/networktocode/ntc-templates/tree/master/ntc_templates/templates) and be an exact match of the full command, no abbreviations.

```python
python val_builder.py -di
**** Validation Builder - Discovery ********************************************
discovery_task******************************************************************
* HME-SWI-VSS01 ** changed : False *********************************************
vvvv discovery_task ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
{ 'show ip ospf neighbor': [ { 'address': '192.168.255.1',
                               'dead_time': '00:00:35',
                               'interface': 'Vlan98',
                               'neighbor_id': '192.168.255.1',
                               'priority': '1',
                               'state': 'FULL/BDR'}]}
^^^^ END discovery_task ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

There are some commands where NTC templates are not used and instead the actual state is created from screen scrapping. In these situations we must convert the output from a string to a list by adding the command to the variable ***non_ntc_tmpl_cmds*** or ***non_ntc_tmpl_regex_cmds*** within *actual_state.py* function *format_actual_state*. By default no strings will generate an *actual state* as this safe guards against the script failing if the command output is an error.

### 2. Actual state (-as): Format the command output into the actual state

Based on the discovery output build the python logic to perform the data model formatting of the *actual_state* to get the values to be validate. This is defined in the *actual_state.py* on a *per-os_type* basis.

By using a breakpoint (*ipdb.set_trace()*) after the command you can look through the discovery data model to workout the python logic for the *actual_state* data model. The [nornir docs](https://nornir.readthedocs.io/en/latest/howto/ipdb_how_to_use_it_with_nornir.html) have a good tutorial on using the [iPython pdb debugger](https://github.com/gotcha/ipdb).

```python
if "show ip ospf neighbor" in cmd:
    # ipdb.set_trace()
    for each_nhbr in output:
        tmp_dict[each_nhbr['neighbor_id']] = {'state': remove_char(each_nhbr['state'], '/')}
```

`-as` runs the commands from the *desired_state.yml* file and passes the returned output through *actual_state.py* printing the resulting *actual_state* to screen.

```python
python val_builder.py -as
**** Validation Builder - Actual State *****************************************
actual_state_task***************************************************************
* HME-SWI-VSS01 ** changed : False *********************************************
vvvv actual_state_task ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
{'show ip ospf neighbor': {'192.168.255.1': {'state': 'FULL'}}}
^^^^ END actual_state_task ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

Add this to the *actual_state.json* file to create a static *actual_state* to save having to run the commands against a live device whilst developing the desired state. Although the JSON formatting of the returned actual_state is correct, for this to be used in Python (the static *actual_state.json* file) you must swap out all `'` for `"`.

```python
{ "show ip ospf neighbor": { "192.168.255.1": {"state": "FULL"}}}
```

### 3. Desired state (-ds): Create the input_data and desired state template

In the *input_data.yml* file define a feature name (will be matched in the template) and elements of this feature that are to be validated. How this is structured depends on the format of the commands output (*actual_state*).

```yaml
all:
  ospf_nbr:
    nbrs: [192.168.255.1]
```

The *input_data* has a direct relationship with the *desired_state.j2* template as it renders that data to create the *desired_state*. The template creates a YAML per-device_type list of nested dictionaries with the command being the key and the value the expected feature state.

Under the ***os_type*** (*ios*) and ***feature*** (*ospf*) add the command (*- show ip ospf neighbor:*) followed by the *input_vars* to populate the input_file variables in the rendered template.

```jinja
{% if 'ios' in os_type |string %}
{% if feature == 'ospf_nbr' %}
- show ip ospf neighbor:
    _mode: strict
{% for each_nbr in input_vars.nbrs %}
    {{ each_nbr }}:
      state: FULL
{% endfor %}
{% endif %}
{% endif %}
```

`-ds` prints the output of the rendered template in YAML and JSON format. The JSON formatted output is what will be used by the compliance report, so this should match the structure of the *actual_state* (formatted command output).

```python
python val_builder.py -ds
**** Validation Builder - Desired State ****************************************
desired_state_task**************************************************************
* HME-SWI-VSS01 ** changed : False *********************************************
vvvv desired_state_task ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
---- template in YAML ** changed : False --------------------------------------- INFO
- show ip ospf neighbor:
    _mode: strict
    192.168.255.1:
      state: FULL

---- template in JSON ** changed : False --------------------------------------- INFO
{ 'result': { 'show ip ospf neighbor': { '192.168.255.1': {'state': 'FULL'},
                                         '_mode': 'strict'}}}
^^^^ END desired_state_task ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

If the desired state contains a nested list it must be specifically called out as a list. For example, with *show vlan brief* interfaces:

```none
- show vlan brief:
    10:
      name: vl10
      intf:
        _mode: strict
        list: ['Gi0/1', 'Gi0/2']
```

### 4. Static Compliance Report (-rds): Test dynamic desired_state against static actual_state

Use `-rds` to build and print the compliance report using the static *actual_state* (*actual_state.json*) from step2 and the dynamically created *desired_state* (*input_data.yml* and *desired_state.j2*) from step3.

```python
python val_builder.py -rds
**** Validation Builder - Compliance Report using dynamic desired_state and static actual_state
report_desired_state_task*******************************************************
* HME-SWI-VSS01 ** changed : False *********************************************
vvvv report_desired_state_task ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
{ 'show ip ospf neighbor': { 'complies': True,
                             'extra': [],
                             'missing': [],
                             'present': { '192.168.255.1': { 'complies': True,
                                                             'nested': True}}}}
^^^^ END report_desired_state_task ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

It is also possible to use `-ads` to test the dynamically created *actual_state* against the static *desired_state* by adding the Jinja template YAML output from step3 to the file *desired_state.yml* (in early steps was an empty dictionary). This is not really needed when building a new as everything has already been proven.

### 5. Compliance Report: Create Compliance report with dynamic desired_state and actual_state

Once happy with the new validations run the script with no flags (the equivalent of using *nr_val.py*) to dynamically create files for both the *desired_state* and *actual_state*.

```python
python val_builder.py
**** Validation Builder - Compliance Report ************************************
report_task*********************************************************************
* HME-SWI-VSS01 ** changed : False *********************************************
vvvv report_task ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
{ 'complies': True,
  'show ip ospf neighbor': { 'complies': True,
                             'extra': [],
                             'missing': [],
                             'present': { '192.168.255.1': { 'complies': True,
                                                             'nested': True}}},
  'skipped': []}
^^^^ END report_task ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

The new lines of code in the jinja template and python file can now be moved into the relevant files within the nornir_validate *templates* directory to be used for future validations.

### 6. Update commands in unit tests

***test_validations.py*** uses static command outputs to test that the desired state templating and actual state command formatting is correct. Before adding the new commands to the testing it is worth checking that all current tests are passing, use `pytest` to run both *test_nr_val.py* and *test_validations.py*.

The ***desired_actual_cmd.py*** file contains the following 3 dictionaries with each having a further child dictionary for the different os_types.

- **desired_state:** Should match the templated result of the rendered jinja template
- **cmd_output:** The raw textFSM formatted device command output (used to create the actual_state)
- **actual_state:** Should match the formatted result of the actual_state python logic

Test methods have been built for WLC and Checkpoints but are hashed out as there are no actual tests for these device types at the moment.

#### a. Desired state - Renders template with the input data asserting against static desired state

Add the input data from val_builder *input_data.yml* to the relevant groups *os_type* dictionary within ***input_data_validations.yml***.

```yaml
    ospf_nbr:
      nbrs: [192.168.255.1, 2.2.2.2]
```

Add the JSON formatted output (not YAML) from ***desired_state*** (`python val_builder.py -ds`) to the end of relevant *os_type* dictionary in the ***desired_state*** section of *desired_actual_cmd.py*. You must remove the parent the *results* dictionary and the 2nd dictionary curly brackets (leave *_mode* in), black will automatically fix formatting and replace all `'` with `"` when the file is saved.

```python
        "show ip ospf neighbor": {
            "_mode": "strict",
            "192.168.255.1": {"state": "FULL"},
            "2.2.2.2": {"state": "FULL"},
        },
```

The desired_state unit tests can be run for all os_types or for each os_type individually.

```python
pytest tests/test_validations.py::TestDesiredState -vv
pytest tests/test_validations.py::TestDesiredState::test_ios_desired_state_templating -vv
pytest tests/test_validations.py::TestDesiredState::test_nxos_desired_state_templating -vv
pytest tests/test_validations.py::TestDesiredState::test_asa_desired_state_templating -vv
```

#### b. Actual State - Creates DMs from static command output asserting against static actual state

Add the discovery output `python val_builder.py -di` to the end of relevant *os_type* dictionary in the ***cmd_output*** section of *desired_actual_cmd.py*. You must remove the outer dictionary curly brackets (*{}*), black will automatically fix formatting and replace all `'` with `"` when the file is saved.

```python
        "show ip ospf neighbor": [
            {
                "address": "192.168.255.1",
                "dead_time": "00:00:35",
                "interface": "Vlan98",
                "neighbor_id": "192.168.255.1",
                "priority": "1",
                "state": "FULL/BDR",
            },
```

Add the output from ***actual_state*** (`python val_builder.py -as`) to the relevant os_type dictionary in ***actual_state*** section of *desired_actual_cmd.py*. You must remove the outer dictionary curly brackets (*{}*), black will automatically fix formatting and replace all `'` with `"` when the file is saved.

The actual_state unit tests can be run for all os_types or for each os_type individually.

```python
pytest tests/test_validations.py::TestActualState -vv
pytest tests/test_validations.py::TestActualState::test_ios_actual_state_formatting -vv
pytest tests/test_validations.py::TestActualState::test_nxos_actual_state_formatting -vv
pytest tests/test_validations.py::TestActualState::test_asa_actual_state_formatting -vv
```

The unit tests can be run for both desired and actual state by omitting the method name.

```python
pytest tests/test_validations.py -vv
```
