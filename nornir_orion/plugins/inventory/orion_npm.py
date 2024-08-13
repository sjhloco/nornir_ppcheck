from nornir.core.inventory import (
    Inventory,
    Group,
    Groups,
    Host,
    Hosts,
    Defaults,
    ConnectionOptions,
    HostOrGroup,
    ParentGroups,
)

import logging
from typing import Any, Dict, Union, Optional, Type
from orionsdk import SwisClient
from requests.packages import urllib3
from collections import defaultdict

# Required because of Nornir logging and ConflictingConfigurationWarning
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# CONN_OPT: The connection options created for hosts and groups
# ----------------------------------------------------------------------------
def _get_connection_options(data: Dict[str, Any]) -> Dict[str, ConnectionOptions]:

    cp = {}
    for cn, c in data.items():
        cp[cn] = ConnectionOptions(
            hostname=c.get("hostname"),
            port=c.get("port"),
            username=c.get("username"),
            password=c.get("password"),
            platform=c.get("platform"),
            extras=c.get("extras"),
        )
    return cp


# ----------------------------------------------------------------------------
# CREATE_INV_OBJ:  Creates the Inventory hosts and groups
# ----------------------------------------------------------------------------
def _get_inventory_element(
    typ: Type[HostOrGroup], data: Dict[str, Any], name: str, defaults: Defaults
) -> HostOrGroup:
    return typ(
        name=name,
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        groups=data.get("groups"),
        defaults=defaults,
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


# ----------------------------------------------------------------------------
# The class is the inventory name used to register the inventory (InventoryPluginRegister.register)
# ----------------------------------------------------------------------------
class OrionNpmInventory:
    # Are all optional with a default value as '_verify' method picks up any missing options
    def __init__(
        self,
        npm_server: Optional[str] = None,
        npm_user: Optional[str] = None,
        npm_pword: Optional[str] = None,
        npm_select: Optional[list[str]] = [],
        npm_where: Optional[str] = None,
        ssl_verify: Union[bool, str] = True,
        all_groups: Optional[list[str]] = [],
    ) -> None:
        """
        SELECT and WHERE are SolarWinds Query Language (SWQL) used to query SolarWinds database (FROM hardcoded to Orion.Nodes)
        https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL?language=en_US
        ssl_verify: Disables certificate validation warnings, so if using self-signed and no CA certs
        """

        self.npm_server = npm_server
        self.npm_user = npm_user
        self.npm_pword = npm_pword
        self.npm_select = npm_select
        self.npm_where = npm_where
        self.ssl_verify = ssl_verify
        self.all_groups = all_groups
        self._verify
        self.devices = dict(results=[])

    # ----------------------------------------------------------------------------
    # 1. VERIFY: Notify the user if any of the inventory plugin options are missing
    # ----------------------------------------------------------------------------
    def _verify(self) -> bool:
        for item in [self.npm_server, self.npm_user, self.npm_pword]:
            if item is None:
                raise ValueError(
                    "Plugin options 'server', 'user' or 'pword' are missing, all are required to connect to Orion"
                )
        for item in [self.npm_where]:
            if item is None:
                raise ValueError(
                    "Plugin option 'WHERE' is missing, it is required to filter the Orion SWQL database"
                )
        return True

    # ----------------------------------------------------------------------------
    # 2. GET_ORION: Gathers a list of devices from Orion
    # ----------------------------------------------------------------------------
    def _getdevices_from_orion(self) -> list:
        # 2a. Disables SSL warnings
        if self.ssl_verify == False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # 2b. Removes default values if added by user and converts list of SELECT attributes into a string
        if "Caption" in self.npm_select:
            self.npm_select.remove("Caption")
        if "IPAddress" in self.npm_select:
            self.npm_select.remove("IPAddress")
        if "MachineType" in self.npm_select:
            self.npm_select.remove("MachineType")
        if len(self.npm_select) != 0:
            tmp_npm_select = ", " + ", ".join(self.npm_select)
        # 2c. Creates Orion connection and attempts to get the data using user input options
        conn = SwisClient(self.npm_server, self.npm_user, self.npm_pword)
        api_query = (
            "SELECT Caption, IPAddress, MachineType"
            + tmp_npm_select
            + " FROM Orion.Nodes"
            + " WHERE "
            + self.npm_where
        )
        self.devices = conn.query(api_query)

    # ----------------------------------------------------------------------------
    # 3. SET_TYPE_GROUP: Based on MachineType adds to group (for conn options) and type (for filtering)
    # ----------------------------------------------------------------------------
    def set_type_and_groups(self, each_device: dict, host_attributes: dict) -> dict:
        for each_grp in self.all_groups:
            # Stops errors when fed in filter has only 1 value (like filter=["ASA", None])
            if len(each_grp["filter"]) == 1:
                each_grp["filter"].append(each_grp["filter"][0])
            # 3a. CREATE: Create groups dict and device type for any matching all_groups filters
            filter_obj = each_device.get("MachineType", "")
            dvc_name = each_device.get("Caption", "")
            if (
                each_grp["filter"][0] in filter_obj
                or each_grp["filter"][1] in filter_obj
            ):
                host_attributes["data"]["type"] = each_grp["type"]
                host_attributes["groups"] = [each_grp["group"]]
            # If cant match on name type match on device name
            elif each_grp["filter"][0] in dvc_name or each_grp["filter"][1] in dvc_name:
                host_attributes["data"]["type"] = each_grp["type"]
                host_attributes["groups"] = [each_grp["group"]]
        # 3b. CATCH-ALL: Anything undefined such as cubes or prime
        if host_attributes.get("groups") == None:
            host_attributes["data"]["type"] = "unknown"
            host_attributes["groups"] = ["unknown"]
        return host_attributes

    # ----------------------------------------------------------------------------
    # 4. CREATE_INV: Builds the inventory
    # ----------------------------------------------------------------------------
    def load(self) -> Inventory:
        """Load of Nornir inventory.
        Returns:
            Inventory: Nornir Inventory
        """
        hosts = Hosts()
        groups = Groups()
        defaults = Defaults()

        # 4a. GET DEVICES: Get devices from Orion, failfast if no data returned (no point continuing)
        self._getdevices_from_orion()
        if len(self.devices["results"]) == 0:
            raise ValueError(
                "No data returned from Orion, check your SWQL query is formatted correctly"
            )
        # 4b. HOST: Organise orion data into correct structure and create inventory hosts
        for each_device in self.devices["results"]:
            host_attributes: Dict[Any, Any] = {"data": {}}
            # Sets groups and type dictionaries
            host_attributes = self.set_type_and_groups(each_device, host_attributes)
            # Add IP address got from mandatory default dictionary IPAddress
            host_attributes["hostname"] = each_device["IPAddress"]
            # Creates data dictionary
            for each_obj in self.npm_select:
                tmp_obj = each_obj.split(".")[-1]
                host_attributes["data"][tmp_obj] = each_device[tmp_obj]
            # Create each inventory host by passing data through function
            hosts[each_device["Caption"]] = _get_inventory_element(
                Host, host_attributes, each_device["Caption"], defaults
            )

        # 4c. GROUP: Organise orion data into correct structure and create inventory groups
        for each_grp in self.all_groups:
            group_attributes: Dict[Any, Any] = {"connection_options": defaultdict(dict)}
            # Create default group for each connection plugin, will be empty if undefined
            group_attributes["connection_options"]["scrapli"][
                "platform"
            ] = each_grp.get("scrapli")
            group_attributes["connection_options"]["netmiko"][
                "platform"
            ] = each_grp.get("netmiko")
            group_attributes["connection_options"]["napalm"]["platform"] = each_grp.get(
                "napalm"
            )
            # Creates each inventory group by passing data through function
            groups[each_grp["group"]] = _get_inventory_element(
                Group, group_attributes, each_grp["group"], defaults
            )
        # Create a 'unknown' group that is catchall for anything not categorised (doesn't match all_groups filters)
        groups["unknown"] = _get_inventory_element(Group, {}, "unknown", defaults)

        # 4d. PARENTGROUP: In the inventory groups objects are ParentGroups [Group: name], this changes them into that
        for g in groups.values():
            g.groups = ParentGroups([groups[g] for g in g.groups])
        for h in hosts.values():
            h.groups = ParentGroups([groups[g] for g in h.groups])

        # Return the inventory to Nornir
        return Inventory(hosts=hosts, groups=groups, defaults=defaults)
