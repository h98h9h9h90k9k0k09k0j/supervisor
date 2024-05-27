"""Validate Pleovisor schema."""

import voluptuous as vol

from supervisor.addons.validate import RE_SLUG_FIELD

from ..const import ATTR_PLEOVISORS


def validate_pleovisor(pleovisor: str) -> str:
    """Validate a valid url for pleovisor."""
    # Validate URL
    # pylint: disable=no-value-for-parameter
    vol.Url()(pleovisor)

    return pleovisor


# pylint: disable=no-value-for-parameter
SCHEMA_PLEOVISORS_FILE = vol.Schema(
    {
        vol.Optional(ATTR_PLEOVISORS, default=dict): {
            vol.Url(): [vol.All(str, vol.Match(RE_SLUG_FIELD))]
        },
    },
    extra=vol.REMOVE_EXTRA,
)
