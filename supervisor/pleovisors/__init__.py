"""Represents the API for Pleovisors."""

import logging

from supervisor.addons.addon import Addon
from supervisor.jobs.const import JobCondition
from supervisor.jobs.decorator import Job
from supervisor.pleovisors.const import FILE_HASSIO_PLEOVISORS
from supervisor.pleovisors.instance import Pleovisor
from supervisor.pleovisors.validate import SCHEMA_PLEOVISORS_FILE

from ..const import ATTR_PLEOVISORS, SOCKET_DOCKER
from ..coresys import CoreSys, CoreSysAttributes
from ..exceptions import DockerError, DockerJobError
from ..utils.common import FileConfiguration

_LOGGER: logging.Logger = logging.getLogger(__name__)
UNKNOWN = "unknown"


class PleovisorsAPI(CoreSysAttributes, FileConfiguration):
    """API for Pleovisors."""

    def __init__(self, coresys: CoreSys):
        """Initialize Pleovisor API object."""
        self.coresys: CoreSys = coresys
        super().__init__(FILE_HASSIO_PLEOVISORS, SCHEMA_PLEOVISORS_FILE)
        self._instances: dict[Pleovisor] = {}

    async def load(self):
        """Load PleovisorsAPI."""
        for url in self._data[ATTR_PLEOVISORS]:
            self._instances[url] = Pleovisor(
                self.coresys, url, self._data[ATTR_PLEOVISORS][url]
            )

    @property
    def instances(self) -> list[Pleovisor]:
        """Return list of all Pleovisor instances."""
        return list(self._instances.values())

    def get_instance(self, url: str) -> Pleovisor:
        """Get the first Pleovisor instance matching the url."""
        instance = self._instances.get(url, None)
        if instance is None:
            raise DockerError(
                "Couldnt find Pleovisor {url} in list of instances!",
                logger=_LOGGER.error,
            )
        return instance

    def instance_exists(self, url: str) -> bool:
        """Check whether a Pleovisor instance matching the url exists."""
        return self._instances.get(url, None) is not None

    @Job(
        name="pleovisor_add_instance",
        conditions=[JobCondition.INTERNET_SYSTEM, JobCondition.SUPERVISOR_UPDATED],
        on_condition=DockerJobError,
    )
    async def add_pleovisor(self, url: str) -> None:
        """Add a Pleovisor."""
        if url == SOCKET_DOCKER:
            raise DockerError(
                f"can't add {url}, is equal to supervisor host", _LOGGER.error
            )

        if self.instance_exists(url):
            raise DockerError(f"Can't add {url}, already added", _LOGGER.error)

        pleovisor = Pleovisor(self.coresys, url)

        # Add Pleovisor to list
        self._instances[url] = pleovisor

        self._data[ATTR_PLEOVISORS][pleovisor.url] = []
        self.save_data()

    async def remove_pleovisor(self, url: str, force_remove=False):
        """Remove a Pleovisor."""
        if url == SOCKET_DOCKER:
            raise DockerError("Can't remove Supervisors Docker!", logger=_LOGGER.error)

        pleovisor = self.get_instance(url)

        pleovisor.remove(force_remove)
        del self._instances[url]
        del self._data[ATTR_PLEOVISORS][url]
        self.save_data()

    async def add_addon(self, pleovisor: Pleovisor | None, addon: Addon):
        """Add store addon to Pleovisor."""

        if pleovisor is not None:
            await pleovisor.add_addon(addon)
            self._data[ATTR_PLEOVISORS][pleovisor.url] = pleovisor.addons_str()
            # Remove addon from other pleovisor without moving to supervisor
            for pleo_instance in self.instances:
                if addon in pleo_instance.addons:
                    pleo_instance.addons.remove(addon)
                    self._data[ATTR_PLEOVISORS][
                        pleo_instance.url
                    ] = pleo_instance.addons_str()
        else:
            # Remove addon from other pleovisor and move back to supervisor
            for pleo_instance in self.instances:
                if addon in pleo_instance.addons:
                    pleo_instance.remove_addon(addon)
                    self._data[ATTR_PLEOVISORS][
                        pleo_instance.url
                    ] = pleo_instance.addons_str()

        self.save_data()
