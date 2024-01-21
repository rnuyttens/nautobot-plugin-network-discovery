

MAPPING_VALUES = {
    "version" : {
        "master_key": {"product_version": "version"},
        "type": "dict",
        "version": 
            {"product_version": "version"}
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
        "inventory":{
            "name":"hostname",
            "pid" : "device_type",
            "sn" : "serial",
        },
        "platform":{
            "platform": "platform"
        },

    }
}



COMMANDS = {

    "inventory": "show inventory",
    "version": "show sysinfo",


}