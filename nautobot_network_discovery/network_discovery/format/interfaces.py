
from django.conf import settings
from nautobot.dcim.choices import InterfaceTypeChoices

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG["nautobot_network_discovery"]

interfaces_model = [
[["Ethernet","Eth","eth"],"Ethernet"],
[["FastEthernet"," FastEthernet","Fa","interface FastEthernet","FastEthernet","fa"],"FastEthernet"],
[["GigabitEthernet","Gi"," GigabitEthernet","interface GigabitEthernet",'gi'],"GigabitEthernet"],
[["TenGigabitEthernet","Te","te"],"TenGigabitEthernet"],
[["TwentyFiveGigE",'Twe','twe'],"TwentyFiveGigabitEthernet"],
[["Port-channel","Po"],"Port-channel"],
[["Serial","Ser"],"Serial"],
[["Vlan","interface Vlan"],"Vlan"],
[["Port","Port ",],"Port"]
]

VIRTUALS = ["loopback", "ethersvi","ethernet svi","lisp"]
LAG= ['etherchannel']
GE_FIXED = ["gigabit ethernet"]
TWE_GE = ["twenty five gigabit ethernet"]
TEN_GE_SFP_PLUS = ["ten gigabit ethernet"]
FOURTY_GE= ["forty gigabit ethernet"]

def split_interface(interface):
    """
	Split and return the interface in two parts : the name and the port

	:param str interface: name of the interface

	:returns: list of two elements with name and port of the device
	"""
    num_index = interface.index(next(x for x in interface if x.isdigit()))
    str_part = interface[:num_index]
    num_part = interface[num_index:]
    return [str_part,num_part]

def normalize_interface_names(non_norm_int):
    """
	Split the interfaces to get its name and search in the interfaces list if it exists.
	If it is found return the normalized name for this interface

	:param str non_norm_int: interface to be normed

	:returns: normed interface (str)
	"""
    if non_norm_int != "":
        try:
            tmp = split_interface(non_norm_int)
            interface_type = tmp[0]
            port = tmp[1]
            for int_types in interfaces_model:
                for names in int_types:
                    for name in names:
                        if interface_type in name:
                            return_this = int_types[1]+port
                            return return_this
        except :
            pass
    return non_norm_int




def run(interfaces):
    if isinstance(interfaces,list):
        for interface in interfaces:
            if interface.get("interface") is not None and interface.get("interface") != "":
                interface['interface'] = normalize_interface_names(interface.get('interface'))
            if interface.get("mac_address") is not None and interface.get("mac_address") != "":
                mac_str = interface.get("mac_address")
                temp = mac_str.replace(":", "").replace("-", "").replace(".", "").upper()
                if len(temp) == 12 :
                    mac = temp[:2] + ":" + ":".join([temp[i] + temp[i+1] for i in range(2,12,2)])
                    interface['mac_address'] = mac
            if interface.get("ip_address") is not None and interface.get("ip_address") != "" and interface.get("prefix_length") is not None and interface.get("prefix_length") !="":
                ip = f'{interface.get("ip_address")}/{interface.get("prefix_length")}'
                interface['ip_address'] = ip
            if interface.get("link_status") is not None and interface.get("link_status") != "":
                if interface.get("link_status") == 'up':
                    interface['link_status'] = True
                    
                else:
                    interface['link_status'] = False

            if interface.get("hardware_type") is not None and interface.get('hardware_type').lower() in LAG :
                interface['hardware_type'] = 'lag'
            elif interface.get("hardware_type") is not None and interface.get('hardware_type').lower() in GE_FIXED :
                interface['hardware_type'] = InterfaceTypeChoices.TYPE_1GE_FIXED
            elif interface.get("hardware_type") is not None and interface.get('hardware_type').lower() in TWE_GE :
                interface['hardware_type'] = InterfaceTypeChoices.TYPE_25GE_SFP28
            elif interface.get("hardware_type") is not None and interface.get('hardware_type').lower() in TEN_GE_SFP_PLUS :
                interface['hardware_type'] = InterfaceTypeChoices.TYPE_10GE_SFP_PLUS
            elif interface.get("hardware_type") is not None and interface.get('hardware_type').lower() in FOURTY_GE :
                interface['hardware_type'] = InterfaceTypeChoices.TYPE_40GE_QSFP_PLUS
            elif interface.get("hardware_type") is not None and interface.get('hardware_type').lower() in VIRTUALS :
                interface['hardware_type'] = 'virtual'
            else:
                interface['hardware_type'] = 'other'

            if interface.get('mode') is not None and interface.get("mode") != "":
                if interface.get("mode") == "trunk" and interface.get('trunking_vlans') == ["ALL"]:
                    interface["mode"] = "tagged-all"
                    interface.pop('trunking_vlans')
                elif interface.get("mode") == "trunk":
                    interface['mode'] = "tagged"
                    if interface.get("trunking_vlans") is not None and interface.get('trunking_vlans') != ["ALL"] and len(interface.get('trunking_vlans')) >0:
                        vlans_list=[]
                        for vlans in interface.get("trunking_vlans"):
                            if "," in vlans:
                                vlans_split = vlans.split(',')
                                for vlan in vlans_split:
                                    if "-" not in vlan:
                                        vlans_list.append(vlan)
                                    else:
                                        for i in range(int(vlan.split('-')[0]),int(vlan.split('-')[1])+1):
                                            vlans_list.append(i)
                        interface["trunking_vlans"]=vlans_list
                else:
                    interface['mode'] = "access"
                    interface['native_vlan'] = ""

            if interface.get('virtual_ip') is not None and interface.get("virtual_ip") != "":
                if "/" not in interface.get('virtual_ip'):
                    interface["virtual_ip"] = f"{interface.get('virtual_ip')}/32"
    return interfaces

def default_interface(interface):

    if isinstance(interface,str):
        if interface is not None and interface != "":
            interfaces = [ {'name' : normalize_interface_names(interface),
                            "type":'other'                         
                            } ]
            return interfaces
            
    else:
        return None
    
