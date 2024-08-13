from typing import Any, Dict
from napalm.base import validate
from napalm.base.exceptions import ValidationException
import json
import os
import re
from datetime import datetime

# ----------------------------------------------------------------------------
# FIX: napalm_validate doesn't recognize ~/ for home drive
# ----------------------------------------------------------------------------
def fix_home_path(input_path: str) -> str:
    if re.match("^~/", input_path):
        return os.path.expanduser(input_path)
    else:
        return input_path


# -------------------------------------------------------------------------------------------
# REPORT_FILE: If a hostname and directory are passed in as function arguments saves report to file
# --------------------------------------------------------------------------------------------
def report_file(
    hostname: str, directory: str, report: Dict[str, Any], complies: bool, skipped: bool
):
    filename = os.path.join(
        fix_home_path(directory),
        hostname
        + "_compliance_report_"
        + datetime.now().strftime("%Y%m%d-%H%M")
        + ".json",
    )
    # If report file already exists conditionally updates 'skipped' and 'complies' with report outcome
    if os.path.exists(filename):
        with open(filename, "r") as file_content:
            existing_report = json.load(file_content)
        if list(report.values())[0].get("skipped"):
            existing_report["skipped"].extend(skipped)
        # Only adds if is no already failing compliance
        if existing_report.get("complies") == True:
            existing_report["complies"] = complies
    # If creating a new report file adds 'complies' and 'skipped' with report outcome
    else:
        existing_report = {}
        existing_report["complies"] = complies
        existing_report["skipped"] = skipped
    # Writes to file the full napalm_validate result (including an existing report)
    existing_report.update(report)
    with open(filename, "w") as file_content:
        json.dump(existing_report, file_content)
    # return f" The report can be viewed using:  \n \33[3m\033[1;37m\33[30m cat {filename} | python -m json.tool \033[0;0m"
    return f" The report can be viewed using:\ncat {filename} | python -m json.tool"


# ----------------------------------------------------------------------------------------------------------
# VALIDATE: Uses naplam_validate on custom data fed in (still supports '_mode: strict') to validate and create reports
# ----------------------------------------------------------------------------------------------------------
def report(
    desired_state: Dict[str, Dict],
    actual_state: Dict[str, Dict],
    hostname: str,
    directory: str,
):
    report: Dict[str, Any] = {}
    for cmd, desired_results in desired_state.items():
        # Safe guard in case any empty desired_results, stops script failing
        if desired_results == None:
            pass
        else:
            # napalm_validate compare method produces report based on desired and actual state
            try:
                report[cmd] = validate.compare(desired_results, actual_state[cmd])
            # If validation couldn't be run on a command adds skipped key to the cmd dictionary
            except NotImplementedError:
                report[cmd] = {"skipped": True, "reason": "NotImplemented"}
    # RESULT: Results of compliance report (complies = validation result, skipped (list of skipped cmds) = validation didn't run)
    complies = all([each_cmpl.get("complies", True) for each_cmpl in report.values()])
    skipped = [cmd for cmd, output in report.items() if output.get("skipped", False)]

    # REPORT_FILE: Save report to file, if not add complies and skipped dictionary to report
    if hostname != None and directory != None:
        report_text = report_file(hostname, directory, report, complies, skipped)
    else:
        report_text = ""  # Empty value if report_file not created
    # These must be added after the report
    report["complies"] = complies
    report["skipped"] = skipped
    # RETURN_RESULT: If compliance fails set state failed (used by Nornir). report dict is used in validation builder
    if complies == True:
        return dict(
            failed=False,
            result="\u2705 Validation report complies, desired_state and actual_state match.",
            report=report,
            report_text=report_text,
        )
    if complies == False or skipped == True:
        return dict(failed=True, result=report, report=report, report_text=report_text)
