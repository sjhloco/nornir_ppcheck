from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nr_val import validate_task


my_input_data = {
    "groups": {
        "ios": {
            "acl": [
                {
                    "name": "TEST_SSH_ACCESS",
                    "ace": [
                        {"remark": "MGMT Access - VLAN10"},
                        {"permit": "10.17.10.0/24"},
                        {"remark": "Citrix Access"},
                        {"permit": "10.10.10.10/32"},
                        {"deny": "any"},
                    ],
                }
            ]
        }
    }
}


nr = InitNornir(config_file="config.yml")
# result = nr.run(task=validate_task, input_data="my_input_data.yml")
result = nr.run(task=validate_task, input_data=my_input_data)
print_result(result)

# result = nr.run(
#     task=validate_task,
#     input_data=my_input_data,
#     directory="/Users/user1/reports",
# )
# print_result(result)
