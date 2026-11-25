"""Konfigurationsdialog fuer Thermik."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_NAME, CONF_SENSOR, CONF_VALVE, DOMAIN


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
            vol.Required(
                CONF_VALVE, default=defaults.get(CONF_VALVE)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="climate")
            ),
            vol.Required(
                CONF_SENSOR, default=defaults.get(CONF_SENSOR)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor", device_class="temperature"
                )
            ),
        }
    )


class ThermikConfigFlow(ConfigFlow, domain=DOMAIN):
    """Raum hinzufuegen."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_VALVE])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )
        return self.async_show_form(step_id="user", data_schema=_schema())

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return ThermikOptionsFlow()


class ThermikOptionsFlow(OptionsFlow):
    """Sensor oder Ventil eines Raums aendern."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(data={})
        return self.async_show_form(
            step_id="init", data_schema=_schema(dict(self.config_entry.data))
        )
