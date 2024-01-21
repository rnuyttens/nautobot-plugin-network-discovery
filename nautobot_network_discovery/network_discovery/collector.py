from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import LifoQueue
from importlib import import_module

from nautobot_network_discovery.network_discovery.device import DeviceDiscovery
from nautobot_network_discovery.network_discovery.nautobotpublish import NautobotPublish
from nautobot_network_discovery.network_discovery.format.interfaces import default_interface



def format_cmd_result(data:dict,cmd_name:str,cmd_result:list,mapper) -> dict:

    for mapkeys,mapvalues in mapper.items():              
        if cmd_name in mapvalues:
            if data.get(mapkeys) is None:
                if mapvalues.get("type") == "list":
                    m= mapvalues.get(cmd_name)
                    results=[]
                    if mapvalues.get("function") is not None:
                        func = import_module(f'nautobot_network_discovery.network_discovery.format.{mapvalues.get("function")}')
                        cmd_result = func.run(cmd_result)
                    if isinstance(cmd_result,list):
                        for c in cmd_result:
                            temp_data={}
                            for k,v in c.items():
                                if m.get(k) is not None and v != "":
                                    temp_data[m.get(k)] = v
                            results.append(temp_data)
                    data[mapkeys] = results

                elif mapvalues.get("type") == "dict":
                    m= mapvalues.get(cmd_name)
                    results={}
                    if mapvalues.get("function") is not None:
                        func = import_module(f'nautobot_network_discovery.network_discovery.format.{mapvalues.get("function")}')
                        cmd_result = func.run(cmd_result)

                    if isinstance(cmd_result,list):
                        for c in cmd_result:
                            temp_data={}
                            for k,y in c.items():
                                if m.get(k) is not None and y != "":
                                    temp_data[m.get(k)] = y
                            results = temp_data                                    
                    data[mapkeys] = results
            else:
                master_key = mapvalues.get("master_key")
                for i,k in master_key.items():
                    master_dev = k
                    master_nb = i
                if mapvalues.get("type") == "list" and master_key is not None:
                    m= mapvalues.get(cmd_name)
                    if mapvalues.get("function") is not None:
                        func = import_module(f'nautobot_network_discovery.network_discovery.format.{mapvalues.get("function")}')
                        cmd_result = func.run(cmd_result)
                    if isinstance(cmd_result,list):
                        for c in cmd_result:
                            for k,v in c.items():
                                for item in data.get(mapkeys):
                                    if c.get(master_dev) == item.get(master_nb) :
                                        if m.get(k) is not None and v!= "":
                                            item[m.get(k)] = v
    return data

def collect_data(device):
    map_platform = None
    try:
        if device.remote_session is None:
            map_platform = import_module('nautobot_network_discovery.network_discovery.mapper.generic')
        else:
            map_platform = import_module(f'nautobot_network_discovery.network_discovery.mapper.{device.platform}')
    except:
        map_platform = import_module('nautobot_network_discovery.network_discovery.mapper.generic')
    if map_platform is not None:
        mapper = map_platform.MAPPING_VALUES
    else:
        mapper = None

    data = {}
    if mapper is not None and device.commands is not None and device.remote_session is not None:    
        for cmd_name,cmd in device.commands.items():
            temp= device.request(cmd)
            if temp is not None:
                data = format_cmd_result(data,cmd_name,temp,mapper)

    if mapper is not None :
        for mapkeys,mapvalues in mapper.items():
            if data.get(mapkeys) is None:
                if mapvalues.get('type') == "list":
                    data[mapkeys] = []
                else:
                    data[mapkeys] = {}
            for value in mapvalues :
                if device.commands is not None and device.commands.get(value) is None and value not in  ("type","function","master_key"):
                    var = mapvalues.get(value)
                    for k,v in var.items():
                        if isinstance(data.get(mapkeys),dict):
                            if data.get(mapkeys).get(v) is None :
                                if value == "manufacturer" :
                                    func = import_module(f'nautobot_network_discovery.network_discovery.format.device')
                                    temp = {}
                                    if hasattr(device,"platform") is True:
                                        temp['platform'] = getattr(device,'platform')
                                    if hasattr(device,"system_description") is True:
                                        temp['system_description'] = getattr(device,'system_description')
                                    if hasattr(device,"software_version") is True:
                                        temp['software_version'] = getattr(device,'software_version')                                
                                    if len(temp) > 0:
                                        temp = func.run([temp])   
                                        data[mapkeys][v] = temp[0].get("manufacturer")
                                    else:
                                        data[mapkeys][v] = "Generic"
                                elif hasattr(device,k) is True and getattr(device,k) != "":                             
                                    data[mapkeys][v]= getattr(device,k)
                
                if device.remote_session is None and value not in  ("type","function","master_key"):
                    var = mapvalues.get(value)
                    for k,v in var.items():
                        try:
                            if mapvalues.get('type') == "dict":
                                if data.get(mapkeys) is not None and isinstance(data.get(mapkeys),dict):
                                    if data.get(mapkeys).get(v) is None :
                                        if hasattr(device,k) is True and getattr(device,k) != "":
                                            data[mapkeys][v] = getattr(device,k)

                            else:
                                if len(data.get(mapkeys)) == 0 :
                                    if hasattr(device,k) is True and getattr(device,k) != "" and k == "interface":
                                        interface = default_interface(getattr(device,k))
                                        interface[0]['ip_address'] = f"{device.ip}/32"
                                        data[mapkeys] = interface
                        except Exception as exc:
                            print(f"{exc}")




    if len(data) > 0:
        device.add_property(**data)
    device.connection_stop()
    return True






def discovery_devices(
                        logger,
                        lock=None ,
                        queue:LifoQueue | None = None,
                        device:DeviceDiscovery | None = None
                      ):
    
    all_devices = []
    if queue is not None and lock is not None:
        while lock.locked() is True:
            check_queue = queue.empty()
            while check_queue is False:
                devices = []
                pool_size = 0
                if queue.empty() is False:
                    while not queue.empty() :
                        device = queue.get_nowait()
                        
                        devices.append(device)

                        queue.task_done()
                    
                    pool_size = len(devices)
                    if pool_size != 0:
                        with ThreadPoolExecutor(max_workers = pool_size,thread_name_prefix='LLDP_NEIGHBOR_PARSER') as executor:
                            futures = [executor.submit(collect_data, device) for device in devices]
                            for future in as_completed(futures):
                                # retrieve the result
                                future.result()

                    all_devices.extend(devices)
                check_queue = queue.empty()

    elif device is not None:
        collect_data(device)
        all_devices.append(device)

    NautobotPublish(logger,all_devices)
