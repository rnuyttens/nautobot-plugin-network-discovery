"""information_extract.py"""
import re

from nautobot_network_discovery.network_discovery.mapper.manufacturers import (
    MANUFACTURER_MAP_DICT,
)


def device_type(data):
    """
    Get device_type from the dictionnary, Generic by default

    :param Device device: device to analyse

    :returns: None
    """
    for d in data:
        if d.get("hardware") is not None :
            if isinstance(d.get("hardware"), list):
                d["hardware"] = d.get("hardware")[0]

    return data



def manufacturer(data=None):
    """
    Get manufacturer from the dictionnary, Generic by default

    :param Device device: device to analyse

    :returns: None
    """
    found = False
    for d in data :
        for reg,manufacturer in MANUFACTURER_MAP_DICT.items():
            if d.get("system_description") is not None and re.match(reg,d.get("system_description").lower()):                        
                d['manufacturer']=manufacturer
                found=True
                break
            elif d.get("software_version") is not None and re.match(reg,d.get("software_version").lower()):                        
                d['manufacturer']=manufacturer
                True
                break
            elif d.get("platform") is not None and re.match(reg,d.get("platform").lower()):                        
                d['manufacturer']=manufacturer  
                found=True
                break

    
    return data


def run(data):
    data = device_type(data)
    data = manufacturer(data)
    return data