import os
import sys
import yaml
import logging
from datetime import datetime
import glob
import difflib
from typing import Any, Dict, List

from rich.console import Console
from rich.theme import Theme
from nornir.core.task import Result

from nornir_rich.functions import print_result
from nornir_utils.plugins.tasks.files import write_file
from nornir_netmiko.tasks import netmiko_send_command

from nornir_orion import orion_inv
from nornir_validate.nr_val import validate_task

# from pathlib import Path
# from nornir_utils.plugins.tasks.data import echo_data

# ----------------------------------------------------------------------------
# VARIABLES: Change any variables such as file location
# ----------------------------------------------------------------------------
working_directory = os.path.dirname(
    __file__
)  # This needs changing to changes folder at work
output_directory = "output"  # store reports and output saved to file
input_directory = "input_files"  # store input files
input_cmd_file = "input_cmd.yml"
input_val_file = "input_val.yml"


# ----------------------------------------------------------------------------
# 1. Addition of input arguments and input file validation
# ----------------------------------------------------------------------------
class InputValidate:
    def __init__(self) -> Dict[str, Any]:
        my_theme = {"repr.ipv4": "none", "repr.number": "none", "repr.call": "none"}
        self.rc = Console(theme=Theme(my_theme))

    # ----------------------------------------------------------------------------
    # 1a. Adds additional arguments to the OrionInventory parser arguments
    # ----------------------------------------------------------------------------
    def add_arg_parser(self, orion) -> Dict[str, Any]:
        args = orion.add_arg_parser()
        #
        args.add_argument(
            "-prt",
            "--print",
            help="Name of change folder directory or direct path to input file",
        )
        args.add_argument(
            "-vtl",
            "--vital_save",
            help="Name of change folder directory where to save files of vital command outputs",
        )
        args.add_argument(
            "-dtl",
            "--detail_save",
            help="Name of change folder directory where to save files of detail command outputs",
        )
        args.add_argument(
            "-val",
            "--validate",
            help="Name of change folder directory where to save compliance report",
        )
        args.add_argument(
            "-cmp",
            "--compare",
            nargs=3,
            help="Name of change folder directory where to find files to compare",
        )
        args.add_argument(
            "-pre",
            "--pre_test",
            help="Name of change folder directory, runs print, vital_save_file and detail_save_file",
        )
        args.add_argument(
            "-pos",
            "--post_test",
            help="Name of change folder directory, runs print, vital_save_file (future compare and validate)",
        )
        return args

    # ----------------------------------------------------------------------------
    # 1b. Checks if change directory and input/ compare files exist
    # ----------------------------------------------------------------------------
    def dir_file_exist(self, run_type: str, run_opt: str) -> Dict[str, Any]:
        # CMP: If it is compare standardise run_opt as it is a list of 3 elements (output_dir & compare files)
        if run_type == "compare":
            cmp_files = run_opt[1:3]
            run_opt = run_opt[0]
            input_filename = "dummy"
        # INPUT_FILE: Sets input file based on if is command checks or validate
        elif run_type == "validate":
            input_filename = input_val_file
        else:
            input_filename = input_cmd_file

        # PRT: If is 'print' and a single input file (not directory) create input & output variable
        if ".yml" in run_opt or ".yaml" in run_opt:
            input_file = run_opt
            output_dir = None
        # DIR: None yaml format means is it is a working directory. Check it exists and create input & output variable
        else:
            working_dir = os.path.join(working_directory, run_opt)
            if not os.path.exists(working_dir):
                self.rc.print(
                    f":x: The '{run_type}' working directory {working_dir} does not exist"
                )
                sys.exit(1)
            else:
                output_dir = os.path.join(working_dir, output_directory)
                input_dir = os.path.join(working_dir, input_directory)
                input_file = os.path.join(input_dir, input_filename)
            # If input (source commands) & output (store comand outputs) directories dont exist create them
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.rc.print(
                    f":white_check_mark: Created the directory [i]{output_dir}[/i]"
                )
            if not os.path.exists(input_dir):
                os.makedirs(input_dir)
                self.rc.print(
                    f":white_check_mark: Created the directory [i]{input_dir}[/i]"
                )

        # FILE_EXIST: If compare files or the input files (cmd or val) dont exist exit
        missing_files = []
        if run_type == "compare":

            cmp_file1 = os.path.join(output_dir, cmp_files[0])
            if not os.path.exists(cmp_file1):
                missing_files.append(cmp_file1)
            cmp_file2 = os.path.join(output_dir, cmp_files[1])
            if not os.path.exists(cmp_file2):
                missing_files.append(cmp_file2)
            result = dict(
                output_dir=output_dir, cmp_file1=cmp_file1, cmp_file2=cmp_file2
            )

        else:
            # INPUT_FILE: Check input file exists and loads and validate contents
            if not os.path.exists(input_file):
                missing_files.append(input_file)
            elif os.path.exists(input_file):
                with open(input_file, "r") as file_content:
                    input_data = yaml.load(file_content, Loader=yaml.FullLoader)
                self.val_input_file(run_type, input_file, input_data)
                result = dict(
                    output_dir=output_dir, input_file=input_file, input_data=input_data
                )

        # ERR_RETURN: If files are missing (input or compare) exists, otherwise returns full path to the files
        if len(missing_files) != 0:
            files = ", ".join(missing_files)
            self.rc.print(f":x: The '{run_type}' file {files} does not exist")
            sys.exit(1)
        else:
            return result

    # ----------------------------------------------------------------------------
    # 1c. Get only the args for differnet run types and from that the get one that is used
    # ----------------------------------------------------------------------------
    def get_run_type(self, args: Dict[str, Any]) -> str:
        run_type, file_path = (None for i in range(2))
        wanted_args = [
            "print",
            "vital_save",
            "detail_save",
            "compare",
            "validate",
            "pre_test",
            "post_test",
        ]
        tmp_args = {k: v for k, v in args.items() if k in wanted_args}
        for k, v in tmp_args.items():
            if v != None:
                run_type = k
                file_path = v
        return run_type, file_path

    # ----------------------------------------------------------------------------
    # 1d. Validates input files contents are of the correct format
    # ----------------------------------------------------------------------------
    def val_input_file(
        self, run_type: str, input_file_path: str, input_data: Dict[str, Any]
    ) -> None:
        if input_data == None:
            self.rc.print(f":x: The '{run_type}' input file {input_file_path} is empty")
            sys.exit(1)
        elif (
            not isinstance(input_data.get("hosts"), dict)
            and not isinstance(input_data.get("groups"), dict)
            and not isinstance(input_data.get("all"), dict)
        ):
            self.rc.print(
                f":x: {input_file_path} must have at least one [i]hosts, groups[/i] or [i]all[/i] dictionary"
            )
            sys.exit(1)


# ----------------------------------------------------------------------------
# 2. Uses nornir to run commands or validation
# ----------------------------------------------------------------------------
class NornirCommands:
    def __init__(self, nr_inv: "nornir"):
        self.nr_inv = nr_inv

    # ----------------------------------------------------------------------------
    # 2a. ORG_CMD: Filters the commands based on the host got from nornir task
    # ----------------------------------------------------------------------------
    def organise_cmds(self, task: "task", input_data: Dict[str, Any]) -> list:
        cmds = dict(print=[], vital=[], detail=[], run_cfg=False)

        # Used to create a dictionary of the commands
        def get_cmds(tmp_input_data: Dict[str, Any]) -> Dict[str, Any]:
            cmds["print"].extend(tmp_input_data.get("cmd_print", []))
            cmds["vital"].extend(tmp_input_data.get("cmd_vital", []))
            cmds["detail"].extend(tmp_input_data.get("cmd_detail", []))

        # If run_cfg is set gathers and saves that first before getting the rest of commands
        if input_data.get("all") != None:
            cmds["run_cfg"] = cmds["run_cfg"] + input_data["all"].get("run_cfg", False)
            get_cmds(input_data["all"])
        if input_data.get("groups") != None:
            for each_grp in input_data["groups"]:
                if each_grp in task.host.groups:
                    grp = input_data["groups"][each_grp]
                    cmds["run_cfg"] = cmds["run_cfg"] + grp.get("run_cfg", False)
                    get_cmds(grp)
        if input_data.get("hosts") != None:
            for each_hst in input_data["hosts"]:
                if (
                    each_hst.lower() == str(task.host).lower()
                    or each_hst.lower() == str(task.host.hostname).lower()
                ):
                    hst = input_data["hosts"][each_hst]
                    cmds["run_cfg"] = cmds["run_cfg"] + hst.get("run_cfg", False)
                    get_cmds(hst)
        if cmds["run_cfg"] == True:
            cmds["run_cfg"] = ["show running-config"]
        return cmds

    # ----------------------------------------------------------------------------
    # RUN_CMD: Runs a list of commands on a device
    # ----------------------------------------------------------------------------
    def run_cmds(self, task: "task", cmd: List, sev_level: "logging") -> str:
        all_output = ""
        for each_cmd in cmd:
            output = "==== " + each_cmd + " " + "=" * (79 - len(each_cmd)) + "\n"
            cmd_output = task.run(
                name=each_cmd,
                task=netmiko_send_command,
                command_string=each_cmd,
                severity_level=sev_level,
            ).result
            all_output = all_output + output + cmd_output + "\n\n\n"
        return all_output

    # ----------------------------------------------------------------------------
    # SAVE_CMD: Saves the contents to file
    # ----------------------------------------------------------------------------
    def save_cmds(
        self, task: "task", run_type: str, data: Dict[str, Any], output: str
    ) -> str:
        output_file = os.path.join(
            data["output_dir"],
            str(task.host)
            + "_"
            + run_type
            + "_"
            + datetime.now().strftime("%Y%m%d-%H%M")
            + ".txt",
        )
        task.run(
            task=write_file,
            filename=output_file,
            content=output,
            severity_level=logging.DEBUG,
        )
        return output_file

    # ----------------------------------------------------------------------------
    # PRINT_CMD: Runs and prints the command outputs to screen
    # ----------------------------------------------------------------------------
    def run_print_cmd(self, task: "task", cmds: List) -> None:
        if len(cmds) != 0:
            self.run_cmds(task, cmds, logging.INFO)

    # ----------------------------------------------------------------------------
    # SAVE_CMD: Runs and saves the command outputs to file
    # ----------------------------------------------------------------------------
    def run_save_cmd(
        self, task: "task", run_type: str, data: Dict[str, Any], cmds: List
    ) -> str:
        if len(cmds) != 0:
            output = self.run_cmds(task, cmds, logging.DEBUG)
            output_file = self.save_cmds(task, run_type, data, output)
            return f"✅ Created command output file '{output_file}'"
        return "empty"

    # ----------------------------------------------------------------------------
    # DIFF: Create HTML diff file from 2 input files
    # ----------------------------------------------------------------------------
    def create_diff(self, data: Dict[str, Any]) -> str:
        pre = open(data["cmp_file1"]).readlines()
        post = open(data["cmp_file2"]).readlines()
        pre_file_name = data["cmp_file1"].split("/")[-1]
        post_file_name = data["cmp_file2"].split("/")[-1]
        file_name = pre_file_name.split("_")[0] + "_diff_" + pre_file_name.split("_")[1]
        output_file = os.path.join(data["output_dir"], file_name + ".html")

        delta = difflib.HtmlDiff().make_file(pre, post, pre_file_name, post_file_name)
        with open(output_file, "w") as f:
            f.write(delta)
        return f"✅ Created compare HTML file '{output_file}'"

    # ----------------------------------------------------------------------------
    # GET_CMP_FILES: Gets last 2 files and compars them
    # ----------------------------------------------------------------------------
    def post_create_diff(self, hostname: str, file_type: str, output_dir: str) -> str:
        file_filter = os.path.join(output_dir, hostname + "_" + file_type + "*")
        files = glob.glob(file_filter)
        files.sort(reverse=True)
        if len(files) >= 2:
            data = dict(output_dir=output_dir, cmp_file1=files[1], cmp_file2=files[0])
            return self.create_diff(data)
        else:
            return f"❌ Only {len(files)} file matched the filter '{file_filter}' for files to be compared"

    # ----------------------------------------------------------------------------
    # 2b. Command engine runs the sub-tasks to get commands and possibly save results to file
    # ----------------------------------------------------------------------------
    def cmd_engine(
        self, task: "task", data: Dict[str, Any], run_type: str
    ) -> "MultiResult":
        result, empty_result = ([] for i in range(2))
        cmds = self.organise_cmds(task, data.get("input_data", {}))

        # RUN_CFG: Saves running config to file
        if cmds["run_cfg"] != False and data["output_dir"] != None:
            result.append(
                self.run_save_cmd(task, "running-config", data, cmds["run_cfg"])
            )
        # PRT: Prints command output to screen
        if run_type == "print":
            self.run_print_cmd(task, cmds["print"])
        # VTL_DTL: Saves vital or detail commands to file
        elif run_type == "vital" or run_type == "detail":
            result.append(self.run_save_cmd(task, run_type, data, cmds[run_type]))
        # CMP: Compares 2 specified files
        elif run_type == "compare":
            result.append(self.create_diff(data))

        # PRE: Prints cmds to screen and saves vital or detail commands to file
        elif run_type == "pre_test":
            self.run_print_cmd(task, cmds["print"])
            result.append(self.run_save_cmd(task, "vital", data, cmds["vital"]))
            result.append(self.run_save_cmd(task, "detail", data, cmds["detail"]))
        # POST: Prints cmds to screen, saves vital commands to file, compares 2 latest vital and run-cfg
        elif run_type == "post_test":
            self.run_print_cmd(task, cmds["print"])
            result.append(self.run_save_cmd(task, "vital", data, cmds["vital"]))
            result.append(
                self.post_create_diff(str(task.host), "vital", data["output_dir"])
            )
            if cmds["run_cfg"] != False:
                result.append(
                    self.post_create_diff(
                        str(task.host), "running-config", data["output_dir"]
                    )
                )

        # RESULT: Prints warning if no commands (for pre and post test) and/or file location for any saved files
        for each_type in ["print", "vital", "detail"]:
            if len(cmds[each_type]) == 0:
                empty_result.append(each_type)
        if cmds["run_cfg"] == False:
            empty_result.append("running-config")
        if len(empty_result) != 0:
            if run_type == "pre_test" or run_type == "post_test":
                empties = ", ".join(list(empty_result))
                result.append(f"⚠️  There were no commands to run for: {empties}")
        if len(result) != 0:
            try:
                result.remove("empty")
                result.remove("empty")
            except:
                pass
            return Result(host=task.host, result="\n".join(result))

    # ----------------------------------------------------------------------------
    # 2c. Task engine to run either run nornir task for commands or validate
    # ----------------------------------------------------------------------------
    def task_engine(self, run_type: str, data: Dict[str, Any]) -> None:
        run_type = run_type.replace("_save", "")
        # Runs the command print or save tasks
        if run_type != "validate":
            result = self.nr_inv.run(
                name=f"{run_type.upper()} command output",
                task=self.cmd_engine,
                data=data,
                run_type=run_type,
            )
        # Runs the validate tasks
        elif run_type == "validate":
            result = self.nr_inv.run(
                task=validate_task,
                input_data=data["input_file"],
                directory=data["output_dir"],
            )
        # Only prints out result if commands commands where run against a device
        if result[list(result.keys())[0]].result != "Nothing run":
            # Adds report information (report_text) if nr_validate has been run
            try:
                result[list(result.keys())[0]].report_text
                print_result(result, vars=["result", "report_text"])
            except:
                print_result(result, vars=["result"])


# ----------------------------------------------------------------------------
# Engine that runs the methods from the script
# ----------------------------------------------------------------------------
def main(inv_settings: str):
    orion = orion_inv.OrionInventory()
    input_val = InputValidate()
    inv_validate = orion_inv.LoadValInventorySettings()

    # 1. Gets info input by user by calling local method that calls remote method
    tmp_args = input_val.add_arg_parser(orion)
    args = vars(tmp_args.parse_args())
    # 2. Load and validates the orion inventory settings, adds any runtime usernames
    inv_settings = inv_validate.load_inv_settings(args, inv_settings)

    # 3a. Tests username and password against orion
    if args.get("npm_user") != None:
        orion.test_npm_creds(inv_settings["npm"])
        # 3b. Initialise Nornir inventory
        nr_inv = orion.load_inventory(inv_settings["npm"], inv_settings["groups"])
    # 3c. Uses static inventory instead of Orion
    elif args.get("npm_user") == None:
        nr_inv = orion.load_static_inventory(
            "inventory/hosts.yml", "inventory/groups.yml"
        )
    # 4. Filter the inventory based on the runtime flags
    nr_inv = orion.filter_inventory(args, nr_inv)
    # 5. add username and password to defaults
    nr_inv = orion.inventory_defaults(nr_inv, inv_settings["device"])

    # 6. Get the run type (flag used) and validate the input file
    run_type, file_path = input_val.get_run_type(args)
    if run_type != None:
        data = input_val.dir_file_exist(run_type, file_path)
    # 7. Run the nornir tasks dependant on the run type (runtime flag)
    nr_cmd = NornirCommands(nr_inv)
    nr_cmd.task_engine(run_type, data)


if __name__ == "__main__":
    main("inv_settings.yml")
