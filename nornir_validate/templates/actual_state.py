from typing import Dict, List
import ipaddress
from collections import defaultdict
import re
import ipdb

# ----------------------------------------------------------------------------
# Engine to run different formatters
# ----------------------------------------------------------------------------
def format_actual_state(
    os_type: str,
    cmd: str,
    output: List,
    tmp_dict: Dict[str, None],
    actual_state: Dict[str, None],
) -> Dict[str, Dict]:

    # NO_NTC: Catch all if no NTC template. Either return dummy to not error or converts string to a list
    non_ntc_tmpl_cmds = [
        "show bgp all summary",
        "show run ssh",
        "show run http",
        "show ip ospf database database-summary | in Total",
        "show ip eigrp interfaces",
        "show switch",
        "show  redundancy state | in state",
        "show nve vni",
        "show nve peers",
        "show crypto session brief",
        "show authentication sessions | count mab",
        "show authentication sessions | count dot1x",
    ]
    non_ntc_tmpl_regex_cmds = r"(show ip route .* summary \| in Total)|(show ip  route.*)|(show mac address-table .*)"
    if isinstance(output, str):
        if cmd in non_ntc_tmpl_cmds:
            output = output.lstrip().rstrip().splitlines()
        elif re.match(non_ntc_tmpl_regex_cmds, cmd):
            output = output.lstrip().rstrip().splitlines()
        # All other cmd outputs that are string are ignored to stop errors
        else:
            actual_state[cmd] = defaultdict(dict)
            return actual_state

    if bool(re.search("ios", str(os_type))):
        ios_format(cmd, output, tmp_dict, actual_state)
    elif bool(re.search("nxos", str(os_type))):
        nxos_format(cmd, output, tmp_dict, actual_state)
    elif bool(re.search("asa", str(os_type))):
        asa_format(cmd, output, tmp_dict, actual_state)
    return actual_state


# ----------------------------------------------------------------------------
# Mini-functions used by all OS types to keep DRY
# ----------------------------------------------------------------------------
# ACL_FORMAT: Removes all the empty dictionaries from ACL list of dicts
def acl_format(input_acl: List) -> List:
    acl: List = []
    for each_acl in input_acl:
        tmp_acl = {}
        for ace_key, ace_val in each_acl.items():
            if len(ace_val) != 0:
                tmp_acl[ace_key] = ace_val
        acl.append(tmp_acl)
    return acl


# ACL_ADDR: Converts addressing into address/prefix
def acl_scr_dst(each_ace: Dict[str, str], src_dst: str) -> str:
    if each_ace.get(src_dst + "_network") != None:
        addr = each_ace[src_dst + "_network"] + "/" + each_ace[src_dst + "_wildcard"]
        return ipaddress.IPv4Interface(addr).with_prefixlen
    elif each_ace.get(src_dst + "_host") != None:
        return ipaddress.IPv4Interface(each_ace[src_dst + "_host"]).with_prefixlen
    else:
        return each_ace[src_dst + "_any"]


# REMOVE: Removes the specified character and anything after it
def remove_char(input_data: str, char: str) -> str:
    if char in input_data:
        return input_data.split(char)[0]
    else:
        return input_data


# HOST_RTE: Add /32 to any host routes
def host_route(input_data: str) -> str:
    if "/" not in input_data:
        return input_data + "/32"
    else:
        return input_data


# EDIT_RTE: Used by "add_prefix" to edit route by adding the prefix
def edit_rte(output: List, rte_idx: int, pfx: int) -> None:
    rte = output[rte_idx].split()
    if len(rte) == 6 or len(rte) == 7 or len(rte) == 2:
        rte[1] = rte[1] + "/" + pfx
    elif len(rte) == 3 or len(rte) == 8:
        rte[2] = rte[2] + "/" + pfx
    output[rte_idx] = " ".join(rte)


# ADD_PFX: Adds prefix to subnetted routes in routing table as these show prefix on another line
def add_prefix(output: List) -> List:
    for idx, each_rte in enumerate(output):
        if "is subnetted" in each_rte:
            # Gets the prefix and the number of routes that need it adding
            pfx = each_rte.split()[0].split("/")[1]
            num_rtes = int(each_rte.split()[-2])
            skipped = 0
            # Uses range to call the list index nof route and add prefix to it
            for x in range(1, num_rtes + 1):
                # Bypass any lines with next-hop on new line (counts number of skipped)
                if output[idx + x].split()[0][0] == "[":
                    skipped = skipped + 1
                else:
                    edit_rte(output, idx + x, pfx)
            # If was any skipped lines, has to run again to account for skipped indexes
            if skipped != 0:
                edit_rte(output, idx + x, pfx)
    return output


# ----------------------------------------------------------------------------
# IOS/IOS-XE desired state formatting
# ----------------------------------------------------------------------------
def ios_format(
    cmd: str, output: List, tmp_dict: Dict[str, None], actual_state: Dict[str, None]
) -> Dict[str, Dict]:

    # ----------------------------------------------------------------------------
    # SWI_RTR: Switch and router commands
    # ----------------------------------------------------------------------------
    # IMAGE: show version - {image: code_number}
    if "show version" in cmd:
        if len(output[0]["version"]) == 0:
            tmp_dict["image"] = output[0]["running_image"]
        else:
            tmp_dict["image"] = output[0]["version"]
    # MGMT ACL: show ip access-lists <name> - [{acl_name: {name: seq_num: {protocol: ip/tcp/udp, src: src_ip, dst: dst_ip, dst_port: port}]
    if "show ip access-lists" in cmd:
        acl = acl_format(output)
        tmp_dict1 = defaultdict(dict)
        for each_ace in acl:
            # Creates dict for each ACE entry
            if each_ace.get("line_num") != None:
                tmp_dict1[each_ace["line_num"]]["action"] = each_ace["action"]
                tmp_dict1[each_ace["line_num"]]["protocol"] = each_ace["protocol"]
                tmp_dict1[each_ace["line_num"]]["src"] = acl_scr_dst(each_ace, "src")
                tmp_dict1[each_ace["line_num"]]["dst"] = acl_scr_dst(each_ace, "dst")
                if each_ace.get("dst_port") != None:
                    tmp_dict1[each_ace["line_num"]]["dst_port"] = each_ace["dst_port"]
                elif each_ace.get("icmp_type") != None:
                    tmp_dict1[each_ace["line_num"]]["icmp_type"] = each_ace["icmp_type"]
                tmp_dict[each_ace["acl_name"]] = dict(tmp_dict1)
    # PO: show etherchannel summary - {po_name: {protocol: type, status: code, members: {intf_name: {mbr_status: code}}}}
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
                # For routers as use bndl rather than P
                if mbr_status == "bndl":
                    mbr_status = "P"
                # Creates dict of members to add to as value in the PO dictionary
                po_mbrs[mbr_intf] = {"mbr_status": mbr_status}
            tmp_dict[each_po["po_name"]]["members"] = po_mbrs
    # INTF_L3: show ip interface brief -  {intf: {ip:x, status: x}}
    elif "show ip interface brief" in cmd:
        for each_intf in output:
            tmp_dict[each_intf["intf"]]["ip"] = each_intf["ipaddr"]
            tmp_dict[each_intf["intf"]]["status"] = each_intf["status"]
    # CDP/LLDP: show cdp/lldp neighbors - {intf: {neighbor: neighbor_interface}}
    elif "show cdp neighbors" in cmd or "show lldp neighbors" in cmd:
        for each_nbr in output:
            tmp_dict[each_nbr["local_interface"]] = {
                each_nbr["neighbor"]: each_nbr["neighbor_interface"]
            }
    # HSRP: show standby brief - {group: {state:x, priority: x}}
    elif "show standby brief" in cmd:
        for each_nbr in output:
            tmp_dict[each_nbr["group"]]["state"] = each_nbr["state"]
            tmp_dict[each_nbr["group"]]["priority"] = each_nbr["priority"]

    # ----------------------------------------------------------------------------
    # SWI: Switch-only commands
    # ----------------------------------------------------------------------------
    # SWI_STACK: show switch - {sw_num: {priority: x, role: x, state: x}}
    elif "show switch" in cmd:
        if len(output) >= 6:
            for each_swi in output[5:]:
                if len(each_swi) != 0:
                    tmp_swi = each_swi.split()
                    tmp_dict[tmp_swi[0].replace("*", "")]["role"] = tmp_swi[1]
                    tmp_dict[tmp_swi[0].replace("*", "")]["priority"] = tmp_swi[3]
                    tmp_dict[tmp_swi[0].replace("*", "")]["state"] = tmp_swi[5]
    # VSS_HA: show  redundancy state | in state - {my_state: ACTIVE, peer_state: STANDBY HOT}
    elif "show  redundancy state | in state" in cmd:
        for each_swi in output:
            if len(each_swi) != 0:
                tmp_swi = each_swi.split()
                tmp_dict[tmp_swi[0] + "_" + tmp_swi[1]] = each_swi.split("-")[
                    1
                ].rstrip()
    # INTF_L2: show interfaces status - {intf: {duplex: x, speed: x, status: x, vlan:x }}
    elif "show interfaces status" in cmd:
        for each_intf in output:
            tmp_dict[each_intf["port"]]["duplex"] = each_intf["duplex"]
            tmp_dict[each_intf["port"]]["speed"] = each_intf["speed"]
            tmp_dict[each_intf["port"]]["status"] = each_intf["status"]
            tmp_dict[each_intf["port"]]["vlan"] = each_intf["vlan"]
    # SWITCHPORT: show interfaces switchport - {intf: {mode: access or trunk, vlan: x or [x,y]}}
    elif "show interfaces switchport" in cmd:
        for each_intf in output:
            mode = each_intf["mode"].replace("static ", "")
            tmp_dict[each_intf["interface"]]["mode"] = mode
            if each_intf["mode"] == "static access":
                tmp_dict[each_intf["interface"]]["vlan"] = each_intf["access_vlan"]
            elif each_intf["mode"] == "trunk":
                tmp_dict[each_intf["interface"]]["vlan"] = each_intf["trunking_vlans"]
            else:
                tmp_dict[each_intf["interface"]]["vlan"] = None
    # VLAN: show vlan brief - {vlan: {name: x, intf:[x,y]}}
    elif "show vlan brief" in cmd:
        for each_vl in output:
            tmp_dict[each_vl["vlan_id"]]["name"] = each_vl["name"]
            tmp_dict[each_vl["vlan_id"]]["intf"] = each_vl["interfaces"]
        for each_vl in [1, 1002, 1003, 1004, 1005]:
            if tmp_dict.get(each_vl) != None:
                del tmp_dict[each_vl]
    # STP_VL: show spanning-tree - {vlan: intf:[x,y]}
    elif "show spanning-tree" in cmd:
        tmp_dict = defaultdict(list)
        for each_intf in output:
            if each_intf["status"] == "FWD":
                tmp_dict[each_intf["vlan_id"]].append(each_intf["interface"])
    # ALL_MAC: show mac address-table count | in Dynamic - {total_mac: x}
    elif "show mac address-table | count dynamic|DYNAMIC" in cmd:
        tmp_dict["total_mac"] = output[0].split()[-1]
    # VLAN_MAC: show mac address-table vlan x | count dynamic|DYNAMIC - {vlxxx_mac: x}
    elif "show mac address-table vlan" in cmd:
        vl = cmd.split()[4] + "_total_mac"
        tmp_dict[vl] = output[0].split()[-1]
    # AUTH_MAB: show authentication sessions | count mab - {auth_mab: x}
    elif "show authentication sessions | count mab" in cmd:
        tmp_dict["auth_mab"] = output[0].split()[-1]
    # AUTH_DOT1X: show authentication sessions | count dot1x - {auth_dot1x: x}
    elif "show authentication sessions | count dot1x" in cmd:
        tmp_dict["auth_dot1x"] = output[0].split()[-1]

    # ----------------------------------------------------------------------------
    # RTR: Router-only commands
    # ----------------------------------------------------------------------------
    # VRF: show vrf - {vrf: [intfx, intfy]}
    elif "show vrf" in cmd:
        for each_vrf in output:
            tmp_dict[each_vrf["name"]] = each_vrf["interfaces"]
    # NUM_ROUTES: show ip route  summary | in Total - {total_subnets: x}
    elif re.match(r"show ip route .* summary \| in Total", cmd):
        if len(output) != 0:
            if cmd.split()[4] == "|":
                vrf = "global_subnets"
            else:
                vrf = cmd.split()[4] + "_subnets"
            tmp_dict[vrf] = output[0].split()[2]
    # ROUTES: show ip  route - {route/prefix: next-hop, route/prefix: [next-hop, next-hop]}
    elif re.match("show ip  route.*", cmd):
        tmp_nh = []
        # Function to add prefix to subnetted routes
        output = add_prefix(output)
        # Format the route table output
        for each_rte in reversed(output):
            tmp_rte = each_rte.split()
            # Removes extra route type OSPF (E2, IA) or EIGRP (EX) add to make len of lines same
            if len(tmp_rte) == 8:
                del tmp_rte[1]
            if len(tmp_rte) == 0 or tmp_rte[0] == "Routing":
                pass
            # Catches multiple next-hops or next-hop on new line adds a list which is then used if it is "via"
            elif tmp_rte[0][0] == "[":
                tmp_nh.append(tmp_rte[2].replace(",", ""))
            # Routes and next-hops on same line
            elif "via" in each_rte:
                if len(tmp_nh) == 0:
                    tmp_dict[tmp_rte[1]] = tmp_rte[4].replace(",", "")
                else:
                    tmp_nh.append(tmp_rte[4].replace(",", ""))
                    tmp_dict[tmp_rte[1]] = tmp_nh
                    tmp_nh = []
            # Routes on own line with next hops on separate line (NH caught with "[")
            elif len(tmp_rte) == 2 or len(tmp_rte) == 3:
                # In case only 1 next-hop make it a string
                if len(tmp_nh) == 1:
                    tmp_nh = tmp_nh[0]
                tmp_dict[tmp_rte[1]] = tmp_nh
                tmp_nh = []
            elif "directly" in each_rte:
                tmp_dict[tmp_rte[1]] = tmp_rte[5]

    # OSPF_INTF: show ip ospf interface brief - {intf: {area: x, cost: y, state: z}}
    elif "show ip ospf interface brief" in cmd:
        for each_intf in output:
            tmp_dict[each_intf["interface"]]["area"] = each_intf["area"]
            tmp_dict[each_intf["interface"]]["state"] = each_intf["state"]
            tmp_dict[each_intf["interface"]]["cost"] = each_intf["cost"]
    # OSPF_NBR: show ip ospf neighbor - {nbr_ip: {state: x}}
    elif "show ip ospf neighbor" in cmd:
        for each_nhbr in output:
            tmp_dict[each_nhbr["neighbor_id"]] = {
                "state": remove_char(each_nhbr["state"], "/")
            }
    # OSPF_LSDB: show ip ospf database database-summary | in Total - {total_lsa: x }
    elif "show ip ospf database database-summary | in Total" in cmd:
        if len(output) != None:
            tmp_dict["total_lsa"] = output[0].split()[1]
    # EIGRP_INTF: show ip eigrp interfaces - {intf: [x, y]}
    elif "show ip eigrp interfaces" in cmd:
        tmp_dict = defaultdict(list)
        if len(output) >= 4:
            for each_nbr in output[3:]:
                tmp_dict["intf"].append(each_nbr.split()[0])
    # EIGRP_NBR: show ip eigrp neighbors - {nbrs: [x, y]}
    elif "show ip eigrp neighbors" in cmd:
        tmp_dict = defaultdict(list)
        for each_nbr in output:
            if len(each_nbr) != 0:
                tmp_dict["nbrs"].append(each_nbr["address"])
    # BGP_PEER: show bgp all summary - {peer: {asn:x, rcv_pfx:x}}
    elif "show bgp all summary" in cmd:
        for each_line in output:
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", each_line):
                bgp_peer = each_line.split()
                tmp_dict[bgp_peer[0]]["asn"] = bgp_peer[2]
                tmp_dict[bgp_peer[0]]["rcv_pfx"] = bgp_peer[-1]
    # NVE_INTF: show nve vni - {l3vni: {bdi: x, vrf: z, state: UP}}
    elif "show nve vni" in cmd:
        for each_vni in output[1:]:
            if len(each_vni) != 0:
                tmp_vni = each_vni.split()
                tmp_dict[tmp_vni[1]]["bdi"] = tmp_vni[5]
                tmp_dict[tmp_vni[1]]["vrf"] = tmp_vni[7]
                tmp_dict[tmp_vni[1]]["state"] = tmp_vni[3]
    # NVE_PEERS: show nve peers - {ls_vni: {peer: ip, state: Up}}
    elif "show nve peers" in cmd:
        for each_vni in output[1:]:
            if len(each_vni) != 0:
                tmp_vni = each_vni.split()
                tmp_dict[tmp_vni[1]]["peer"] = tmp_vni[3]
                tmp_dict[tmp_vni[1]]["state"] = tmp_vni[6]
    # VPN: show crypto session brief - {vpn_peer: {intf: x, status: UA}}
    elif "show crypto session brief" in cmd:
        for each_vpn in output[4:]:
            if len(each_vpn) != 0:
                tmp_vpn = each_vpn.split()
                tmp_dict[tmp_vpn[0]]["intf"] = tmp_vpn[1]
                tmp_dict[tmp_vpn[0]]["status"] = tmp_vpn[-1]

    actual_state[cmd] = dict(tmp_dict)
    return actual_state


# ----------------------------------------------------------------------------
# NXOS desired state formatting
# ----------------------------------------------------------------------------
def nxos_format(
    cmd: str, output: List, tmp_dict: Dict[str, None], actual_state: Dict[str, None]
) -> Dict[str, Dict]:
    # MGMT_ACL: Creates ACL dicts in the format [{acl_name: {seq_num: {protocol: ip/tcp/udp, src: src_ip, dst: dst_ip, dst_port: port}]
    if "show access-lists" in cmd:
        acl = acl_format(output)
        tmp_dict1 = defaultdict(dict)
        for each_ace in acl:
            # Creates dict for each ACE entry
            if each_ace.get("action") != "remark":
                tmp_dict1[each_ace["sn"]]["action"] = each_ace["action"]
                tmp_dict1[each_ace["sn"]]["protocol"] = each_ace["protocol"]
                tmp_dict1[each_ace["sn"]]["src"] = each_ace["source"]
                tmp_dict1[each_ace["sn"]]["dst"] = each_ace["destination"]
                if each_ace["protocol"] == "icmp" and each_ace.get("modifier") != None:
                    tmp_dict1[each_ace["sn"]]["icmp_type"] = each_ace["modifier"]
                elif each_ace.get("modifier") != None:
                    tmp_dict1[each_ace["sn"]]["dst_port"] = each_ace["modifier"]
                tmp_dict[each_ace["name"]] = dict(tmp_dict1)
    actual_state[cmd] = dict(tmp_dict)
    return actual_state


# ----------------------------------------------------------------------------
# ASA desired state formatting
# ----------------------------------------------------------------------------
def asa_format(
    cmd: str, output: List, tmp_dict: Dict[str, None], actual_state: Dict[str, None]
) -> Dict[str, Dict]:
    # !!!!!! ADD SAFE GUARD INCASE EMPTY !!!!!
    # MGMT_ACL: Creates SSH and HTTP dicts in the format [{ssh_or_http: {seq_num: {src: src_ip, intf: interface}]
    if "show run ssh" in cmd or "show run http" in cmd:
        tmp_dict1 = defaultdict(dict)
        seq = 10
        for each_ace in output:
            try:
                ip_mask = each_ace.split()[1] + "/" + each_ace.split()[2]
                ip_pfxlen = ipaddress.IPv4Interface(ip_mask).with_prefixlen
                if ip_pfxlen == "0.0.0.0/0":
                    tmp_dict1[str(seq)]["src"] = "any"
                else:
                    tmp_dict1[str(seq)]["src"] = ip_pfxlen
                tmp_dict1[str(seq)]["intf"] = each_ace.split()[3]
                seq = seq + 10
            except:
                pass
        if len(tmp_dict1) != 0:
            tmp_dict[cmd.split()[-1].upper()] = dict(tmp_dict1)

    actual_state[cmd] = dict(tmp_dict)
    return actual_state
