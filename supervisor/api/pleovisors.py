"""Init file for Supervisor Home Assistant RESTful API."""

import asyncio
import logging
from typing import Any

from aiohttp import web
import voluptuous as vol

from supervisor.addons.addon import Addon
from supervisor.addons.manager import AnyAddon
from supervisor.exceptions import APIError, DockerError
from supervisor.pleovisors.instance import Pleovisor
from supervisor.pleovisors.validate import validate_pleovisor

from ..const import ATTR_ADDONS, ATTR_PLEOVISOR, ATTR_URL
from ..coresys import CoreSysAttributes
from .utils import api_process, api_validate

_LOGGER: logging.Logger = logging.getLogger(__name__)

SCHEMA_ADD_PLEOVISOR = vol.Schema(
    {vol.Required(ATTR_PLEOVISOR): vol.All(str, validate_pleovisor)}
)


class APIPleovisors(CoreSysAttributes):
    """Handle REST API for pleovisor."""

    def _extract_pleovisor(self, request: web.Request) -> Pleovisor:
        """Return repository, throw an exception it it doesn't exist."""
        pleovisor_url: str = request.match_info.get("pleovisor")
        pleovisor = self.sys_pleovisors.get(pleovisor_url)
        if not pleovisor:
            raise APIError(f"Pleovisor {pleovisor_url} does not exist")

    def _generate_pleovisor_information(self, pleovisor: Pleovisor) -> dict[str, Any]:
        """Generate repository information."""
        return {ATTR_URL: pleovisor.url, ATTR_ADDONS: pleovisor.addons}

    @api_process
    async def pleovisor_list(self, request: web.Request) -> list[dict[str, Any]]:
        """Return all pleovisors."""
        return [
            self._generate_pleovisor_information(pleovisor)
            for pleovisor in self.sys_pleovisors.all_pleovisors
        ]

    @api_process
    async def pleovisor_info(self, request: web.Request) -> dict[str, Any]:
        """Return Pleovisor information."""
        pleovisor: Pleovisor = self._extract_pleovisor(request)
        return self._generate_pleovisor_information(pleovisor)

    @api_process
    async def add_pleovisor(self, request: web.Request):
        """Add Pleovisor."""
        body = await api_validate(SCHEMA_ADD_PLEOVISOR, request)
        await asyncio.shield(self.sys_pleovisors.add_pleovisor(body[ATTR_PLEOVISOR]))

    @api_process
    async def remove_pleovisor(self, request: web.Request):
        """Remove Pleovisor."""
        pleovisor: Pleovisor = self._extract_pleovisor(request)
        await asyncio.shield(self.sys_pleovisors.remove_pleovisor(pleovisor))

    @api_process
    async def add_addon(self, request: web.Request):
        """Add Pleovisor."""
        addon_slug: str = request.match_info.get("addon")
        addon: AnyAddon | None = self.coresys.addons.get(addon_slug)
        if addon is None:
            raise APIError("Couldn't find addon {addon_slug}")
        if addon is Addon:  # Opposed to AddonStore
            raise DockerError("Addon {addon_slug} is a Core addon")
        pleovisor: Pleovisor = self._extract_pleovisor(request)

        await asyncio.shield(self.sys_pleovisors.add_addon(pleovisor, addon))
