"""Init file for Supervisor Home Assistant RESTful API."""

import asyncio
import logging
from typing import Any

from aiohttp import web
import voluptuous as vol

from supervisor.addons.addon import Addon
from supervisor.exceptions import APIAddonNotInstalled, APIError, DockerError
from supervisor.pleovisors.instance import Pleovisor
from supervisor.pleovisors.validate import validate_pleovisor

from ..const import ATTR_PLEOVISOR, ATTR_PLEOVISORS, REQUEST_FROM
from ..coresys import CoreSysAttributes
from .utils import api_process, api_validate

_LOGGER: logging.Logger = logging.getLogger(__name__)

SCHEMA_ADD_PLEOVISOR = vol.Schema(
    {vol.Required(ATTR_PLEOVISOR): vol.All(str, validate_pleovisor)}
)


class APIPleovisors(CoreSysAttributes):
    """Handle REST API for pleovisor."""

    def _extract_pleovisor(self, request: web.Request) -> Pleovisor | None:
        """Return repository, throw an exception it it doesn't exist."""
        pleovisor_url: str = request.match_info.get("pleovisor")
        if pleovisor_url == "supervisor":
            return None
        try:
            pleovisor = self.sys_pleovisors.get_instance(pleovisor_url)
        except DockerError:
            raise APIError(f"Pleovisor {pleovisor_url} does not exist") from DockerError
        return pleovisor

    def get_addon_for_request(self, request: web.Request) -> Addon:
        """Return addon, throw an exception if it doesn't exist."""
        addon_slug: str = request.match_info.get("addon")

        # Lookup itself
        if addon_slug == "self":
            addon = request.get(REQUEST_FROM)
            if not isinstance(addon, Addon):
                raise APIError("Self is not an Addon")
            return addon

        addon = self.sys_addons.get(addon_slug)
        if not addon:
            raise APIError(f"Addon {addon_slug} does not exist")
        if not isinstance(addon, Addon) or not addon.is_installed:
            raise APIAddonNotInstalled("Addon is not installed")

        return addon

    @api_process
    async def pleovisor_list(self, request: web.Request) -> dict[str, Any]:
        """Return all pleovisors."""
        return {
            ATTR_PLEOVISORS: [
                pleovisor.to_dict() for pleovisor in self.sys_pleovisors.instances
            ]
        }

    @api_process
    async def pleovisor_info(self, request: web.Request) -> dict[str, Any]:
        """Return Pleovisor information."""
        pleovisor: Pleovisor | None = self._extract_pleovisor(request)
        if pleovisor is None:
            raise APIError("Supervisor is not a Pleovisor.")
        return pleovisor.to_dict()

    @api_process
    async def add_pleovisor(self, request: web.Request):
        """Add Pleovisor."""
        body = await api_validate(SCHEMA_ADD_PLEOVISOR, request)
        await asyncio.shield(self.sys_pleovisors.add_pleovisor(body[ATTR_PLEOVISOR]))

    @api_process
    async def remove_pleovisor(self, request: web.Request):
        """Remove Pleovisor."""
        pleovisor_url: str = request.match_info.get("pleovisor")
        await asyncio.shield(self.sys_pleovisors.remove_pleovisor(pleovisor_url))

    @api_process
    async def add_addon(self, request: web.Request):
        """Add Pleovisor."""
        addon: Addon = self.get_addon_for_request(request)
        pleovisor: Pleovisor = self._extract_pleovisor(request)

        await asyncio.shield(self.sys_pleovisors.add_addon(pleovisor, addon))
