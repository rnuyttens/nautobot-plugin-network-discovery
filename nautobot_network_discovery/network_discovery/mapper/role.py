ROLE_MAP_DICT = {
    "capabilities": {
                "Host Phone":"Phone",
                "Host Phone two-port mac relay":"Phone",
                "Host":"Host",
                "trans-Bridge source-route-Bridge igmp":"Bridge",
                "router trans-Bridge":"Bridge",
                "router":"Router",
                "router switch igmp":"Router-Switch",
                "router igmp":"Router",
                "switch igmp":"Switch",
                "switch igmp cvta Phone port":"Switch",
                "r":"router",
                "t":"Phone",
                "c":"cable",
                "w":"WLAN",
                "p":"repeater",
                "s":"station",
                "o":"Other",
                "b":"Bridge"
            },
    "regex":    {
            ".*vmware esx.*":"Host vSphere",
            ".*vmware.*":"VM",
            ".*c9120.*":"Access Point",
            ".*air-cap.*":"Access Point",
            ".*ucs.*":"Server",
            ".*firewall.*":"Firewall",
            ".*camera.*" : "Camera",
            ".*ap software.*": "Access Point",
            ".*ip phone.*": "Phone",
            ".*ap3g.*": "Access Point"
            }
}
