"""Config Flow for Presence-based Lights."""


import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import light
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import callback

from . import (
    CONF_DEVICE_GROUP,
    CONF_DISABLE_TURN_OFF,
    CONF_LIGHT_GROUP,
    CONF_LIGHT_PROFILE,
    DOMAIN,
)

LIGHT_PROFILES = "light_profiles"
CONF_DEVICE_DOMAINS = ["device_tracker", "group", "person"]
CONF_LIGHT_DOMAINS = ["group", "light"]


class PresenceBasedLightsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Hive config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN

    def __init__(self):
        """Initialize the config flow."""

    async def async_step_user(self, user_input=None):
        """Prompt user input. Create or edit entry."""
        errors = {}
        profiles = light.Profiles(self.hass)
        profile_list = []
        await profiles.async_initialize()
        for key in dict(profiles.data):
            profile_list.append(key)
        # Login to Hive with user data.
        if user_input is not None:
            unique_id = (
                f"{user_input[CONF_DEVICE_GROUP]}-{user_input[CONF_LIGHT_GROUP]}"
            )
            self.entry = await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            name = (
                f"{self.hass.states.get(user_input[CONF_DEVICE_GROUP]).name} -"
                f" {self.hass.states.get(user_input[CONF_LIGHT_GROUP]).name}"
            )

            return self.async_create_entry(
                title=name,
                data={**user_input, LIGHT_PROFILES: profile_list},
            )

        light_group_entities = _async_get_matching_entities(
            self.hass,
            domains=CONF_LIGHT_DOMAINS,
        )
        device_group_entities = _async_get_matching_entities(
            self.hass,
            domains=CONF_DEVICE_DOMAINS,
        )
        # Show User Input form.
        schema = vol.Schema(
            {
                vol.Optional(CONF_DEVICE_GROUP): vol.In(device_group_entities),
                vol.Optional(CONF_LIGHT_GROUP): vol.In(light_group_entities),
                vol.Optional(CONF_LIGHT_PROFILE, default="relax"): vol.In(profile_list),
                vol.Optional(CONF_DISABLE_TURN_OFF, default=False): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, user_input=None):
        """Import user."""
        return await self.async_step_user(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Hive options callback."""
        return PresenceBasedLightsOptionsFlowHandler(config_entry)


class PresenceBasedLightsOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for Hive."""

    def __init__(self, config):
        """Initialize Hive options flow."""
        self.light_profile = config.options.get(
            CONF_LIGHT_PROFILE, config.data.get(CONF_LIGHT_PROFILE)
        )
        self.disable_turn_off = config.options.get(
            CONF_DISABLE_TURN_OFF, config.data.get(CONF_DISABLE_TURN_OFF)
        )
        self.light_profiles = config.data.get(LIGHT_PROFILES)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(CONF_LIGHT_PROFILE, default=self.light_profile): vol.In(
                    self.light_profiles
                ),
                vol.Optional(
                    CONF_DISABLE_TURN_OFF, default=self.disable_turn_off
                ): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


def _async_get_matching_entities(hass, domains=None):
    """Fetch all entities or entities in the given domains."""
    return {
        state.entity_id: f"{state.attributes.get(ATTR_FRIENDLY_NAME, state.entity_id)} ({state.entity_id})"
        for state in sorted(
            hass.states.async_all(domains and set(domains)),
            key=lambda item: item.entity_id,
        )
    }
