MAPPING_VALUES = {

    "device":{
        "type": "dict",
        "role":{
            "role":"role",
        },
        "device_type":{
            "device_type":"device_type",
        },
        "manufacturer":{
            "manufacturer": "manufacturer"
        },            
        "serial":{
            "serial": "serial"
        },        
        "platform":{
            "platform": "platform"
        },
        "hostname":{
            "hostname":"name"
        },

    },
    "version":{
        "type": "dict",
        "version":{
                "version":"version"
            
        }
    },
    "interfaces":{
        "type": "list",
        "interface":{
            'interface': 'name'
        }
        
    }
}

DISCOVERY_TEMPLATE = {
    'ip' : 'management_ip',
    'version' : 'software_version',
    'interface': 'neighbor_interface',
    'hostname': 'neighbor'

}