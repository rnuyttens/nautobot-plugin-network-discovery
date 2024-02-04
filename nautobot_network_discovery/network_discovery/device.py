"""device.py"""
import logging
import os
from importlib import import_module

from django.conf import settings
from netmiko import (
    ConnectHandler, 
    NetmikoAuthenticationException, 
    SSHDetect
)
from paramiko.ssh_exception import (
    AuthenticationException, 
    SSHException
)

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG["nautobot_network_discovery"]


class DeviceDiscovery:
    def __init__(
                    self,
                    host,
                    port=None,
                    timeout=None,
                    username= None,
                    password= None,
                    secret = None,
                    discovery_type= None,
                    location=None,
                    role=PLUGIN_SETTINGS["default_device_role"],
                    manufacturer= str(os.getenv("DEFAULT_MANUFACTURER","Generic")),
                    model= str(os.getenv("DEFAULT_MODEL","Generic")),
                    platform = "autodetect",
                    hostname = None,
                    secrets_group = None,
                    namespace=PLUGIN_SETTINGS["default_ipam_namespace"],
                    logger= None,
                    

                ):



        self.ip = host
        self.port = port
        self.timeout = timeout
        self.username=username
        self.password=password
        self.secret=secret
        self.platform = platform
        self.discovery_type = discovery_type
        self.location = location
        self.manufacturer = manufacturer
        self.model = model
        self.role = role
        self.platform = platform
        self.secrets_group = secrets_group
        if hostname is not None:
            self.hostname = hostname
        else:
            self.hostname = f"H-{self.ip}"
        self.remote_session = None
        self.commands = None
        self.logger = logger
        self.namespace=namespace

    def connection(self):
        if self.role not in PLUGIN_SETTINGS["deny_role_scan"]:
            ssh_profile = {
                            "username": self.username,
                            "password": self.password,
                            "secret":self.secret,
                            "ip": self.ip,
                            "device_type": self.platform,
                            "global_delay_factor": int(self.timeout),
                            "conn_timeout": int(self.timeout),
                            "auth_timeout": int(self.timeout)
                            }
            best_match = None
            if self.platform == "autodetect" :
                try : 
                    guesser = SSHDetect(**ssh_profile)
                    best_match = guesser.autodetect()  
                except (NetmikoAuthenticationException,AuthenticationException) as error :
                    print(error)
                except NameError as error:
                    print(error)
                except (SSHException) as error:
                    print(error)       
                except Exception as error:
                    print(error)

                if best_match is not None:    
                    ssh_profile["device_type"] = best_match
                    self.platform = best_match
                else:
                    self.platform = None
        else: 
            self.platform = None
        if self.platform in PLUGIN_SETTINGS["override_network_driver"]:
            ssh_profile["device_type"] = PLUGIN_SETTINGS["override_network_driver"].get(self.platform)

        if self.platform is not None:
            try:
                cmd = import_module(f'nautobot_network_discovery.network_discovery.mapper.{self.platform}')
                self.commands = cmd.COMMANDS
                self.remote_session = ConnectHandler(**ssh_profile)
                self.remote_session.enable()
                if self.platform == "fortinet" and self.remote_session._vdoms is True:
                    self.remote_session._config_global()

                self.remote_session.session_timeout=int(os.getenv('SSH_SESSION_TIMEOUT',"60"))
                self.remote_session.timeout=int(os.getenv('SSH_TIMEOUT',"30"))
                self.remote_session.ansi_escape_codes = True
                self.logger.info(f"Successful connection to {self.ip}")
            except:
                print("no command")
        else:
            self.commands = None
            self.remote_session = None

    def request(self,command):
        if self.remote_session is not None:
            try:
                if isinstance(command,str):
                    req = self.remote_session.send_command(command,use_textfsm=True,read_timeout=30)
                    if isinstance(req,list):
                        return req
                    else:
                        return None
                if isinstance(command,dict):
                    req = self.remote_session.send_command(
                                                                    command.get('cmd'),
                                                                    use_ttp=True, 
                                                                    ttp_template=command.get('ttp_template',read_timeout=30)
                                                                )           
                    if isinstance(req,list):
                        return req
                    else:
                        return None
                else:
                    return None
            except Exception as exc:
                print(f"Failed command for: {command} on: {self.ip}{exc}")
                return None
    


            
    def connection_stop(self):
        if self.remote_session is not None:
            self.remote_session.disconnect()
            print(f"Disconnection from{self.ip}")

    def add_property(self,**kwargs):
        for name, data in kwargs.items():
            setattr(self, name, data)
    
    def serialize(self):
        return self.__dict__
    
    def nautobot_serialize(self):
        map_platform = None
        data = {}
        try:
            map_platform = import_module(f'nautobot_network_discovery.network_discovery.mapper.{self.platform}')
        except:
            map_platform = import_module('nautobot_network_discovery.network_discovery.mapper.generic')
        if map_platform is not None:
            mapper = map_platform.MAPPING_VALUES
        else:
            mapper = None
        if mapper is not None:
            
            serialize=self.serialize()
            for key,value in mapper.items():
                data[key] = serialize.get(key)
        return data