
# [nautobot-plugin-network-discovery]

It's a Nautobot jobs for network discovery, the job connects to the equipment and collects the necessary information (LLDP neighbors, version, interfaces, etc.) then publishes the information in Nautobot
# Post in Nautobot:
- Device:
	- Name
	- Manufacturer
	- Device type
	- Device platform
	- Serial
	- Role
	- Secret Group Association (if the device connection was successful)
	- Version (If **[nautobot-app-device-lifecycle-mgmt](https://github.com/nautobot/nautobot-app-device-lifecycle-mgmt)** is install)
	- Interface:
		- Description
		- Mode (access, tagged or tagged-all)
		- untagged vlan
		- tagged vlan
		- IP Address (No secondary address) 
		- MTU
		- MAC Address
		- VRF



# For the future:

- add more logging
- Comment
- Documentation
- Create Test

# Vendor Support:

- cisco_ios
- cisco_xe

# Experimental/Incomplete Vendor:

- juniper_junos
- cisco_wlc_ssh

# For install:

- pip install git+[https://github.com/rnuyttens/nautobot-plugin-network-discovery.git](https://github.com/rnuyttens/nautobot-plugin-network-discovery.git)

# Configuration in nautobot_config.py

- Mandatory:

```json

PLUGINS = ["nautobot_network_discovery"]

```

- Optionnal:

```json
PLUGINS_CONFIG = {
"nautobot_network_discovery": {
	"default_device_role": "network",
	"default_device_role_color": "ff0000",
	"default_device_status": "Active",
	"default_ip_status": "Active",
	"default_ipam_namespace": "Global",
	"default_interface_type": "other",
	"create_management_interface_if_missing": true,
	"create_default_platform_per_vendor": false,
	"default_platform_suffix": "default_platform",
	"skip_device_type_on_update": false,
	"skip_manufacturer_on_update": false,
	"update_device_type_if_device_exist": false,
	"update_role_if_device_exist" : false,
	"override_network_driver": {
		"aruba_procurve": "hp_procurve"
	},
	"object_match_strategy": "loose",
	"deny_role_scan": [
						"Access Point",
						"Camera",
						"Phone"
					],
	}, 
}
```
