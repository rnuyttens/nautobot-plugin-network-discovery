It's a Nautobot jobs for network discovery

For the future:
 - add more logging
 - Comment 
 - Documentation
 - Create Test

Vendor Support:
 - cisco_ios
 - cisco_xe

Experimental/Incomplete Vendor:
 - juniper_junos
 - cisco_wlc_ssh


For install:
 - pip install git+https://github.com/rnuyttens/nautobot-plugin-network-discovery.git

Configuration in nautobot_config.py

 - Mandatory:
    PLUGINS =  ["nautobot_network_discovery"]
 - Optionnal:
    PLUGINS_CONFIG = {
        "nautobot_network_discovery": {
            "default_device_role": "network",
            "default_device_role_color": "ff0000",
            "default_device_status": "Active",
            "default_ip_status": "Active",
            "default_ipam_namespace" : "Global",
            "default_interface_type": "other",
            "create_management_interface_if_missing": True,
            "create_default_platform_per_vendor": False,
            "default_platform_suffix": "default_platform",
            "skip_device_type_on_update": False,
            "skip_manufacturer_on_update": False,
            "update_device_type_if_device_exist":False, 
            "override_network_driver": {
                    "aruba_procurve" : "hp_procurve"
                },
            "object_match_strategy": "loose",
            "deny_role_scan": ["Access Point", "Camera","Phone"]
        }
    }
