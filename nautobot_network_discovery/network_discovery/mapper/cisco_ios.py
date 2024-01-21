MAPPING_VALUES = {
    "interfaces" : {
        "master_key" : {"name" : "interface"},
        "type": "list",
        'function': "interfaces",
        "interface" : {
            'description': 'description',
            'duplex': 'duplex',
            'interface': 'name',
            'ip_address': 'ip_address',
            'link_status': 'enabled',
            'mac_address': 'mac_address',
            'mtu': 'mtu',
            'speed': 'speed',
            'hardware_type': "type"
        },
        "switchport": {
            "mode": "mode",
            "access_vlan": "untagged_vlan",
            "trunking_vlans": "tagged_vlans",
            "native_vlan": "untagged_vlan"
        },
        "ip_interface": {
            "vrf": "vrf"
        },
        "vip" :{
            "virtual_ip": "vip"
        }
    },
    "vlans" : {
        "master_key": {"vid": "vlan_id"},
        "type": "list",
        "vlan" :{
            'vlan_name': 'name', 
            'vlan_id': 'vid'
        }
    },
    "vrfs" : {
        "master_key": {"name": "vrf"},
        "type": "list",
        "vrf" : {
            'description': 'description',
            'default_rd': 'rd',
            'rt_export': 'rt_export',
            'rt_import': 'rt_import',
            'name': 'vrf'
        }
    },
    "version" : {
        "master_key": {"version": "version"},
        "type": "dict",
        "version": 
            {"version": "version"}
    },
    "device":{
        'function': "device",
        "type": "dict",
        "manufacturer":{
            "manufacturer": "manufacturer"
        },
        "role":{
            "role":"role",
        },
        "version":{
            "manufacturer": "manufacturer",
            "hostname":"hostname",
            "hardware" : "device_type",
            "serial" : "serial",
            "hostname": "name"
        },
        "platform":{
            "platform": "platform"
        },

    }
}

COMMANDS = {

    "interface": "show interfaces",
    "vlan": "show vlan",
    "version": "show version",
    "vrf": "show vrf",
    "switchport": "show interface switchport",
    "ip_interface": "show ip interface",
    "vip": "show standby"
    

}

DISCOVERY_CMD={
    "lldp":"show lldp neighbors detail"
}

DISCOVERY_TEMPLATE = {
    'ip' : 'management_ip',
    'version' : 'sw_version',
    'hostname' : "neighbor",
    'interface' : "neighbor_interface",
    "manufacturer" : "manufacturer",
    "device_type": "model",
    "serial":"serial"
}
