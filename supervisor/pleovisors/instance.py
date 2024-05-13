"""Pleovisor Instance."""

import logging
from typing import Self

from supervisor.const import ATTR_ADDONS, ATTR_URL
from supervisor.docker.manager import DockerAPI
from supervisor.exceptions import DockerError

from ..coresys import CoreSys

_LOGGER: logging.Logger = logging.getLogger(__name__)


class Pleovisor:
    """Pleovisor Instance."""

    def __init__(self, coresys: CoreSys, url: str, addons: list | None = None):
        """Initialize Docker base wrapper."""
        self.docker = DockerAPI(coresys, url)
        self._url: str = url
        self.coresys = coresys
        self.addons: list = addons or []

    def to_dict(self) -> dict[str, any]:
        """Get dictionary representation."""
        return {
            self.url: self.addons,
        }

    @classmethod
    def try_from_dict(cls, coresys, data: dict[str, any]) -> Self | None:
        """Return object from dictionary representation."""
        try:
            return cls(coresys, url=data.keys[0], addons=data.items[0])
        except DockerError:
            return None

    @property
    def url(self) -> str:
        """Return repo slug."""
        return self._url

    @property
    def data(self):
        """Return data equilevant of Pleovisor."""
        return {
            ATTR_URL: self.url,
            ATTR_ADDONS: [
                container.name for container in self.docker.containers.list(all=True)
            ],
        }

    def add_addon(self, addon_image: str):
        """Add addon to Pleovisor."""
        if addon_image in self.addons:
            raise DockerError(
                "Pleovisor {self.url} already has {addon_image}",
                logger=_LOGGER.error,
            )
        self.docker.run(addon_image)

    def remove_addon(self, addon_image: str):
        """Remove addon from Pleovisor."""
        if addon_image not in self.addons:
            raise DockerError(
                "Pleovisor {self.url} does not have {addon_image}",
                logger=_LOGGER.error,
            )
        self.docker.stop_container(addon_image, timeout=10, remove_container=True)

    def remove(self, force_remove: bool = False):
        """Call to remove Pleovisor."""
        if len(self.addons) > 0:
            if not force_remove:
                raise DockerError(
                    "Couldnt remove Pleovisor {url}, because it still has addons!",
                    logger=_LOGGER.error,
                )
            for addon in self.addons:
                self.remove_addon(addon)

        self.docker.docker.close()
