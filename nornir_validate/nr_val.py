from typing import Any, Dict, List
import logging
import argparse
import yaml
from collections import defaultdict
import os
import sys
import ipdb

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_jinja2.plugins.tasks import template_file
from nornir_utils.plugins.tasks.data import load_yaml
from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.functions import print_result

# Needed so can find modules when is import into another script
sys.path.insert(0, "nornir_validate")
from templates.actual_state import format_actual_state
from compliance_report import report

# ----------------------------------------------------------------------------
# Manually defined variables and user input
# ----------------------------------------------------------------------------
# Name of the input variable file (needs its full path)
input_data = "input_data.yml"
# Enter a directory location to save compliance report to file
report_directory = None
# report_directory = "/Users/user1/Documents/Coding/Nornir/code/nornir_validate"
# report_directory = "C:\\scripts\\nornir_checks\\nornir_validate\\reports"

# ----------------------------------------------------------------------------
# Input Arguments
# ----------------------------------------------------------------------------
def _create_parser() -> Dict[str, Any]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--directory",
        default=report_directory,
        help="Directory where to save the compliance report",
    )
    parser.add_argument(
        "-f",
        "--filename",
        default=input_data,
        help="Name (with full path) of the input Yaml file of validation variables",
    )
    return vars(parser.parse_args())


# ----------------------------------------------------------------------------
# 1. Import input vars creating host_var of desired state
# ----------------------------------------------------------------------------
def input_task(task: Task, input_data: str, template_task: str) -> str:
    desired_state: Dict[str, Any] = {}
    # Needed incase importing the module
    if "validation_builder" in os.getcwd():
        tmpl_path = os.path.join(os.path.dirname(os.getcwd()), "templates/")
    elif "nornir_validate" in os.getcwd():
        tmpl_path = "templates/"
    else:
        tmpl_path = "nornir_validate/templates/"

    # 1a. LOAD: Load the the input file or change name of the input data variable
    if ".yml" in input_data:
        input_vars = task.run(task=load_yaml, file=input_data).result
    else:
        input_vars = input_data

    # 1b. TMPL: Create the desired_state for each feature to be validated (double 'if' to stop error if top level dict not exist)
    if input_vars.get("hosts") != None:
        if input_vars["hosts"].get(str(task.host)) != None:
            task.run(
                task=template_task,
                tmpl_path=tmpl_path,
                input_vars=input_vars["hosts"][str(task.host)],
                desired_state=desired_state,
            )
    if input_vars.get("groups") != None:
        if input_vars["groups"].get(str(task.host.groups[0])) != None:
            task.run(
                task=template_task,
                tmpl_path=tmpl_path,
                input_vars=input_vars["groups"][str(task.host.groups[0])],
                desired_state=desired_state,
            )

    if input_vars.get("all") != None:
        task.run(
            task=template_task,
            tmpl_path=tmpl_path,
            input_vars=input_vars["all"],
            desired_state=desired_state,
        )

    # 1c. VAR: Create host_var of combined desired states or exits if nothing to be validated
    if len(desired_state) == 0:
        result_text = "\u26A0\uFE0F  No validations were performed as no desired_state was generated, check input file and template"
        return Result(host=task.host, failed=True, result=result_text)
    else:
        task.host["desired_state"] = desired_state


# ----------------------------------------------------------------------------
#  Gets os_type from host_var OS types (platform) and then removes duplicates and None
# ----------------------------------------------------------------------------
def merge_os_types(host):
    tmp_os_type: List = []
    tmp_os_type.append(host.platform)
    tmp_os_type.append(host.get_connection_parameters("scrapli").platform)
    tmp_os_type.append(host.get_connection_parameters("netmiko").platform)
    tmp_os_type.append(host.get_connection_parameters("napalm").platform)
    set_os_type = set(tmp_os_type)
    os_type = list(set_os_type)
    os_type.remove(None)
    os_type.sort()
    return os_type


# ----------------------------------------------------------------------------
# 2. Creates desired state YML from template and serializes it
# ----------------------------------------------------------------------------
def template_task(
    task: Task, tmpl_path: str, input_vars: str, desired_state: Dict[str, Any]
) -> str:
    os_type = merge_os_types(task.host)

    for val_feature, feature_vars in input_vars.items():
        tmp_desired_state = task.run(
            task=template_file,
            template="desired_state.j2",
            path=tmpl_path,
            os_type=os_type,
            feature=val_feature,
            input_vars=feature_vars,
        ).result
        # Converts jinja string into yaml and list of dicts [cmd: {seq: ket:val}] into a dict of cmds {cmd: {seq: key:val}}
        for each_list in yaml.load(tmp_desired_state, Loader=yaml.BaseLoader):
            desired_state.update(each_list)


# ----------------------------------------------------------------------------
# 3. Creates actual state by formatting cmd outputs
# ----------------------------------------------------------------------------
def actual_state_engine(os_type: List, cmd_output: Dict[str, List]) -> Dict[str, Dict]:
    actual_state: Dict[str, Any] = {}

    # Loops through getting command and output from the command
    for cmd, output in cmd_output.items():
        tmp_dict = defaultdict(dict)
        # EMPTY: If output is empty or not formatted (string) just adds an empty dictionary
        if output == None:
            actual_state[cmd] = tmp_dict
        elif len(output) == 0:
            actual_state[cmd] = tmp_dict
        else:
            format_actual_state(os_type, cmd, output, tmp_dict, actual_state)

    return actual_state


# ----------------------------------------------------------------------------
# 4. Formats gathered output as actual state and runs compliance report
# ----------------------------------------------------------------------------
def validate_task(
    task: Task, input_data: str = input_data, directory: str = report_directory
) -> str:
    # 4a. TMPL: Creates desired states using the jinja template
    task.run(
        task=input_task,
        input_data=input_data,
        template_task=template_task,
        severity_level=logging.DEBUG,
    )
    cmd_output = {}
    # 4b. CMD: Using commands from the desired output gathers the actual config form the device
    for each_cmd in task.host["desired_state"]:
        cmd_output[each_cmd] = task.run(
            task=netmiko_send_command,
            command_string=each_cmd,
            use_textfsm=True,
            severity_level=logging.DEBUG,
        ).result
    # 4c. ACTUAL: Formats the returned data into dict of cmds {cmd: {seq: key:val}} same as desired_state
    os_type = merge_os_types(task.host)
    actual_state = actual_state_engine(os_type, cmd_output)
    # 4d. VAL: Uses Napalm_validate validate method to generate a compliance report
    comp_result = report(
        task.host["desired_state"], actual_state, str(task.host), directory
    )
    # 4e. RSLT: Nornir returns compliance result or if fails the compliance report
    return Result(
        host=task.host,
        failed=comp_result["failed"],
        result=comp_result["result"],
        report=comp_result["report"],
        report_text=comp_result["report_text"],
    )


# ----------------------------------------------------------------------------
# Runs the script
# ----------------------------------------------------------------------------
def main():
    args = _create_parser()
    nr = InitNornir(config_file="config.yml")
    result = nr.run(
        task=validate_task, input_data=args["filename"], directory=args["directory"]
    )
    print_result(result, vars=["result", "report_text"])


if __name__ == "__main__":
    main()
