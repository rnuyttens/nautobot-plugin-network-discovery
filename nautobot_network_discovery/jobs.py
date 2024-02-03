"""Network Discovery Jobs."""
from queue import LifoQueue
from threading import Lock, Thread

from django.conf import settings
from nautobot.apps.jobs import (
    BooleanVar,
    ChoiceVar,
    IntegerVar,
    Job,
    ObjectVar,
    StringVar,
)
from nautobot.core.celery import register_jobs
from nautobot.dcim.models import DeviceType, Location, Platform
from nautobot.extras.choices import (
    SecretsGroupAccessTypeChoices,
    SecretsGroupSecretTypeChoices,
)
from nautobot.extras.models import Role, SecretsGroup, SecretsGroupAssociation

from nautobot_network_discovery.exceptions import OnboardException
from nautobot_network_discovery.helpers import onboarding_task_fqdn_to_ip
from nautobot_network_discovery.network_discovery.collector import discovery_devices
from nautobot_network_discovery.network_discovery.device import DeviceDiscovery
from nautobot_network_discovery.network_discovery.neighbors import NeighborsDiscovery

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG["nautobot_network_discovery"]


class NetworkDiscoveryTask(Job):  # pylint: disable=too-many-instance-attributes
    """Nautobot Job for onboarding a new device."""

    location = ObjectVar(
        model=Location,
        query_params={"content_type": "dcim.device"},
        description="Assigned Location for the onboarded device.",
    )
    ip_address = StringVar(
        description="IP Address/DNS Name of the device to onboard, specify in a comma separated list for multiple devices.",
        label="IP Address/FQDN",
    )
    port = IntegerVar(default=22)
    timeout = IntegerVar(default=30)
    ssh_credentials = ObjectVar(
        model=SecretsGroup, 
        required=True, 
        description="SecretsGroup for Device SSH connection credentials.",
        label="SSH Credentials"

    )
    platform = ObjectVar(
        model=Platform,
        required=False,
        description="Device platform. Define ONLY to override auto-recognition of platform.",
    )
    role = ObjectVar(
        model=Role,
        query_params={"content_type": "dcim.device"},
        required=False,
        description="Device role. Define ONLY to override auto-recognition of role.",
    )
    device_type = ObjectVar(
        model=DeviceType,
        label="Device Type",
        required=False,
        description="Device type. Define ONLY to override auto-recognition of type.",
    )

    discovery_type = ChoiceVar(
        description="Discovery mode",
        label="Discovery Mode",
        choices=(
            ("single", "Single device"),
            ("lldp", "LLDP Discovery"),
        ),
    )


    class Meta:  # pylint: disable=too-few-public-methods
        """Meta object boilerplate for onboarding."""

        name = "Perform Network Discovery"
        description = "Login to a device(s) and populate Nautobot Device object(s)."
        has_sensitive_variables = False
        soft_time_limit = 600
        time_limit= 800

    def __init__(self, *args, **kwargs):
        """Overload init to instantiate class attributes per W0201."""
        self.username = None
        self.password = None
        self.secret = None
        self.secrets_group = None
        self.platform = None
        self.port = None
        self.timeout = None
        self.location = None
        self.device_type = None
        self.role = None
        self.discovery_type = None
        super().__init__(*args, **kwargs)

    def run(self, *args, **data):
        """Process a single Onboarding Task instance."""
        self._parse_credentials(data["ssh_credentials"])
        self.platform = data["platform"]
        self.port = data["port"]
        self.timeout = data["timeout"]
        self.location = data["location"]
        self.device_type = data["device_type"]
        self.role = data["role"]
        self.discovery_type=data["discovery_type"]

        self.logger.info("START: onboarding devices")
        # allows for itteration without having to spawn multiple jobs
        # Later refactor to use nautobot-plugin-nornir
        for address in data["ip_address"].split(","):
            try:
                self._onboard(address=address)
            except OnboardException as err:
                self.logger.exception(
                    "The following exception occurred when attempting to onboard %s: %s", address, str(err)
                )
                if not data["continue_on_failure"]:
                    raise OnboardException(
                        "fail-general - An exception occured and continue on failure was disabled."
                    ) from err

    def _onboard(self, address):
        """Onboard single device."""
        self.logger.info("Attempting to onboard %s.", address)
        address = onboarding_task_fqdn_to_ip(address)
        if self.discovery_type == 'lldp':
            self.logger.info("Start LLDP Discovery")
            mutex = Lock()
            queue=LifoQueue()
            device_data = {
                "host": address,
                "port": self.port,
                "timeout": self.timeout,
                "discovery_type": self.discovery_type,
                "location": self.location.name,
                "logger": self.logger
                }
            if self.username is not None:
                device_data["username"] = self.username
            if self.password is not None:
                device_data["password"] = self.password
            if self.password is not None:
                device_data["secret"] = self.secret 
            if self.role is not None:
                device_data["role"] = self.role.name   
            if self.device_type is not None:
                device_data["device_type"] = self.device_type.model   
            if self.platform is not None:
                device_data["platform"] = self.platform.network_driver   
            if self.secrets_group is not None:
                device_data["secrets_group"] = self.secrets_group  

            device = DeviceDiscovery(**device_data)


            neighbors_discovery = Thread(target=NeighborsDiscovery,kwargs={"logger" :self.logger,"device":device,"lock":mutex,"queue":queue},name = "PUBLISH_THREAD")
            neighbors_discovery.start()
            discovery_devices(logger=self.logger,lock=mutex,queue=queue)
        else:
            self.logger.info(f"Start Discovery for {address}")
            device_data = {
                "host":address,
                "port":self.port,
                "timeout":self.timeout,
                "discovery_type":self.discovery_type,
                "location":self.location.name,
                "logger" :self.logger
                }
            if self.username is not None:
                device_data["username"] = self.username
            if self.password is not None:
                device_data["password"] = self.password
            if self.password is not None:
                device_data["secret"] = self.secret 
            if self.role is not None:
                device_data["role"] = self.role.name   
            if self.device_type is not None:
                device_data["model"] = self.device_type.model   
            if self.platform is not None:
                device_data["platform"] = self.platform.network_driver   
            if self.secrets_group is not None:
                device_data["secrets_group"] = self.secrets_group 

            device = DeviceDiscovery(**device_data)
            device.connection()
            discovery_devices(logger=self.logger,device=device)


        self.logger.info(
            "Successfully onboarded with a management IP of %s", address
        )

    def _parse_credentials(self, credentials):
        """Parse and return dictionary of credentials."""
        if credentials:
            self.logger.info("Attempting to parse credentials from selected SecretGroup")
            try:
                self.secrets_group = credentials.name
                self.username = credentials.get_secret_value(
                    access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
                    secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME,
                )
                self.password = credentials.get_secret_value(
                    access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
                    secret_type=SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
                )
                try:
                    self.secret = credentials.get_secret_value(
                        access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
                        secret_type=SecretsGroupSecretTypeChoices.TYPE_SECRET,
                    )
                except SecretsGroupAssociation.DoesNotExist:
                    self.secret = None
            except SecretsGroupAssociation.DoesNotExist as err:
                self.logger.exception(
                    "Unable to use SecretsGroup selected, ensure Access Type is set to Generic & at minimum Username & Password types are set."
                )
                raise OnboardException("fail-credentials - Unable to parse selected credentials.") from err

        else:
            self.logger.info("Using napalm credentials configured in nautobot_config.py")
            self.username = settings.NAPALM_USERNAME
            self.password = settings.NAPALM_PASSWORD
            self.secret = settings.NAPALM_ARGS.get("secret", None)
            


register_jobs(NetworkDiscoveryTask)
