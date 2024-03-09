"""information_extract.py"""

import re

from nautobot_network_discovery.network_discovery.mapper.role import ROLE_MAP_DICT


def role(lldp_data):
    """
    Get role from the dictionnary, Default by default.
    Use of a correlation table to have normalized roles

    :param Device device: device to analyse

    :returns: void
    """


    if lldp_data.get("system_description") is not None and lldp_data.get("system_description") != "":
        for reg,role in ROLE_MAP_DICT.get('regex').items():
            if re.match(reg,lldp_data.get("system_description").lower()):
                return role
            
    if lldp_data.get("software_version") is not None and lldp_data.get("software_version") != "" :
        for reg,role in ROLE_MAP_DICT.get('regex').items():
            if re.match(reg,lldp_data.get("software_version").lower()):
                return role


    if lldp_data.get("capabilities") is not None and lldp_data.get("capabilities") != "":
        for reg,role in ROLE_MAP_DICT.get('capabilities').items():
            if reg == lldp_data.get("capabilities").lower():
                return role

    elif lldp_data.get("lldp_capabilities") is not None and lldp_data.get("lldp_capabilities") != "":
        cap = lldp_data.get("lldp_capabilities").split(',')
        role = ""
        for capa in cap:
            try:
                capa_transformed = ROLE_MAP_DICT.get('capabilities').get(capa)
                if role == "" and capa_transformed is not None:
                    return capa_transformed
                else:
                    role_found = role + "-" + capa_transformed
                    return role_found
            except Exception:
                pass
    return None


                

       

                    
            