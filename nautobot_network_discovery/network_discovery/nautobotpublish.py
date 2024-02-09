import ipaddress
import logging
import random

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from nautobot.apps.choices import PrefixTypeChoices
from nautobot.dcim.models import (
    Device,
    DeviceType,
    Interface,
    Location,
    Manufacturer,
    Platform,
)
from nautobot.extras.models import (
    Relationship,
    RelationshipAssociation,
    Role,
    SecretsGroup,
    Status,
)
from nautobot.ipam.models import (
    VLAN, 
    VRF, 
    IPAddress, 
    Namespace, 
    Prefix
)


from nautobot_network_discovery.exceptions import OnboardException

if "nautobot_device_lifecycle_mgmt" in settings.PLUGINS:
    from nautobot_device_lifecycle_mgmt.models import SoftwareLCM
else:
    SoftwareLCM = None



PLUGIN_SETTINGS = settings.PLUGINS_CONFIG["nautobot_network_discovery"]

def object_match(obj, search_array):
    """Used to search models for multiple criteria.

    Inputs:
        obj:            The model used for searching.
        search_array:   Nested dictionaries used to search models. First criteria will be used
                        for strict searching. Loose searching will loop through the search_array
                        until it finds a match. Example below.
                        [
                            {"slug__iexact": 'switch1'},
                            {"model__iexact": 'Cisco'}
                        ]
    """
    try:
        result = obj.objects.get(**search_array[0])
        return result
    except obj.DoesNotExist:
        if PLUGIN_SETTINGS["object_match_strategy"] == "loose":
            for search_array_element in search_array[1:]:
                try:
                    result = obj.objects.get(**search_array_element)
                    return result
                except obj.DoesNotExist:
                    pass
                except obj.MultipleObjectsReturned as err:
                    raise OnboardException(
                        f"fail-general - ERROR multiple objects found in {str(obj)} searching on {str(search_array_element)})",
                    ) from err
        raise
    except obj.MultipleObjectsReturned as err:
        raise OnboardException(
            f"fail-general - ERROR multiple objects found in {str(obj)} searching on {str(search_array_element)})",
        ) from err




class NautobotPublish:
    def __init__(self,logger,devices):
        self.logger = logger
        self.devices_list = devices
        self.updated_devices=[]
        self.created_devices=[]        
        self.ensure_device_site()
        self.ensure_device_manufacturer()
        self.ensure_device_platform()
        self.ensure_device_device_type()
        self.ensure_device_role()
        self.ensure_device_device()
        self.ensure_version()
        self.ensure_vlan()
        self.ensure_vrf()
        self.ensure_ipaddress()
        self.ensure_interface()

        logger.info(f"{len(self.created_devices)} new devices add in Nautobot, {len(self.updated_devices)} updated devices add in Nautobot")

    def ensure_device_site(self):
        """Ensure device's site."""
        for device in self.devices_list:
            try:
                device.location = Location.objects.get(name=device.location)
            except Location.DoesNotExist as err:
                raise OnboardException(f"fail-config - Site not found: {device.location}") from err


    def ensure_device_manufacturer(self):
        manufacturers = []
        nb_manufacturers={}
        for device in self.devices_list:
            if (device.nautobot_serialize().get('device') is not None and 
                device.nautobot_serialize().get('device').get('manufacturer') is not None and 
                device.nautobot_serialize().get('device').get('manufacturer') not in manufacturers):
                manufacturers.append(device.nautobot_serialize().get('device').get('manufacturer'))
        if len(manufacturers) > 0:
            for nb_manufacturer in manufacturers:
                search_array = [{"name__iexact": nb_manufacturer}]
                try:
                    nb_manufacturers[nb_manufacturer] = object_match(Manufacturer, search_array)
                            
                except Manufacturer.DoesNotExist as err:
                        nb_manufacturers[nb_manufacturer]= Manufacturer.objects.create(name=nb_manufacturer)
        
            for device in self.devices_list:
                if device.nautobot_serialize().get('device') is not None and device.nautobot_serialize().get('device').get('manufacturer') is not None :                
                    device.manufacturer = nb_manufacturers.get(device.nautobot_serialize().get('device').get('manufacturer'))

    def ensure_device_platform(self):
        elements = []
        nb_elements={}
        for device in self.devices_list:
            if (device.nautobot_serialize().get('device') is not None and 
                device.nautobot_serialize().get('device').get('platform') is not None and 
                device.nautobot_serialize().get('device').get('platform') not in elements):
                elements.append(device.nautobot_serialize().get('device').get('platform'))
            elif PLUGIN_SETTINGS["create_default_platform_per_vendor"] is True:
                plt = f'{device.manufacturer.name}_{PLUGIN_SETTINGS["default_platform_suffix"]}'
                device.device["platform"] = plt
                if plt not in elements:
                    elements.append(plt)
        if len(elements) > 0:
            for element in elements:
                search_array = [{"network_driver__iexact": element}]
                try:
                    nb_elements[element] = object_match(Platform, search_array)     
                except Platform.DoesNotExist as err:
                        nb_elements[element]= Platform.objects.create(name=element,network_driver=element)
        
        for device in self.devices_list:
            if device.nautobot_serialize().get('device') is not None and device.nautobot_serialize().get('device').get('platform') is not None :                
                device.platform = nb_elements.get(device.nautobot_serialize().get('device').get('platform'))

    def ensure_device_device_type(self):
        for device in self.devices_list:
            if (device.nautobot_serialize().get('device') is not None and 
                device.nautobot_serialize().get('device').get('device_type') is not None):
                search_array = [
                                    {
                                        "model__iexact": device.nautobot_serialize().get('device').get('device_type'),
                                        "manufacturer":device.manufacturer
                                    }
                                ]
                try:
                   device.device_type = object_match(DeviceType, search_array)
                            
                except DeviceType.DoesNotExist as err:
                        device.device_type = DeviceType.objects.create(
                                                                        model=device.nautobot_serialize().get('device').get('device_type'),
                                                                        manufacturer=device.manufacturer
                                                                        )
            else:
                try:
                    search_array = [
                                        {
                                            "model__iexact": f"{device.manufacturer.name}_Generic",
                                            "manufacturer": device.manufacturer
                                        }
                                    ]

                    try:
                        device.device_type = object_match(DeviceType, search_array)
                                
                    except DeviceType.DoesNotExist as err:
                            device.device_type = DeviceType.objects.create(
                                                                            model=f"{device.manufacturer.name}_Generic",
                                                                            manufacturer=device.manufacturer
                                                                            )
                except Exception as exc: 
                    print(exc)

        
    def ensure_device_role(self,default_role=PLUGIN_SETTINGS["default_device_role"],default_color=PLUGIN_SETTINGS["default_device_role_color"]):
        for device in self.devices_list:
            if (device.nautobot_serialize().get('device') is not None and 
                device.nautobot_serialize().get('device').get('role') is not None):
                try:
                    device.role = Role.objects.get(name=device.nautobot_serialize().get('device').get('role'))
                except Role.DoesNotExist as err:
                        hexa = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
                        choices = random.choices(hexa,k=6)
                        color = "".join(choices)
                        device.role = Role.objects.create(
                            name=device.nautobot_serialize().get('device').get('role'),
                            color=color
                        )
                        device.role.content_types.set([ContentType.objects.get_for_model(Device)])
                        device.role.validated_save()
                        #self.nb_device_role.content_types.set([ContentType.objects.get_for_model(Device)])
            else:
                try:
                    device.role = Role.objects.get(name=default_role)
                except Role.DoesNotExist as err:
                        device.role = Role.objects.create(
                            name=default_role,
                            color=default_color,
                            )
                        device.role.content_types.set([ContentType.objects.get_for_model(Device)])
                        device.role.validated_save()                


        
    def ensure_device_device(self,default_status=PLUGIN_SETTINGS["default_device_status"]):
        for device in self.devices_list:
            if (device.nautobot_serialize().get('device') is not None):
                # Construct lookup arguments if onboarded device does not exist in Nautobot
                ct = ContentType.objects.get_for_model(Device)  # pylint: disable=invalid-name
                try:
                    device_status = Status.objects.get(content_types__in=[ct], name=default_status)
                except Status.DoesNotExist as err:
                    raise OnboardException(
                        f"fail-general - ERROR could not find existing device status: {default_status}",
                    ) from err
                except Status.MultipleObjectsReturned as err:
                    raise OnboardException(
                        f"fail-general - ERROR multiple device status using same name: {default_status}",
                    ) from err
                lookup_args = None
                try:
                    lookup_args = {
                        "name": device.nautobot_serialize().get('device').get('name'),
                        "defaults": {
                            "location": device.location,
                            # `status` field is defined only for new devices, no update for existing should occur
                            "status": device_status,
                        },
                    }
                    try:
                        exist = Device.objects.get(name=device.nautobot_serialize().get('device').get('name'))
                    except Device.DoesNotExist:
                        lookup_args["defaults"]["device_type"] = device.device_type
                        lookup_args["defaults"]["role"] = device.role
                        exist = None
                    if exist and PLUGIN_SETTINGS['update_device_type_if_device_exist'] is True:
                        lookup_args["defaults"]["device_type"] = device.device_type
                    if exist and PLUGIN_SETTINGS['update_role_if_device_exist'] is True:
                        lookup_args["defaults"]["role"] = device.role
                    if device.secrets_group is not None and device.remote_session is not None:
                        lookup_args["defaults"]["secrets_group"]= SecretsGroup.objects.get(name=device.secrets_group)
                    if device.nautobot_serialize().get('device').get('serial') is not None:
                        lookup_args["defaults"]["serial"] = device.nautobot_serialize().get('device').get('serial')               
                    if isinstance(device.platform, Platform):
                        lookup_args["defaults"]["platform"] = device.platform
                except Exception as err:
                    print(f"Device post failed: {err}")
            try:
                if lookup_args is not None:
                    device.device, created = Device.objects.update_or_create(**lookup_args)
                    if created:
                        self.created_devices.append(device.device)
                        self.logger.info("CREATED device: %s", device.device.name)
                    else:
                        self.updated_devices.append(device.device)
                        self.logger.info("GOT/UPDATED device: %s", device.hostname)
            except Device.MultipleObjectsReturned as err:
                raise OnboardException(
                    f"fail-general - ERROR multiple devices using same name in Nautobot: {device.nautobot_serialize().get('device').get('name')}",
                ) from err


    def ensure_interface(self):
        for device in self.devices_list:
            if (device.nautobot_serialize().get('interfaces') is not None):
                interfaces=[]
                # TODO: Add option for default interface status
                for interf in device.nautobot_serialize().get('interfaces'):
                    try:
                        defaults = {
                                        "status": Status.objects.get(name="Active"),
                                    }
                        try : 
                            exist = Interface.objects.get(
                                    name=interf.get('name'),
                                    device=device.device
                            )
                        except Interface.DoesNotExist:
                            defaults["type"]=interf.get('type')
                            exist=None
                        if interf.get('mode') is not None:
                            defaults['mac_address'] = interf.get('mac_address') 
                        if interf.get('enabled') is not None:
                            defaults['enabled'] = interf.get('enabled') 
                        if interf.get('mtu') is not None:
                            defaults['mtu'] = interf.get('mtu') 
                        if interf.get('description') is not None and interf.get('description') != "":
                            defaults['description'] = interf.get('description') 
                        if interf.get('mode') is not None:
                            defaults['mode'] = interf.get('mode') 
                        if (interf.get('mode') == "access" and hasattr(device, "vlans") and 
                            interf.get('untagged_vlan') is not None and 
                            interf.get('untagged_vlan') != ""):
                            for vlan in device.vlans:
                                if vlan.vid == int(interf.get('untagged_vlan')): 
                                    defaults['untagged_vlan']=vlan
                                    break                               
                        elif interf.get('mode') == "tagged":
                            if interf.get('untagged_vlan') is not None and interf.get('untagged_vlan') != "" :
                                for vlan in device.vlans:
                                    if vlan.vid == int(interf.get('untagged_vlan')): 
                                        defaults['untagged_vlan']=vlan
                                        break     
                        elif interf.get('mode') == "tagged-all":
                            if interf.get('untagged_vlan') is not None and interf.get('untagged_vlan') != "" :
                                for vlan in device.vlans:
                                    if vlan.vid == int(interf.get('untagged_vlan')): 
                                        defaults['untagged_vlan']=vlan
                                        break     

                        interface, create = Interface.objects.update_or_create(
                            name=interf.get('name'),
                            device=device.device,
                            defaults=defaults
                        )
                        if interface is not None:
                            if interf.get('mode') == "tagged" and len(interf.get('tagged_vlans')) >0:
                                #interface.mode="tagged"
                                tagged_vlans=[]
                                for vl in interf['tagged_vlans']:
                                    for vlan in device.vlans:
                                        if vlan.vid == int(vl) and vlan not in tagged_vlans: 
                                            tagged_vlans.append(vlan)
                                            break
                                if len(tagged_vlans):
                                    for vl in tagged_vlans:
                                        if vl not in interface.tagged_vlans.all():
                                            interface.tagged_vlans.add(vl)
                                if len(interface.tagged_vlans.all())>0:    
                                    for vl in interface.tagged_vlans.all():
                                        if vl not in tagged_vlans:
                                            interface.tagged_vlans.remove(vl)
                                interface.full_clean()
                                interface.save()                                                              
                            if interf.get('ip_address') is not None and interf.get('ip_address') != "" :
                                interface.ip_addresses.add(interf.get('ip_address'))
                                interface.full_clean()
                                interface.save()
                                ip_interface=interf.get('ip_address').address.ip
                                if str(ip_interface) == str(device.ip):
                                    device.device.primary_ip4 = interf.get('ip_address')
                                    device.device.save()
                            if interf.get('vip') is not None and interf.get('vip') != "" :
                                interface.ip_addresses.add(interf.get('vip'))
                                interface.full_clean()
                                interface.save()
                            if len(interface.ip_addresses.all()) > 0:
                                for i in interface.ip_addresses.all():
                                    present = False
                                    if interf.get('ip_address') is not None and i == interf.get('ip_address'):
                                        present = True
                                    if interf.get('vip') is not None and i == interf.get('vip') :
                                        present = True
                                    if present is False:
                                        i.delete()
                                interface.full_clean()
                                interface.save()
                            if interf.get('vrf') is not None and isinstance(interf.get('vrf'),VRF):
                                interface.vrf = interf.get('vrf')
                                interface.full_clean()
                                interface.save()
                        interfaces.append(interface)
                    except Exception as exc:
                        print(f"failed for interface {interf} on device {device.device.name} : {exc}")



    def ensure_vlan(self):
        for device in self.devices_list:
            if (device.nautobot_serialize().get('vlans') is not None):
                vlans=[]
                # TODO: Add option for default interface status
                for vlan in device.nautobot_serialize().get('vlans'):
                    try:
                        vl, create = VLAN.objects.get_or_create(
                            name=vlan.get('name'),
                            defaults={
                                        "vid": vlan.get('vid') , 
                                        "location": device.location,
                                        "status": Status.objects.get(name="Active"),
                                    },
                        )
                        if vl not in vlans:
                            vlans.append(vl)
                    except Exception as exc:
                        print(exc)

                if len(vlans)>0:
                    try:
                        relationship=Relationship.objects.get(key='vlan')
                    except:
                        relationship=None
                    if relationship is not None:
                        for vl in vlans:
                            presence=False
                            if len(RelationshipAssociation.objects.filter(relationship=relationship,source_id=vl.id,destination_id=device.device.id))>0:
                                for vlan in RelationshipAssociation.objects.filter(relationship=relationship,source_id=vl.id,destination_id=device.device.id):
                                    if vlan.destination == device.device and vlan.source == vl:
                                        presence = True
                                        break
                            if presence is False :
                                asso = RelationshipAssociation.objects.create(
                                                                                relationship=relationship,
                                                                                source=vl,
                                                                                destination=device.device
                                                                            )
                        if len(RelationshipAssociation.objects.filter(relationship=relationship,destination_id=device.device.id))>0:
                            for vlan in RelationshipAssociation.objects.filter(relationship=relationship,destination_id=device.device.id):
                                if vlan.destination == device.device and vlan.source not in vlans:
                                    vlan.delete()

                device.add_property(vlans=vlans)
             
                

    def ensure_vrf(self):
        for device in self.devices_list:
            if (device.nautobot_serialize().get('vrfs') is not None):
                vrfs=[]
                # TODO: Add option for default interface status
                for vrf in device.nautobot_serialize().get('vrfs'):
                    try:
                        vrf_nb, _ = VRF.objects.get_or_create(
                            name=vrf.get('vrf'),
                            defaults={
                                        "rd": vrf.get('rd') , 
                                        "namespace": Namespace.objects.get(name=device.namespace),
                                    },
                        )
                        vrfs.append(vrf_nb)
                        if vrf_nb not in device.device.vrfs.all():
                            vrf_nb.add_device(device.device)
                    except Exception as exc:
                        print(exc)
                for vrf in device.device.vrfs.all():
                    if vrf not in vrfs:
                        vrf.remove_device(device.device)
                if (device.nautobot_serialize().get('interfaces') is not None and len(device.device.vrfs.all()) > 0):
                    interfaces=[]
                    # TODO: Add option for default interface status
                    for interf in device.nautobot_serialize().get('interfaces'):
                        for vrf in device.device.vrfs.all():
                            try:
                                if interf.get('vrf') is not None and interf.get('vrf') == vrf.name :
                                    interf["vrf"] = vrf
                        
                            except Exception as exc:
                                print(exc)
                        interfaces.append(interf)
                    device.interfaces = interfaces


    def ensure_ipaddress(self):
        
        default_status_name = PLUGIN_SETTINGS["default_ip_status"]
        try:
            ip_status = Status.objects.get(name=default_status_name)
        except Status.DoesNotExist as err:
            raise OnboardException(
                f"fail-general - ERROR could not find existing IP Address status: {default_status_name}",
            ) from err
        for device in self.devices_list:
            if ( device.nautobot_serialize().get('interfaces') is not None ) :
                namespace = Namespace.objects.get(name=device.namespace)
                interfaces=[]
                # TODO: Add option for default interface status
                for interf in device.nautobot_serialize().get('interfaces'):
                    try:
                        if device.remote_session is not None and interf.get('ip_address') is not None and interf.get('ip_address') !="":
                            prefix = ipaddress.ip_interface(interf.get('ip_address'))
                            nautobot_prefix, _ = Prefix.objects.get_or_create(
                                prefix=f"{prefix.network}",
                                namespace=namespace,
                                type=PrefixTypeChoices.TYPE_NETWORK,
                                defaults={"status": ip_status},
                                )
                            defaults = {"status": ip_status,
                                           "type": "host"}
                            address, created = IPAddress.objects.get_or_create(
                                address=interf.get('ip_address'),
                                parent=nautobot_prefix,
                                defaults=defaults,
                                )
                            
                            interf["ip_address"] = address
                    except Exception as exc:
                        print(f"{device.device.name} : {interf.get('ip_address')} : {exc}")
                        interf.pop("ip_address")
                    try:
                        if interf.get('vip') is not None and interf.get('vip') !="":
                            prefix = ipaddress.ip_interface(interf.get('vip'))
                            role = Role.objects.get(name="VIP")
                            nautobot_prefix, _ = Prefix.objects.get_or_create(
                                prefix=f"{prefix.network}",
                                namespace=namespace,
                                type=PrefixTypeChoices.TYPE_NETWORK,
                                defaults={"status": ip_status},
                                )
                            defaults = {"status": ip_status,
                                        "type": "host",
                                        "role": role
                                        }
                            address, created = IPAddress.objects.get_or_create(
                                address=interf.get('vip'),
                                parent=nautobot_prefix,
                                defaults=defaults,
                                )
                            interf["vip"] = address
                    except Exception as exc:
                        interf.pop("vip")
                        print(f"{device.device.name} : {interf.get('vip')} : {exc}")
                    interfaces.append(interf)
                device.interfaces = interfaces

        for device in self.devices_list:
            if device.remote_session is None and device.nautobot_serialize().get('interfaces') is not None :
                interfaces=[]
                for interf in device.nautobot_serialize().get('interfaces'):
                    if interf.get('ip_address') is not None and interf.get('ip_address') !="":
                        prefix_found=[]
                        for pref in Prefix.objects.all():
                            if ipaddress.ip_interface(interf.get('ip_address')) in ipaddress.ip_network(f"{pref.network}/{pref.prefix_length}"):
                                prefix_found.append(pref)
                        if len(prefix_found)>0:
                            for pref in prefix_found:
                                if len(pref.subnets()) == 0:
                                    nautobot_prefix =pref
                                    break
                        else:
                            pref = ipaddress.ip_interface(interf.get('ip_address'))
                            nautobot_prefix, _ = Prefix.objects.get_or_create(
                                prefix=f"{pref.network}",
                                namespace=namespace,
                                type=PrefixTypeChoices.TYPE_NETWORK,
                                defaults={"status": ip_status},
                                )
                        if nautobot_prefix:

                            try:
                                address = IPAddress.objects.get(address=interf.get('ip_address'))
                            except IPAddress.DoesNotExist:
                                defaults = {"status": ip_status,
                                                "type": "host"}
                                try:
                                    address, created = IPAddress.objects.get_or_create(
                                        address=interf.get('ip_address'),
                                        parent=nautobot_prefix,
                                        defaults=defaults,
                                        )
                                except:
                                    interf.pop("ip_address")
                            if address:    
                                interf["ip_address"] = address                        
                    interfaces.append(interf)
                device.interfaces = interfaces

    def ensure_version(self):
        if SoftwareLCM is not None:
            relationship=Relationship.objects.get(key='device_soft')
            for device in self.devices_list:
                if (device.nautobot_serialize().get('version') is not None and 
                    device.nautobot_serialize().get('version').get("version") is not None and 
                    device.device.platform is not None):
                    try:
                        ver, _ = SoftwareLCM.objects.get_or_create(
                            version=device.nautobot_serialize().get('version').get("version"),
                            defaults={
                                        "device_platform": device.platform
                                    },
                        )
                        presence=False
                        change_version=False
                        if len(RelationshipAssociation.objects.filter(relationship=relationship,destination_id=device.device.id))>0:
                            for version in RelationshipAssociation.objects.filter(relationship=relationship,destination_id=device.device.id):
                                if version.relationship.key == "device_soft":
                                    if version.destination == device.device and version.source == ver:
                                        presence = True
                                        break
                                    elif version.destination == device.device:
                                        version.delete()
                                        change_version=True
                                        break
                        if presence is False or change_version is True :
                            asso = RelationshipAssociation.objects.create(
                                                                            relationship=relationship,
                                                                            source=ver,
                                                                            destination=device.device
                                                                        ) 
                    except Exception as exc:
                        print(f"Version: {device.device.name} : {ver}  {exc}")
