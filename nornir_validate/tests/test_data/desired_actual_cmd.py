# These dictionaries are used by test_validations.py to test templated desired_state and formatted actual_state

# --------------------------------------------------------------------------------------
# DESIRED: The desired state after it has been templated and assigned as a host_var
# --------------------------------------------------------------------------------------
desired_state = {
    ## --------------------------------------------------------------------------------------
    ## IOS/IOS-XE: Desired State for IOS/IOS-XE os-type
    ## --------------------------------------------------------------------------------------
    "ios": {
        "show version": {"image": "16.6.2"},
        "show ip access-lists TEST_SSH_ACCESS": {
            "TEST_SSH_ACCESS": {
                "_mode": "strict",
                "10": {
                    "action": "permit",
                    "protocol": "ip",
                    "src": "10.17.10.0/24",
                    "dst": "any",
                },
                "20": {
                    "action": "permit",
                    "protocol": "ip",
                    "src": "10.10.10.10/32",
                    "dst": "any",
                },
                "30": {"action": "deny", "protocol": "ip", "src": "any", "dst": "any"},
            }
        },
        "show etherchannel summary": {
            "Po3": {
                "status": "U",
                "protocol": "LACP",
                "members": {
                    "_mode": "strict",
                    "Gi0/15": {"mbr_status": "P"},
                    "Gi0/16": {"mbr_status": "P"},
                },
            }
        },
        "show ip interface brief": {
            "GigabitEthernet1": {"ip": "10.10.20.102", "status": "up"},
            "GigabitEthernet2": {"ip": "10.20.20.102", "status": "up"},
            "GigabitEthernet3": {"ip": "10.30.20.102", "status": "up"},
        },
        "show cdp neighbors": {
            "Gi0/1": {"Switch01": "Gi0/3"},
            "Gi0/2": {"Switch02": "Gi0/3"},
        },
        "show lldp neighbors": {"Gi2": {"Router01": "Gi0/1"}},
        "show standby brief": {"0": {"priority": "50", "state": "Active"}},
        "show switch": {
            "1": {"priority": "15", "role": "Active", "state": "Ready"},
            "2": {"priority": "14", "role": "Standby", "state": "Ready"},
            "_mode": "strict",
        },
        "show  redundancy state | in state": {
            "my_state": "ACTIVE",
            "peer_state": "STANDBY " "HOT",
        },
        "show interfaces status": {
            "Gi0/0": {
                "duplex": "a-full",
                "speed": "auto",
                "status": "connected",
                "vlan": "routed",
            },
            "Gi0/1": {
                "duplex": "a-full",
                "speed": "auto",
                "status": "suspended",
                "vlan": "20",
            },
            "Gi0/2": {
                "duplex": "a-full",
                "speed": "auto",
                "status": "connected",
                "vlan": "trunk",
            },
            "Po3": {
                "duplex": "auto",
                "speed": "auto",
                "status": "notconnect",
                "vlan": "20",
            },
        },
        "show interfaces switchport": {
            "Gi0/1": {"mode": "access", "vlan": "10"},
            "Gi0/3": {"mode": "trunk", "vlan": "10,20,30"},
        },
        "show vlan brief": {
            "10": {
                "intf": {"_mode": "strict", "list": ["Gi0/1", "Gi0/2"]},
                "name": "vl10",
            },
            "20": {"intf": {"_mode": "strict", "list": ["Lo3"]}, "name": "vl2"},
        },
        "show spanning-tree": {
            "10": {"list": ["Gi0/1", "Gi0/2"]},
            "20": {"list": ["Gi0/3"]},
        },
        "show mac address-table | count dynamic|DYNAMIC": {"total_mac": "1100"},
        "show mac address-table vlan 52 | count dynamic|DYNAMIC": {
            "52_total_mac": "21"
        },
        "show authentication sessions | count mab": {"auth_mab": "21"},
        "show authentication sessions | count dot1x": {"auth_dot1x": "22"},
        "show vrf": {
            "AMB": {"_mode": "strict", "list": ["Gi0/1", "Gi0/2"]},
            "BLU": {"_mode": "strict", "list": ["Lo2"]},
            "GRY": {"_mode": "strict", "list": ["Vl20"]},
        },
        "show ip route  summary | in Total": {"global_subnets": "20"},
        "show ip route vrf BLU summary | in Total": {"BLU_subnets": "113"},
        "show ip  route": {
            "0.0.0.0/0": "10.30.20.1",
            "1.1.1.1/32": "Loopback1",
            "10.30.20.0/24": "GigabitEthernet1",
            "10.30.20.102/32": "GigabitEthernet1",
            "192.168.25.42/32": {"list": ["192.168.14.10", "192.168.14.2"]},
            "21.1.1.1/32": "10.10.10.2",
        },
        "show ip  route vrf BLU": {"0.0.0.0/0": "10.30.20.1"},
        "show ip ospf interface brief": {
            "Gi3": {"area": "0", "cost": "1", "state": "P2P"},
            "_mode": "strict",
        },
        "show ip ospf neighbor": {
            "192.168.255.1": {"state": "FULL"},
            "2.2.2.2": {"state": "FULL"},
            "_mode": "strict",
        },
        "show ip ospf database database-summary | in Total": {"total_lsa": "8"},
        "show ip eigrp interfaces": {
            "intf": {"_mode": "strict", "list": ["Gi3", "Lo1"]}
        },
        "show ip eigrp neighbors": {
            "nbrs": {"_mode": "strict", "list": ["10.10.10.2", "2.2.2.2"]}
        },
        "show bgp all summary": {
            "10.10.10.2": {"asn": "888", "rcv_pfx": "2"},
            "10.10.20.2": {"asn": "889", "rcv_pfx": "3"},
            "_mode": "strict",
        },
        "show nve vni": {
            "10301": {"bdi": "301", "state": "Up", "vrf": "BLU"},
            "10302": {"bdi": "302", "state": "Up", "vrf": "GRN"},
            "_mode": "strict",
        },
        "show nve peers": {
            "10301": {"peer": "192.168.10.10", "state": "UP"},
            "10302": {"peer": "192.168.10.10", "state": "UP"},
            "_mode": "strict",
        },
        "show crypto session brief": {
            "21.16.9.23": {"intf": "Tu10", "status": "UA"},
            "_mode": "strict",
        },
    },
    ## --------------------------------------------------------------------------------------
    ## NXOS: Desired State for NXOS os-type
    ## --------------------------------------------------------------------------------------
    "nxos": {
        "show access-lists TEST_SSH_ACCESS": {
            "TEST_SSH_ACCESS": {
                "20": {
                    "action": "permit",
                    "dst": "any",
                    "protocol": "ip",
                    "src": "10.17.10.0/24",
                },
                "40": {
                    "action": "permit",
                    "dst": "any",
                    "protocol": "ip",
                    "src": "10.10.10.10/32",
                },
                "50": {"action": "deny", "dst": "any", "protocol": "ip", "src": "any"},
                "_mode": "strict",
            }
        },
    },
    ## --------------------------------------------------------------------------------------
    ## ASA: Desired State for ASA os-type
    ## --------------------------------------------------------------------------------------
    "asa": {
        "show run http": {
            "HTTP": {
                "10": {"intf": "mgmt", "src": "10.17.10.0/24"},
                "20": {"intf": "mgmt", "src": "10.10.10.10/32"},
                "30": {"intf": "mgmt", "src": "any"},
                "_mode": "strict",
            }
        },
        "show run ssh": {
            "SSH": {
                "10": {"intf": "mgmt", "src": "10.17.10.0/24"},
                "20": {"intf": "mgmt", "src": "10.10.10.10/32"},
                "30": {"intf": "mgmt", "src": "any"},
                "_mode": "strict",
            }
        },
    },
    "ckp": {},
    "wlc": {},
}

# --------------------------------------------------------------------------------------
# CMD: The command output (textFSM formatted) that is used to format the actual_state
# --------------------------------------------------------------------------------------
cmd_output = {
    ## --------------------------------------------------------------------------------------
    ## IOS/IOS-XE: Command output for IOS/IOS-XE os-type
    ## --------------------------------------------------------------------------------------
    "ios": {
        "show version": [
            {
                "config_register": "0xF",
                "hardware": ["WS-C3560CX-12PC-S"],
                "hostname": "HME-C3560-SWI01",
                "mac": ["CC:7F:75:81:98:00"],
                "reload_reason": "power-on",
                "restarted": "21:53:18 UTC Tue May 17 2022",
                "rommon": "Bootstrap",
                "running_image": "/c3560cx-universalk9-mz.152-7.E2.bin",
                "serial": ["FOC2414L6TJ"],
                "uptime": "2 weeks, 2 days, 18 hours, 28 minutes",
                "uptime_days": "2",
                "uptime_hours": "18",
                "uptime_minutes": "28",
                "uptime_weeks": "2",
                "uptime_years": "",
                "version": "15.2(7)E2",
            }
        ],
        "show ip access-lists TEST_SSH_ACCESS": [
            {"acl_name": "TEST_SSH_ACCESS", "line_num": ""},
            {
                "acl_name": "TEST_SSH_ACCESS",
                "line_num": "10",
                "action": "permit",
                "protocol": "ip",
                "src_any": "",
                "src_network": "10.17.10.0",
                "src_wildcard": "0.0.0.255",
                "dst_any": "any",
            },
            {
                "acl_name": "TEST_SSH_ACCESS",
                "line_num": "20",
                "action": "permit",
                "protocol": "ip",
                "src_host": "10.10.10.10",
                "dst_any": "any",
            },
            {
                "acl_name": "TEST_SSH_ACCESS",
                "line_num": "30",
                "action": "deny",
                "protocol": "ip",
                "src_any": "any",
                "dst_any": "any",
            },
        ],
        "show etherchannel summary": [
            {
                "group": "3",
                "po_name": "Po3",
                "po_status": "SD",
                "protocol": "LACP",
                "interfaces": ["Gi0/15", "Gi0/16"],
                "interfaces_status": ["D", "D"],
            }
        ],
        "show ip interface brief": [
            {
                "intf": "GigabitEthernet0/0",
                "ipaddr": "10.30.20.101",
                "proto": "up",
                "status": "up",
            },
            {
                "intf": "GigabitEthernet0/1",
                "ipaddr": "unassigned",
                "proto": "down",
                "status": "up",
            },
        ],
        "show cdp neighbors": [
            {
                "capability": "R S I",
                "local_interface": "Gig 0/3",
                "neighbor": "Switch",
                "neighbor_interface": "0/3",
                "platform": "Gig",
            }
        ],
        "show lldp neighbors": [
            {
                "capabilities": "R",
                "local_interface": "Gi3",
                "neighbor": "Router",
                "neighbor_interface": "Gi0/3",
            }
        ],
        "show standby brief": [
            {
                "active": "local",
                "group": "0",
                "iface": "Gi0/2",
                "preempt": "P",
                "priority": "50",
                "standby": "unknown",
                "state": "Active",
                "virtualip": "20.20.20.1",
            }
        ],
        "show switch": "Switch/Stack Mac Address : b838.613a.ae80 - Local Mac Address\n"
        "Mac persistency wait time: Indefinite\n"
        "                                             H/W   Current\n"
        "Switch#   Role    Mac Address     Priority Version  State\n"
        "------------------------------------------------------------\n"
        "*1       Active   b838.613a.ae80     15     V01     Ready\n"
        " 2       Standby  b838.613a.7400     14     V01     Ready\n"
        " 3       Member   b838.613a.5800     13     V01     Ready",
        "show  redundancy state | in state": "         my state = 13 -ACTIVE\n"
        "       peer state =  8 -STANDBY HOT",
        "show interfaces status": [
            {
                "duplex": "a-full",
                "fc_mode": "",
                "name": "",
                "port": "Gi0/0",
                "speed": "auto",
                "status": "connected",
                "type": "RJ45",
                "vlan": "routed",
            },
            {
                "duplex": "a-full",
                "fc_mode": "",
                "name": "",
                "port": "Gi0/1",
                "speed": "auto",
                "status": "suspended",
                "type": "RJ45",
                "vlan": "20",
            },
            {
                "duplex": "a-full",
                "fc_mode": "",
                "name": "",
                "port": "Gi0/2",
                "speed": "auto",
                "status": "connected",
                "type": "RJ45",
                "vlan": "trunk",
            },
        ],
        "show interfaces switchport": [
            {
                "access_vlan": "20",
                "admin_mode": "dynamic auto",
                "interface": "Gi0/1",
                "mode": "down (suspended member of bundle " "Po3)",
                "native_vlan": "1",
                "switchport": "Enabled",
                "switchport_monitor": "",
                "switchport_negotiation": "On",
                "trunking_vlans": ["ALL"],
                "voice_vlan": "none",
            },
            {
                "access_vlan": "1",
                "admin_mode": "trunk",
                "interface": "Gi0/3",
                "mode": "trunk",
                "native_vlan": "1",
                "switchport": "Enabled",
                "switchport_monitor": "",
                "switchport_negotiation": "On",
                "trunking_vlans": ["10,20"],
                "voice_vlan": "none",
            },
            {
                "access_vlan": "20",
                "admin_mode": "dynamic auto",
                "interface": "Po3",
                "mode": "down",
                "native_vlan": "0",
                "switchport": "Enabled",
                "switchport_monitor": "",
                "switchport_negotiation": "On",
                "trunking_vlans": ["ALL"],
                "voice_vlan": "none",
            },
        ],
        "show vlan brief": [
            {"interfaces": [], "name": "default", "status": "active", "vlan_id": "1"},
            {"interfaces": [], "name": "test", "status": "active", "vlan_id": "10"},
            {
                "interfaces": ["Gi0/1"],
                "name": "test20",
                "status": "active",
                "vlan_id": "20",
            },
        ],
        "show spanning-tree": [
            {
                "cost": "4",
                "interface": "Gi0/3",
                "port_id": "4",
                "port_priority": "128",
                "role": "Desg",
                "status": "FWD",
                "type": "P2p ",
                "vlan_id": "10",
            },
            {
                "cost": "4",
                "interface": "Gi0/3",
                "port_id": "4",
                "port_priority": "128",
                "role": "Desg",
                "status": "FWD",
                "type": "P2p ",
                "vlan_id": "20",
            },
        ],
        "show mac address-table | count dynamic|DYNAMIC": "Number of lines which match regexp = 1103",
        "show mac address-table vlan 852 | count dynamic|DYNAMIC": "Number of lines which match regexp = 6",
        "show authentication sessions | count mab": "Number of lines which match regexp = 13",
        "show authentication sessions | count dot1x": "Number of lines which match regexp = 21",
        "show vrf": [
            {
                "default_rd": "1:1",
                "interfaces": ["Lo50"],
                "name": "BLU",
                "protocols": "ipv4",
            }
        ],
        "show ip route  summary | in Total": "Total           6           20          0           2288        9956",
        "show ip route vrf BLU summary | in Total": "Total           17          113         0           11232       49320",
        "show ip  route": "Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP\n"
        "       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area \n"
        "       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2\n"
        "       E1 - OSPF external type 1, E2 - OSPF external type 2\n"
        "       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2\n"
        "       ia - IS-IS inter area, * - candidate default, U - per-user static route\n"
        "       o - ODR, P - periodic downloaded static route, H - NHRP, l - LISP\n"
        "       a - application route\n"
        "       + - replicated route, % - next hop override, p - overrides from PfR\n"
        "\n"
        "Gateway of last resort is 10.30.20.1 to network 0.0.0.0\n"
        "\n"
        "S*    0.0.0.0/0 [1/0] via 10.30.20.1\n"
        "      1.0.0.0/32 is subnetted, 1 subnets\n"
        "C        1.1.1.1 is directly connected, Loopback1\n"
        "      2.0.0.0/32 is subnetted, 1 subnets\n"
        "B        2.2.2.2 [20/0] via 10.10.10.2, 04:34:22\n"
        "      4.0.0.0/32 is subnetted, 1 subnets\n"
        "O        4.4.4.4 [110/2] via 10.10.10.2, 04:34:35, GigabitEthernet3\n"
        "      5.0.0.0/32 is subnetted, 1 subnets\n"
        "O IA     5.5.5.5 [110/2] via 10.10.10.2, 04:34:35, GigabitEthernet3\n"
        "      6.0.0.0/32 is subnetted, 1 subnets\n"
        "O E2     6.6.6.6 [110/20] via 10.10.10.2, 04:34:35, GigabitEthernet3\n"
        "      10.0.0.0/8 is variably subnetted, 4 subnets, 2 masks\n"
        "C        10.10.10.0/24 is directly connected, GigabitEthernet3\n"
        "L        10.10.10.1/32 is directly connected, GigabitEthernet3\n"
        "C        10.30.20.0/24 is directly connected, GigabitEthernet1\n"
        "L        10.30.20.102/32 is directly connected, GigabitEthernet1\n"
        "      21.0.0.0/32 is subnetted, 1 subnets\n"
        "D        21.1.1.1 [90/130816] via 10.10.10.2, 03:05:48, GigabitEthernet3\n"
        "      23.0.0.0/32 is subnetted, 1 subnets\n"
        "D EX     23.1.1.1 [170/130816] via 10.10.10.2, 03:05:54, GigabitEthernet3\n"
        "O        192.168.14.4/30\n"
        "        [110/100] via 192.168.14.2, 01:34:45, Port-channel1\n"
        "    192.168.25.0/32 is subnetted, 5 subnets\n"
        "C        192.168.25.41 is directly connected, Loopback1\n"
        "O        192.168.25.42\n"
        "        [110/101] via 192.168.14.10, 23:34:23, GigabitEthernet4\n"
        "        [110/101] via 192.168.14.2, 23:33:52, Port-channel1\n"
        "O        192.168.25.43 [110/51] via 192.168.14.2, 23:42:46, Port-channel1\n"
        "C        192.168.25.45 is directly connected, Loopback2\n"
        "C        192.168.25.47 is directly connected, Loopback3",
        "show ip  route vrf BLU": "\n"
        "Routing Table: BLU\n"
        "Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP\n"
        "       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area \n"
        "       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2\n"
        "       E1 - OSPF external type 1, E2 - OSPF external type 2\n"
        "       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2\n"
        "       ia - IS-IS inter area, * - candidate default, U - per-user static route\n"
        "       o - ODR, P - periodic downloaded static route, H - NHRP, l - LISP\n"
        "       a - application route\n"
        "       + - replicated route, % - next hop override, p - overrides from PfR\n"
        "\n"
        "Gateway of last resort is not set\n"
        "\n"
        "      50.0.0.0/32 is subnetted, 1 subnets\n"
        "C        50.1.1.1 is directly connected, Loopback50\n"
        "B        10.12.1.0/27 [200/1000] via 192.168.12.5, 1w1d\n"
        "                    [200/1000] via 192.168.12.1, 1w1d\n"
        "B        10.12.242.64/28 [200/1000] via 192.168.12.5, 1w1d\n"
        "                        [200/1000] via 192.168.12.1, 1w1d\n"
        "    172.16.0.0/24 is subnetted, 2 subnets\n"
        "B        172.16.10.0 [200/0] via 10.80.10.2, 04:42:57\n"
        "B        172.16.20.0 [200/0] via 10.80.10.2, 04:42:52",
        "show ip ospf interface brief": [
            {
                "area": "0",
                "cost": "1",
                "interface": "Lo7",
                "ip_address_mask": "7.7.7.7/32",
                "neighbors_fc": "0/0",
                "state": "LOOP",
            },
            {
                "area": "0",
                "cost": "1",
                "interface": "Gi3",
                "ip_address_mask": "10.10.10.1/24",
                "neighbors_fc": "1/1",
                "state": "P2P",
            },
            {
                "area": "2",
                "cost": "1",
                "interface": "Lo8",
                "ip_address_mask": "8.8.8.8/32",
                "neighbors_fc": "0/0",
                "state": "LOOP",
            },
        ],
        "show ip ospf neighbor": [
            {
                "address": "192.168.255.1",
                "dead_time": "00:00:35",
                "interface": "Vlan98",
                "neighbor_id": "192.168.255.1",
                "priority": "1",
                "state": "FULL/BDR",
            },
            {
                "address": "2.2.2.2",
                "dead_time": "00:00:31",
                "interface": "Vlan2",
                "neighbor_id": "2.2.2.2",
                "priority": "1",
                "state": "FULL/BDR",
            },
        ],
        "show ip ospf database database-summary | in Total": "  Total         11       0        0       ",
        "show ip eigrp interfaces": "EIGRP-IPv4 Interfaces for AS(1)\n"
        "                              Xmit Queue   PeerQ        Mean   Pacing Time   Multicast    Pending\n"
        "Interface              Peers  Un/Reliable  Un/Reliable  SRTT   Un/Reliable   Flow Timer   Routes\n"
        "Gi3                      1        0/0       0/0           9       0/0           50           0\n"
        "Lo20                     0        0/0       0/0           0       0/0            0           0",
        "show ip eigrp neighbors": [
            {
                "address": "10.10.10.2",
                "as": "1",
                "hold": "11",
                "interface": "Gi3",
                "q_cnt": "0",
                "rto": "100",
                "seq_num": "7",
                "srtt": "9",
                "uptime": "04:49:21",
            }
        ],
        "show bgp all summary": "For address family: IPv4 Unicast\n"
        "BGP router identifier 9.9.9.9, local AS number 65101\n"
        "BGP table version is 3, main routing table version 3\n"
        "2 network entries using 496 bytes of memory\n"
        "2 path entries using 272 bytes of memory\n"
        "2/2 BGP path/bestpath attribute entries using 560 bytes of memory\n"
        "1 BGP AS-PATH entries using 24 bytes of memory\n"
        "0 BGP route-map cache entries using 0 bytes of memory\n"
        "0 BGP filter-list cache entries using 0 bytes of memory\n"
        "BGP using 1352 total bytes of memory\n"
        "BGP activity 2/0 prefixes, 2/0 paths, scan interval 60 secs\n"
        "\n"
        "Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd\n"
        "10.10.10.2      4          888     313     323        3    0    0 04:49:08        1",
        "show nve vni": "Interface  VNI        Multicast-group VNI state  Mode  BD    cfg vrf\n"
        "nve1       10301   N/A             Up         L3CP  301  CLI BLU\n"
        "nve1       10302   N/A             Up         L3CP  302  CLI GRN",
        "show nve peers": "Interface  VNI      Type Peer-IP          RMAC/Num_RTs   eVNI     state flags UP time\n"
        "nve1       10301 L3CP 192.168.1.2   2466.8cd1.5555 10301   UP   A/M 2d10h\n"
        "nve1       10302 L3CP 192.168.1.2   2466.8cd1.5555 10302   UP   A/M 2d10h",
        "show crypto session brief": "Status: A- Active, U - Up, D - Down, I - Idle, S - Standby, N - Negotiating\n"
        "        K - No IKE\n"
        "ivrf = (none)\n"
        "Peer            I/F          Username        Group/Phase1_id          Uptime   Status\n"
        "21.16.9.23  Tu11                         10.211.20.2             10:55:31 UA",
    },
    ## --------------------------------------------------------------------------------------
    ## NXOS: Command output for NXOS os-type
    ## --------------------------------------------------------------------------------------
    "nxos": {
        "show access-lists TEST_SSH_ACCESS": [
            {
                "action": "remark",
                "destination": "VLAN10",
                "modifier": "",
                "name": "TEST_SSH_ACCESS",
                "port": "",
                "protocol": "Access",
                "range": "",
                "sn": "10",
                "source": "-",
            },
            {
                "action": "permit",
                "destination": "any",
                "modifier": "",
                "name": "TEST_SSH_ACCESS",
                "port": "",
                "protocol": "ip",
                "range": "",
                "sn": "20",
                "source": "10.17.10.0/24",
            },
            {
                "action": "remark",
                "destination": "Access",
                "modifier": "",
                "name": "TEST_SSH_ACCESS",
                "port": "",
                "protocol": "MGMT",
                "range": "",
                "sn": "30",
                "source": "Citrix",
            },
            {
                "action": "permit",
                "destination": "any",
                "modifier": "",
                "name": "TEST_SSH_ACCESS",
                "port": "",
                "protocol": "ip",
                "range": "",
                "sn": "40",
                "source": "10.10.10.10/32",
            },
            {
                "action": "deny",
                "destination": "any",
                "modifier": "",
                "name": "TEST_SSH_ACCESS",
                "port": "",
                "protocol": "ip",
                "range": "",
                "sn": "50",
                "source": "any",
            },
        ]
    },
    ### ASA: Command output for IOS/IOS-XE os-type ###
    "asa": {
        "show run http": "http server enable\n"
        "http 0.0.0.0 0.0.0.0 mgmt\n"
        "http 10.17.10.0 255.255.255.0 mgmt\n"
        "http 10.10.10.10 255.255.255.255 mgmt",
        "show run ssh": "ssh stricthostkeycheck\n"
        "ssh 10.17.10.0 255.255.255.0 mgmt\n"
        "ssh 10.10.10.10 255.255.255.255 mgmt\n"
        "ssh 0.0.0.0 0.0.0.0 mgmt\n"
        "ssh timeout 30\n"
        "ssh version 2\n"
        "ssh key-exchange group dh-group1-sha1",
    },
    "ckp": {},
    "wlc": {},
}

# --------------------------------------------------------------------------------------
# ACTUAL: The actual state after it has been formatted by actual_state.py
# --------------------------------------------------------------------------------------
actual_state = {
    ## --------------------------------------------------------------------------------------
    ## IOS/IOS-XE: Actual State for IOS/IOS-XE os-type
    ## --------------------------------------------------------------------------------------
    "ios": {
        "show version": {"image": "15.2(7)E2"},
        "show ip access-lists TEST_SSH_ACCESS": {
            "TEST_SSH_ACCESS": {
                "10": {
                    "action": "permit",
                    "dst": "any",
                    "protocol": "ip",
                    "src": "10.17.10.0/24",
                },
                "20": {
                    "action": "permit",
                    "dst": "any",
                    "protocol": "ip",
                    "src": "10.10.10.10/32",
                },
                "30": {"action": "deny", "dst": "any", "protocol": "ip", "src": "any"},
            }
        },
        "show etherchannel summary": {
            "Po3": {
                "members": {
                    "Gi0/15": {"mbr_status": "D"},
                    "Gi0/16": {"mbr_status": "D"},
                },
                "protocol": "LACP",
                "status": "SD",
            }
        },
        "show ip interface brief": {
            "GigabitEthernet0/0": {"ip": "10.30.20.101", "status": "up"},
            "GigabitEthernet0/1": {"ip": "unassigned", "status": "up"},
        },
        "show cdp neighbors": {"Gig 0/3": {"Switch": "0/3"}},
        "show lldp neighbors": {"Gi3": {"Router": "Gi0/3"}},
        "show standby brief": {"0": {"priority": "50", "state": "Active"}},
        "show switch": {
            "1": {"priority": "15", "role": "Active", "state": "Ready"},
            "2": {"priority": "14", "role": "Standby", "state": "Ready"},
            "3": {"priority": "13", "role": "Member", "state": "Ready"},
        },
        "show  redundancy state | in state": {
            "my_state": "ACTIVE",
            "peer_state": "STANDBY HOT",
        },
        "show interfaces status": {
            "Gi0/0": {
                "duplex": "a-full",
                "speed": "auto",
                "status": "connected",
                "vlan": "routed",
            },
            "Gi0/1": {
                "duplex": "a-full",
                "speed": "auto",
                "status": "suspended",
                "vlan": "20",
            },
            "Gi0/2": {
                "duplex": "a-full",
                "speed": "auto",
                "status": "connected",
                "vlan": "trunk",
            },
        },
        "show interfaces switchport": {
            "Gi0/1": {"mode": "down (suspended member " "of bundle Po3)", "vlan": None},
            "Gi0/3": {"mode": "trunk", "vlan": ["10,20"]},
            "Po3": {"mode": "down", "vlan": None},
        },
        "show vlan brief": {
            "1": {"intf": [], "name": "default"},
            "10": {"intf": [], "name": "test"},
            "20": {"intf": ["Gi0/1"], "name": "test20"},
        },
        "show spanning-tree": {"10": ["Gi0/3"], "20": ["Gi0/3"]},
        "show mac address-table | count dynamic|DYNAMIC": {"total_mac": "1103"},
        "show mac address-table vlan 852 | count dynamic|DYNAMIC": {
            "852_total_mac": "6"
        },
        "show authentication sessions | count mab": {"auth_mab": "13"},
        "show authentication sessions | count dot1x": {"auth_dot1x": "21"},
        "show vrf": {"BLU": ["Lo50"]},
        "show ip route  summary | in Total": {"global_subnets": "20"},
        "show ip route vrf BLU summary | in Total": {"BLU_subnets": "113"},
        "show ip  route": {
            "0.0.0.0/0": "10.30.20.1",
            "1.1.1.1/32": "Loopback1",
            "10.10.10.0/24": "GigabitEthernet3",
            "10.10.10.1/32": "GigabitEthernet3",
            "10.30.20.0/24": "GigabitEthernet1",
            "10.30.20.102/32": "GigabitEthernet1",
            "2.2.2.2/32": "10.10.10.2",
            "21.1.1.1/32": "10.10.10.2",
            "23.1.1.1/32": "10.10.10.2",
            "4.4.4.4/32": "10.10.10.2",
            "5.5.5.5/32": "10.10.10.2",
            "6.6.6.6/32": "10.10.10.2",
            "192.168.14.4/30": "192.168.14.2",
            "192.168.25.41/32": "Loopback1",
            "192.168.25.42/32": ["192.168.14.2", "192.168.14.10"],
            "192.168.25.43/32/32": "192.168.14.2",
            "192.168.25.45": "Loopback2",
            "192.168.25.47": "Loopback3",
        },
        "show ip  route vrf BLU": {
            "50.1.1.1/32": "Loopback50",
            "10.12.1.0/27": ["192.168.12.1", "192.168.12.5"],
            "10.12.242.64/28": ["192.168.12.1", "192.168.12.5"],
            "172.16.10.0/24": "10.80.10.2",
            "172.16.20.0/24": "10.80.10.2",
        },
        "show ip ospf interface brief": {
            "Gi3": {"area": "0", "cost": "1", "state": "P2P"},
            "Lo7": {"area": "0", "cost": "1", "state": "LOOP"},
            "Lo8": {"area": "2", "cost": "1", "state": "LOOP"},
        },
        "show ip ospf neighbor": {
            "192.168.255.1": {"state": "FULL"},
            "2.2.2.2": {"state": "FULL"},
        },
        "show ip ospf database database-summary | in Total": {"total_lsa": "11"},
        "show ip eigrp interfaces": {"intf": ["Gi3", "Lo20"]},
        "show ip eigrp neighbors": {"nbrs": ["10.10.10.2"]},
        "show bgp all summary": {"10.10.10.2": {"asn": "888", "rcv_pfx": "1"}},
        "show nve vni": {
            "10301": {"bdi": "301", "vrf": "BLU", "state": "Up"},
            "10302": {"bdi": "302", "vrf": "GRN", "state": "Up"},
        },
        "show nve peers": {
            "10301": {"peer": "192.168.1.2", "state": "UP"},
            "10302": {"peer": "192.168.1.2", "state": "UP"},
        },
        "show crypto session brief": {"21.16.9.23": {"intf": "Tu11", "status": "UA"}},
    },
    ## --------------------------------------------------------------------------------------
    ## NXOS: Actual State for NXOS os-type
    ## --------------------------------------------------------------------------------------
    "nxos": {
        "show access-lists TEST_SSH_ACCESS": {
            "TEST_SSH_ACCESS": {
                "20": {
                    "action": "permit",
                    "dst": "any",
                    "protocol": "ip",
                    "src": "10.17.10.0/24",
                },
                "40": {
                    "action": "permit",
                    "dst": "any",
                    "protocol": "ip",
                    "src": "10.10.10.10/32",
                },
                "50": {"action": "deny", "dst": "any", "protocol": "ip", "src": "any"},
            }
        }
    },
    ## --------------------------------------------------------------------------------------
    ## ASA: Actual State for ASA os-type
    ## --------------------------------------------------------------------------------------
    "asa": {
        "show run http": {
            "HTTP": {
                "10": {"intf": "mgmt", "src": "any"},
                "20": {"intf": "mgmt", "src": "10.17.10.0/24"},
                "30": {"intf": "mgmt", "src": "10.10.10.10/32"},
            }
        },
        "show run ssh": {
            "SSH": {
                "10": {"intf": "mgmt", "src": "10.17.10.0/24"},
                "20": {"intf": "mgmt", "src": "10.10.10.10/32"},
                "30": {"intf": "mgmt", "src": "any"},
            }
        },
    },
    "ckp": {},
    "wlc": {},
}
