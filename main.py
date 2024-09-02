import os
import sys
import yaml
import logging
from datetime import datetime
import glob
import difflib
import getpass
from typing import Any, Optional
from rich.console import Console
from rich.theme import Theme
from nornir.core import Nornir
from nornir.core.task import Result, Task
from nornir_rich.functions import print_result
from nornir_utils.plugins.tasks.files import write_file
from nornir_netmiko.tasks import netmiko_send_command
import nornir_inv


# ----------------------------------------------------------------------------
# VARIABLES: Hardcoded default variables such as file location or username
# ----------------------------------------------------------------------------
working_directory = os.path.dirname(__file__)  # Location of the project folder
inventory: str = "inventory"  # Location of the nornir inventory file
device_user: str = "test_user"  # Default device username
output_folder: str = "output"  # Folder that stores reports and output saved to file
input_cmd_file: str = "input_cmd.yml"  # Commands to be run, is in project folder
# input_val_file: str = "input_val.yml"      # TBD: For future use with nornir_validate


# ----------------------------------------------------------------------------
# 1. Addition of input arguments and input file validation
# ----------------------------------------------------------------------------
class InputValidate:
    def __init__(self, working_directory) -> None:
        my_theme = {"repr.ipv4": "none", "repr.number": "none", "repr.call": "none"}
        self.rc = Console(theme=Theme(my_theme))
        self.working_dir = working_directory

    # ----------------------------------------------------------------------------
    # CHK_DIR: Checks if change directory exists and creates full file paths
    # ----------------------------------------------------------------------------
    def dir_exist_get_paths(self, run_type: str, file_path: str) -> tuple[str, ...]:
        # PRT: If is 'print' and a single input file (not directory) create input & output variable
        if ".yml" in file_path or ".yaml" in file_path:
            input_file = file_path
            working_dir, output_fldr = ("" for i in range(2))
        # DIR: Non-yaml format means is it a working directory. Check for env var and create input & output variable
        else:
            working_dir = os.path.join(
                os.environ.get("WORKING_DIRECTORY", self.working_dir), file_path
            )
            if not os.path.exists(working_dir):
                self.rc.print(
                    f":x: The '{run_type}' working directory {working_dir} does not exist"
                )
                sys.exit(1)
            else:
                output_fldr = os.path.join(working_dir, output_folder)
                input_file = os.path.join(working_dir, input_cmd_file)
            # If output (store command outputs) directories dont exist create it
            if not os.path.exists(output_fldr):
                os.makedirs(output_fldr)
                self.rc.print(
                    f":white_check_mark: Created the folder [i]{output_fldr}[/i]"
                )
        return working_dir, output_fldr, input_file

    # ----------------------------------------------------------------------------
    # ERR_MISS: Errors and exits if files are missing (input or compare)
    # ----------------------------------------------------------------------------
    def err_missing_files(self, run_type: str, missing_files: list) -> None:
        if len(missing_files) != 0:
            files = ", ".join(missing_files)
            self.rc.print(f":x: The '{run_type}' file {files} does not exist")
            sys.exit(1)

    # ----------------------------------------------------------------------------
    # INPUT_FILE: Validates input files contents are of the correct format
    # ----------------------------------------------------------------------------
    def val_input_file(
        self, run_type: str, input_file: str, input_data: dict[str, Any]
    ) -> None:
        if input_data == None:
            self.rc.print(f":x: The '{run_type}' input file {input_file} is empty")
            sys.exit(1)
        elif (
            not isinstance(input_data.get("hosts"), dict)
            and not isinstance(input_data.get("groups"), dict)
            and not isinstance(input_data.get("all"), dict)
        ):
            self.rc.print(
                f":x: {input_file} must have at least one [i]hosts, groups[/i] or [i]all[/i] dictionary"
            )
            sys.exit(1)

    # ----------------------------------------------------------------------------
    # 1a. Adds additional arguments to the Nornir Inventory parser arguments
    # ----------------------------------------------------------------------------
    def add_arg_parser(self, nr_inv_args) -> dict[str, Any]:
        args = nr_inv_args.add_arg_parser()
        args.add_argument(
            "-u",
            "--username",
            help="Device username, overrides environment variables and hardcoded script variable",
        )
        args.add_argument(
            "-prt",
            "--print",
            help="Name of change directory or direct path to input file",
        )
        args.add_argument(
            "-vtl",
            "--vital_save",
            help="Name of change directory where to save files created from vital command outputs",
        )
        args.add_argument(
            "-dtl",
            "--detail_save",
            help="Name of change directory where to save files created from detail command outputs",
        )
        # TBD: For future use with nornir_validate
        # args.add_argument(
        #     "-val",
        #     "--validate",
        #     help="Name of change folder directory where to save compliance report",
        # )
        args.add_argument(
            "-cmp",
            "--compare",
            nargs=3,
            help="Name of directory that holds compare files (where compare output is saved) as well the name of the files to compare",
        )
        args.add_argument(
            "-pre",
            "--pre_test",
            help="Name of change directory, runs print, vital_save_file and detail_save_file",
        )
        args.add_argument(
            "-pos",
            "--post_test",
            help="Name of change directory, runs print, vital_save_file and compare (of vital)",
        )
        return args

    # ----------------------------------------------------------------------------
    # 1b. Gathers username/password checking various input options
    # ----------------------------------------------------------------------------
    def get_user_pass(self, args: dict[str, Any]) -> dict[str, str]:
        # USER: Check for username in this order: args, env var, var, prompt
        device = {}
        if args.get("username") != None:
            device["user"] = args["username"]
        elif os.environ.get("DEVICE_USER") != None:
            device["user"] = os.environ["DEVICE_USER"]
        elif device_user != None:
            device["user"] = device_user
        else:
            device["user"] = input("Enter device username: ")
        # PWORD: Check for password in thid order: env var, prompt
        if os.environ.get("DEVICE_PWORD") != None:
            device["pword"] = os.environ["DEVICE_PWORD"]
        else:
            device["pword"] = getpass.getpass("Enter device password: ")
        return device

    # ----------------------------------------------------------------------------
    # 1c. Get only the args for different run types and from that the get one that is used
    # ----------------------------------------------------------------------------
    def get_run_type(self, args: dict[str, Any]) -> tuple[str | None, str | None]:
        run_type, file_path = (None for i in range(2))
        wanted_args = [
            "print",
            "vital_save",
            "detail_save",
            "compare",
            # "validate",
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
    # 1d. If compare arg validates all the files exist (a list of 3 elements, output_fldr & 2 compare files)
    # ----------------------------------------------------------------------------
    def val_compare_arg(self, run_type: str, file_path: list) -> dict[str, Any]:
        missing_files = []
        # DIR: Check that output dir exists and get full file path
        working_dir, output_fldr, z = self.dir_exist_get_paths(run_type, file_path[0])
        # FILE: Check that compare files exist
        cmp_file1 = os.path.join(working_dir, file_path[1])
        if not os.path.exists(cmp_file1):
            missing_files.append(cmp_file1)
        cmp_file2 = os.path.join(working_dir, file_path[2])
        if not os.path.exists(cmp_file2):
            missing_files.append(cmp_file2)
        # ERR/RTR: Errors or returns file paths based on whether exist or not
        self.err_missing_files(run_type, missing_files)
        return dict(output_fldr=output_fldr, cmp_file1=cmp_file1, cmp_file2=cmp_file2)

    # ----------------------------------------------------------------------------
    # 1e. Validates input command file exists and contents are of the correct format
    # ----------------------------------------------------------------------------
    def val_noncompare_arg(self, run_type: str, file_path: str) -> dict[str, Any]:
        # DIR: Check that output dir exists and get full file path
        z, output_fldr, input_file = self.dir_exist_get_paths(run_type, file_path)
        # FILE: Check input file exists and loads and validate contents
        if not os.path.exists(input_file):
            self.err_missing_files(run_type, [input_file])
        elif os.path.exists(input_file):
            with open(input_file, "r") as file_content:
                input_data = yaml.load(file_content, Loader=yaml.FullLoader)
            # ERR/RTR: Errors or returns file paths based on whether input file correctly formatted
            self.val_input_file(run_type, input_file, input_data)
        return dict(
            output_fldr=output_fldr, input_file=input_file, input_data=input_data
        )


# ----------------------------------------------------------------------------
# 2. Uses nornir to run commands
# ----------------------------------------------------------------------------
class NornirCommands:
    def __init__(self, task: Task) -> None:
        self.task = task

    # ----------------------------------------------------------------------------
    # CMDS: Creates a dictionary of the commands
    # ----------------------------------------------------------------------------
    def get_cmds(self, cmds, input_data: dict[str, Any]) -> None:
        cmds["run_cfg"] = cmds["run_cfg"] + input_data.get("run_cfg", False)
        cmds["print"].extend(input_data.get("cmd_print", []))
        cmds["vital"].extend(input_data.get("cmd_vital", []))
        cmds["detail"].extend(input_data.get("cmd_detail", []))
        self.cmds = cmds  # Needed so can unittest this method as no return

    # ----------------------------------------------------------------------------
    # ORG_CMD: Filters the commands based on the host got from nornir task
    # ----------------------------------------------------------------------------
    def organise_cmds(self, input_data: dict[str, Any]) -> dict[str, Any]:
        cmds = dict(print=[], vital=[], detail=[], run_cfg=False)
        # If run_cfg is set gathers and saves that first before getting the rest of commands
        if input_data.get("all") != None:
            self.get_cmds(cmds, input_data["all"])
        if input_data.get("groups") != None:
            for each_grp in input_data["groups"]:
                if each_grp in self.task.host.groups:
                    self.get_cmds(cmds, input_data["groups"][each_grp])
        if input_data.get("hosts") != None:
            for each_hst in input_data["hosts"]:
                if (
                    each_hst.lower() == str(self.task.host).lower()
                    or each_hst.lower() == str(self.task.host.hostname).lower()
                ):
                    self.get_cmds(cmds, input_data["hosts"][each_hst])
        if cmds["run_cfg"] == True:
            cmds["run_cfg"] = ["show running-config"]
        return cmds

    # ----------------------------------------------------------------------------
    # RUN_CMD: Runs a nornir task that executes a list of commands on a device
    # ----------------------------------------------------------------------------
    def run_cmds(self, cmd: list, sev_level: int) -> str:
        all_output = ""
        for each_cmd in cmd:
            output = "==== " + each_cmd + " " + "=" * (79 - len(each_cmd)) + "\n"
            cmd_output = self.task.run(
                name=each_cmd,
                task=netmiko_send_command,
                command_string=each_cmd,
                severity_level=sev_level,
            ).result
            all_output = all_output + output + cmd_output + "\n\n\n"
        return all_output

    # ----------------------------------------------------------------------------
    # SAVE_CMD: Runs a nornir task to save cmd output (gathered by diff method) to file
    # ----------------------------------------------------------------------------
    def save_cmds(self, run_type: str, data: dict[str, Any], output: str) -> str:
        date = datetime.now().strftime("%Y%m%d-%H%M")
        file_name = str(self.task.host) + "_" + run_type + "_" + date + ".txt"
        output_file = os.path.join(data["output_fldr"], file_name)
        self.task.run(
            task=write_file,
            filename=output_file,
            content=output,
            severity_level=logging.DEBUG,
        )
        return output_file

    # ----------------------------------------------------------------------------
    # PRINT_CMD: Runs and prints the command outputs to screen
    # ----------------------------------------------------------------------------
    def run_print_cmd(self, cmds: list) -> None:
        if len(cmds) != 0:
            self.run_cmds(cmds, logging.INFO)

    # ----------------------------------------------------------------------------
    # SAVE_CMD: Uses separate methods to runs and save the command outputs to file
    # ----------------------------------------------------------------------------
    def run_save_cmd(self, run_type: str, data: dict[str, Any], cmds: list) -> str:
        if len(cmds) != 0:
            output = self.run_cmds(cmds, logging.DEBUG)
            output_file = self.save_cmds(run_type, data, output)
            return f"✅ Created command output file '{output_file}'"
        return "empty"

    # ----------------------------------------------------------------------------
    # DIFF: Create HTML diff file from 2 input files
    # ----------------------------------------------------------------------------
    def create_diff(self, data: dict[str, Any]) -> str:
        # Create file names and load compare files
        pre_file_name = data["cmp_file1"].split("/")[-1]
        post_file_name = data["cmp_file2"].split("/")[-1]
        output_file = os.path.join(
            data["output_fldr"],
            pre_file_name.split("_")[0]
            + "_diff_"
            + pre_file_name.split("_")[1].replace(".txt", "")
            + ".html",
        )
        pre = open(data["cmp_file1"]).readlines()
        post = open(data["cmp_file2"]).readlines()
        # Create diff html page with a reduced font size in the html table
        diff = difflib.HtmlDiff().make_file(pre, post, pre_file_name, post_file_name)
        diff_font = diff.replace("   <tbody>", '   <tbody style="font-size:12px">')
        with open(output_file, "w") as f:
            f.write(diff_font)
        return f"✅ Created compare HTML file '{output_file}'"

    # ----------------------------------------------------------------------------
    # POST_DIFF: Gets last 2 files and compares them
    # ----------------------------------------------------------------------------
    def pos_create_diff(self, file_type: str, output_fldr: str) -> str:
        hostname = str(self.task.host)
        file_filter = os.path.join(output_fldr, hostname + "_" + file_type + "*")
        # Uses glob to match file names using a filter, then selects last 2 (most recent) to compare
        files = glob.glob(file_filter)
        files.sort(reverse=True)
        if len(files) >= 2:
            data = dict(output_fldr=output_fldr, cmp_file1=files[1], cmp_file2=files[0])
            return self.create_diff(data)
        else:
            return f"❌ Only {len(files)} file matched the filter '{file_filter}' for files to be compared"


# ----------------------------------------------------------------------------
# 3. Uses nornir to run commands
# ----------------------------------------------------------------------------
class NornirEngine:
    def __init__(self, nr_inv: Nornir) -> None:
        self.nr_inv = nr_inv

    # ----------------------------------------------------------------------------
    # 2b. Command engine runs the sub-tasks to get commands and possibly save results to file
    # ----------------------------------------------------------------------------
    def cmd_engine(
        self, task: Task, data: dict[str, Any], run_type: str
    ) -> Optional[Result]:
        self.nr_cmd = NornirCommands(task)

        # ORG_CMD: Organises cmds to be run and also creates empty lists to store results
        result, empty_result = ([] for i in range(2))
        cmds = self.nr_cmd.organise_cmds(data.get("input_data", {}))

        # RUN_CFG: Saves running config to file
        if cmds["run_cfg"] != False and data["output_fldr"] != None:
            result.append(self.nr_cmd.run_save_cmd("config", data, cmds["run_cfg"]))
        # PRT: Prints command output to screen
        if run_type == "print":
            self.nr_cmd.run_print_cmd(cmds["print"])
        # VTL_DTL: Saves vital or detail commands to file
        elif run_type == "vital" or run_type == "detail":
            result.append(self.nr_cmd.run_save_cmd(run_type, data, cmds[run_type]))
        # CMP: Compares 2 specified files
        elif run_type == "compare":
            result.append(self.nr_cmd.create_diff(data))

        # PRE/POST: Prints cmds to screen and saves vital commands to file
        else:
            self.nr_cmd.run_print_cmd(cmds["print"])
            result.append(self.nr_cmd.run_save_cmd("vital", data, cmds["vital"]))
            # PRE: saves vital commands to file
            if run_type == "pre_test":
                result.append(self.nr_cmd.run_save_cmd("detail", data, cmds["detail"]))
            # POST: Compares 2 latest vital and config
            elif run_type == "post_test":
                result.append(self.nr_cmd.pos_create_diff("vital", data["output_fldr"]))
                if cmds["run_cfg"] != False:
                    result.append(
                        self.nr_cmd.pos_create_diff("config", data["output_fldr"])
                    )

        # RESULT: Prints warning if no commands (for pre and post test) and/or file location for any saved files
        for each_type in ["print", "vital", "detail"]:
            if len(cmds[each_type]) == 0:
                empty_result.append(each_type)
        if cmds["run_cfg"] == False:
            empty_result.append("config")
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
        else:
            return None

    # ----------------------------------------------------------------------------
    # 2c. Task engine to run nornir task for commands and prints result
    # ----------------------------------------------------------------------------
    def task_engine(self, run_type: str, data: dict[str, Any]) -> None:
        run_type = run_type.replace("_save", "")
        # The parent nornir task in which the cmd_engine tuns the nornir sub-tasks
        if run_type != "validate":
            result = self.nr_inv.run(
                name=f"{run_type.upper()} command output",
                task=self.cmd_engine,
                data=data,
                run_type=run_type,
            )
        # TBD: For future use with nornir_validate
        # elif run_type == "validate":
        #     result = self.nr_inv.run(
        #         task=validate_task,
        #         input_data=data["input_file"],
        #         directory=data["output_fldr"],
        #     )
        # Only prints out result if commands where run against a device
        if result[list(result.keys())[0]].result != "Nothing run":
            # Adds report information (report_text) if nr_validate has been run
            try:
                result[list(result.keys())[0]].report_text
                print_result(result, vars=["result", "report_text"])
            except:
                print_result(result, vars=["result"])
                # Incase want to use orig nornir_print, dont use as doesnt delete empty results when run with prt flag
                # print_result(result, vars=["result"], line_breaks=True)


# ----------------------------------------------------------------------------
# Engine that runs the methods from the script
# ----------------------------------------------------------------------------
def main():
    build_inv = nornir_inv.BuildInventory()  # parsers in nor_inv script
    input_val = InputValidate(working_directory)  # parsers & val in this file

    # 1. Gets info input by user by calling local method that calls remote nor_inv method
    tmp_args = input_val.add_arg_parser(build_inv)
    args = vars(tmp_args.parse_args())

    # 2. Get the run type (flag used)
    run_type, file_path = input_val.get_run_type(args)

    # 3a. CMP: Validate directories and files exist, doesn't need device creds
    if run_type == "compare":
        data = input_val.val_compare_arg(run_type, file_path)
        device = dict(user=None, pword=None)
        # 3b. OTHER: Validates the input file exists, is correct format and gets device creds
    elif run_type != None:
        data = input_val.val_noncompare_arg(run_type, file_path)
        device = input_val.get_user_pass(args)

    # 4. Loads inventory using static host and group files (checks first if location changed with env vars)
    nr_inv = build_inv.load_inventory(
        os.path.join(os.environ.get("INVENTORY", inventory), "hosts.yml"),
        os.path.join(os.environ.get("INVENTORY", inventory), "groups.yml"),
    )

    # 5. Filter the inventory based on the runtime flags and add creds to Nornir inventory defaults
    nr_inv = build_inv.filter_inventory(args, nr_inv)
    nr_inv = build_inv.inventory_defaults(nr_inv, device)

    # 6. Run the nornir tasks dependant on the run type (runtime flag)
    nr_eng = NornirEngine(nr_inv)
    nr_eng.task_engine(run_type, data)


if __name__ == "__main__":
    main()
