"""Validate Pleovisor schema."""

import voluptuous as vol

from supervisor.addons.validate import RE_SLUG_FIELD

from ..const import ATTR_ADDONS, ATTR_PLEOVISORS, ATTR_URL


def validate_pleovisor(pleovisor: str) -> str:
    """Validate a valid url for pleovisor."""
    # Validate URL
    # pylint: disable=no-value-for-parameter
    vol.Url()(pleovisor)

    return pleovisor


# pylint: disable=no-value-for-parameter
SCHEMA_PLEOVISOR = vol.Schema(
    {
        vol.Required(ATTR_URL): vol.Url(),
        vol.Optional(ATTR_ADDONS, default=list): [vol.Match(RE_SLUG_FIELD)],
    },
    extra=vol.REMOVE_EXTRA,
)

SCHEMA_PLEOVISORS_FILE = vol.Schema(
    {
        vol.Optional(ATTR_PLEOVISORS, default=list): [SCHEMA_PLEOVISOR],
    },
    extra=vol.REMOVE_EXTRA,
)
