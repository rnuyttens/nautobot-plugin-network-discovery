MAPPING_VALUES = {
    "interfaces" : {
        "master_key" : {"name" : "name"},
        "type": "list",
        'function': "interfaces",
        "interface" : {
            'description': 'description',
            'name': 'name',
            'ip_address': 'ip_address',
            'status': 'enabled',
            'mtu_override': 'mtu',
        },
        "physical_interface" : {
            'speed': 'speed',
            'duplex': 'duplex',

        },
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
        "hostname":{
            "hostname":"name",
        },
        "version":{
            "manufacturer": "manufacturer",
            "version" : "device_type",
            "serial_number" : "serial",
            "hostname": "name"
        },
        "platform":{
            "platform": "platform"
        },

    }
}


COMMANDS = {
    "interface": "get system interface",
    "physical_interface": "get system physical",
    "version": "get system status",
}