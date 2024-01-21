"""Plugin declaration for nautobot_network_discovery."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

__version__ = metadata.version(__name__)

from nautobot.extras.plugins import NautobotAppConfig


class NautobotNetworkDiscoveryConfig(NautobotAppConfig):
    """Plugin configuration for the nautobot_network_discovery plugin."""

    name = "nautobot_network_discovery"
    verbose_name = "Network Discovery"
    version = __version__
    author = "Raphael NUYTTENS"
    description = "Nautobot App that simplifies device onboarding by collecting and populating common device 'facts' into Nautobot."
    base_url = "nautobot-network-discovery"
    required_settings = []
    min_version = "2.0.0"
    max_version = "2.9999"
    default_settings = {
        "default_device_role": "network",
        "default_device_role_color": "ff0000",
        #"default_management_interface": "PLACEHOLDER",
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
    caching_config = {}





config = NautobotNetworkDiscoveryConfig  # pylint:disable=invalid-name
