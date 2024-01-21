

MAPPING_VALUES = {
    "interfaces" : {
        "master_key" : {"name" : "interface"},
        "type": "list",
        'function': "interfaces",
        "interface" : {
            'description': 'description',
            'interface': 'name',
            'destination': 'ip_address',
            'admin_state': 'enabled',
            'mtu': 'mtu',
            'hardware_type': "type"
        },
    },
    "version" : {
        "master_key": {"junos_version": "version"},
        "type": "dict",
        "version": 
            {"junos_version": "version"}
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
            "name":"hostname",
            "model" : "device_type",
            "serial_number" : "serial",

        },
        "platform":{
            "platform": "platform"
        },

    }
}



COMMANDS = {
    "interface": "show interfaces"
    "version": "show version",


}