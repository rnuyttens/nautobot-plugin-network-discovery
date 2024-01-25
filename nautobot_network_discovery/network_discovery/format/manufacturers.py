"""information_extract.py"""
import re

from nautobot_network_discovery.network_discovery.mapper.manufacturers import (
    MANUFACTURER_MAP_DICT,
)


def manufacturer(data=None,platform=None):
    """
    Get manufacturer from the dictionnary, Generic by default

    :param Device device: device to analyse

    :returns: None
    """

    for reg,manufacturer in MANUFACTURER_MAP_DICT.items():
        if data is not None and data.get("system_description") is not None and re.match(reg,data.get("system_description").lower()):                        
            return manufacturer
        elif data is not None and data.get("software_version") is not None and re.match(reg,data.get("software_version").lower()):                        
            return manufacturer
        elif data is not None and data.get("platform") is not None and re.match(reg,data.get("platform").lower()):                        
            return manufacturer   
        elif platform is not None and  re.match(reg,platform):    
            return manufacturer
        

    return "Generic"


