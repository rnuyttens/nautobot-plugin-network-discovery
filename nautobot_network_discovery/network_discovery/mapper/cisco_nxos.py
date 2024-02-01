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
    },
    "version" : {
        "master_key": {"os": "version"},
        "type": "dict",
        "version": 
            {"os": "version"}
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
        "hostname":{
            "hostname":"name",
        },
        "version":{
            "platform" : "device_type",
            "serial" : "serial",
            "hostname": "name"
        },
        "platform":{
            "platform": "platform"
        },
    }
}

COMMANDS = {
    "version": "show version",
    "interface":" show interface"
}

