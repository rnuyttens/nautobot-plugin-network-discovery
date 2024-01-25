import re
from importlib import import_module
from multiprocessing.pool import ThreadPool
from queue import LifoQueue
from threading import Lock

from nautobot_network_discovery.network_discovery.device import DeviceDiscovery
from nautobot_network_discovery.network_discovery.format.manufacturers import (
    manufacturer,
)
from nautobot_network_discovery.network_discovery.format.role import role
from nautobot_network_discovery.network_discovery.mapper.lldp_mapper import (
    LLDP_MAPPER_DICT,
)


def lldp_autodetect(lldp_data:dict) -> str:
    """
    Search in the database if the type exist and return it, else return None

    :param str snmp_type: data to analyse

    :returns: name of the vendor (str), can be None
    """

    try:
        if lldp_data.get("system_description") is not None and lldp_data.get("system_description") != "":
            for device_type in LLDP_MAPPER_DICT:
                for search_pattern in LLDP_MAPPER_DICT.get(device_type).get("search_patterns") :
                    match = re.search(search_pattern, lldp_data.get("system_description"))
                    if match:
                        return device_type                
        elif  lldp_data.get("platform") is not None and lldp_data.get("platform") != "" :
            for device_type in LLDP_MAPPER_DICT:
                for search_pattern in LLDP_MAPPER_DICT.get(device_type).get("search_patterns") :
                    match = re.search(search_pattern, lldp_data.get("platform"))
                    if match:
                        return device_type              
        if lldp_data.get("software_version") is not None and lldp_data.get("software_version") != "":
            for device_type in LLDP_MAPPER_DICT:
                for search_pattern in LLDP_MAPPER_DICT.get(device_type).get("search_patterns") :
                    match = re.search(search_pattern, lldp_data.get("software_version"))
                    if match:
                        return device_type 
        else:
            return None
    except OSError as exc:
        return None
    except Exception:
        return None


class NeighborsDiscovery:
    def __init__(self,logger,device:DeviceDiscovery,lock:Lock,queue:LifoQueue):
        self.ips = [device.ip]
        self.logger=logger
        self.hostnames = []
        lock.acquire()
        self.queue = queue
        self.start_collect([device])
        lock.release()

    def start_collect(self,devices:list):
        while len(devices)>0:
            if len(devices) < 48:
                pool_size = len(devices)
            else:
                pool_size = 48
            if pool_size != 0:
                with ThreadPool(processes=pool_size) as pool:
                    thread = pool.map(self.collect, devices)
                results = []
                for device in thread:
                    results.extend(device)       
                devices= results 
            else:
                devices = []
        print(f"total ip: {len(self.ips)}")

    def collect(self,device:DeviceDiscovery) -> list:
        collect_device = []
        try :
            device.connection()
        except Exception as exc:
            print(exc)
            pass
        try :
            if device.remote_session is not None:
                cmd = import_module(f'nautobot_network_discovery.network_discovery.mapper.{device.platform}')
                try: 
                    for k,v in cmd.DISCOVERY_CMD.items():
                        new_devices = self.parse_neighbors(device,device.request(v))
                        if new_devices is not None :
                            collect_device.extend(new_devices)
                except:
                    pass
            self.queue.put(device)
        except Exception as exc:
            print(exc,device)
        return collect_device
      


    def parse_neighbors(self,device:DeviceDiscovery,command_result):
        if command_result is not None:
            new_devices=[]
            cmd=import_module(f'nautobot_network_discovery.network_discovery.mapper.{device.platform}')
            discovery_key =cmd.DISCOVERY_TEMPLATE
            for discovery_device in command_result:
                if (discovery_key.get('ip') in discovery_device and 
                    discovery_device.get(discovery_key.get('ip')) != "" and 
                    discovery_device.get(discovery_key.get('ip')) not in self.ips) and (discovery_key.get('hostname') in discovery_device and 
                                                                                       discovery_device.get(discovery_key.get('hostname')) != "" and 
                                                                                       discovery_device.get(discovery_key.get('hostname')) not in self.hostnames
                                                                                       ):


                    dev = DeviceDiscovery(
                                                host=discovery_device.get(discovery_key.get('ip')),
                                                port=device.port,
                                                timeout=device.timeout,
                                                username=device.username,
                                                password=device.password,
                                                secret=device.secret,
                                                discovery_type='lldp',
                                                location=device.location,
                                                role=role(discovery_device),
                                                platform=lldp_autodetect(discovery_device),
                                                manufacturer=manufacturer(discovery_device,lldp_autodetect(discovery_device)),
                                                hostname=discovery_device.get('neighbor'),
                                                secrets_group=device.secrets_group
                                            )
                    
                    self.logger.info(f"New device found: {dev.hostname}")

                    self.ips.append(dev.ip)
                    self.hostnames.append(dev.hostname)
                    data ={}

                    for k,v in discovery_key.items():
                        if discovery_device.get(v) is not None and discovery_device.get(v) != "" and v != "manufacturer":
                            data[k] = discovery_device.get(v)
                    if len(data) > 0:
                        dev.add_property(**data)
                    new_devices.append(dev)
            if len(new_devices) > 0 :
                return new_devices
            else:
                return None
        else:
            return None