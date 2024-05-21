"""Pleovisor Instance."""

import asyncio
import logging

from supervisor.addons.addon import Addon
from supervisor.const import ATTR_ADDONS, ATTR_URL
from supervisor.docker.manager import DockerAPI
from supervisor.exceptions import DockerError

from ..coresys import CoreSys, CoreSysAttributes

_LOGGER: logging.Logger = logging.getLogger(__name__)


class Pleovisor(CoreSysAttributes):
    """Pleovisor Instance."""

    def __init__(self, coresys: CoreSys, url: str, addons: list | None = None):
        """Initialize Docker base wrapper."""
        self.docker = DockerAPI(coresys, url)
        self._url: str = url
        self.coresys = coresys
        self.addons: list[Addon] = []
        if addons is not None:
            for addon_str in addons:
                asyncio.shield(self._init_addon(addon_str))

    async def _init_addon(self, addon_slug: str) -> Addon:
        """Init addon from string."""
        addon = self.sys_addons.get(addon_slug)
        if not addon:
            raise DockerError(f"Addon {addon_slug} does not exist")
        if not isinstance(addon, Addon) or not addon.is_installed:
            raise DockerError("Addon is not installed")
        await self.add_addon(addon)

    def addons_str(self):
        """Return list of strings."""
        return [addon.slug for addon in self.addons]

    def to_dict(self) -> dict[str, any]:
        """Get dictionary representation."""
        return {
            self.url: self.addons_str(),
        }

    @property
    def url(self) -> str:
        """Return repo slug."""
        return self._url

    @property
    def data(self):
        """Return data equilevant of Pleovisor."""
        return {
            ATTR_URL: self.url,
            ATTR_ADDONS: [addon.slug for addon in self.addons],
        }

    async def add_addon(self, addon: Addon):
        """Add addon to Pleovisor."""
        if addon in self.addons:
            raise DockerError(
                "Pleovisor {self.url} already has {addon}",
                logger=_LOGGER.error,
            )
        self.addons.append(addon)
        await addon.move(self.docker)

    def remove_addon(self, addon: Addon):
        """Remove addon from Pleovisor and restart it at Supervisor."""
        if addon not in self.addons:
            return
        self.addons.remove(addon)
        addon.move(None)

    def remove(self, force_remove: bool = False):
        """Call to remove Pleovisor."""
        if len(self.addons) > 0:
            if not force_remove:
                raise DockerError(
                    "Couldnt remove Pleovisor {self.url}, because it still has addons!",
                    logger=_LOGGER.error,
                )
            for addon in self.addons:
                self.remove_addon(addon)

        self.docker.docker.close()
