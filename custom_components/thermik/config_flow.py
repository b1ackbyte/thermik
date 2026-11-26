"""Konfigurationsdialog fuer Thermik."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AWAY_DELAY,
    CONF_AWAY_TEMP,
    CONF_ECO_TEMP,
    CONF_NAME,
    CONF_PRESENCE,
    CONF_SCHEDULE,
    CONF_SENSOR,
    CONF_VALVE,
    CONF_WINDOW_DELAY,
    CONF_WINDOWS,
    DEFAULT_AWAY_DELAY,
    DEFAULT_AWAY_TEMP,
    DEFAULT_ECO_TEMP,
    DEFAULT_WINDOW_DELAY,
    DOMAIN,
    OPTIONAL_KEYS,
)


def _temp_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=5,
            max=30,
            step=0.5,
            unit_of_measurement="°C",
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _number_selector(maximum: int, step: int, unit: str) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=maximum,
            step=step,
            unit_of_measurement=unit,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _optional(key: str, defaults: dict[str, Any]) -> vol.Optional:
    """Optionales Feld; vorhandener Wert wird nur vorgeschlagen (loeschbar)."""
    if (value := defaults.get(key)) not in (None, [], ""):
        return vol.Optional(key, description={"suggested_value": value})
    return vol.Optional(key)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME, description={"suggested_value": defaults.get(CONF_NAME, "")}
            ): str,
            vol.Required(
                CONF_VALVE, description={"suggested_value": defaults.get(CONF_VALVE)}
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="climate")
            ),
            vol.Required(
                CONF_SENSOR, description={"suggested_value": defaults.get(CONF_SENSOR)}
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor", device_class="temperature"
                )
            ),
            # Fenster-offen-Erkennung
            _optional(CONF_WINDOWS, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)
            ),
            vol.Optional(
                CONF_WINDOW_DELAY,
                default=defaults.get(CONF_WINDOW_DELAY, DEFAULT_WINDOW_DELAY),
            ): _number_selector(60, 1, "min"),
            # Zeitplan (Schedule-Helfer: an = Komfort, aus = Absenkung)
            _optional(CONF_SCHEDULE, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="schedule")
            ),
            vol.Optional(
                CONF_ECO_TEMP, default=defaults.get(CONF_ECO_TEMP, DEFAULT_ECO_TEMP)
            ): _temp_selector(),
            # Anwesenheit
            _optional(CONF_PRESENCE, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["person", "device_tracker"], multiple=True
                )
            ),
            vol.Optional(
                CONF_AWAY_TEMP, default=defaults.get(CONF_AWAY_TEMP, DEFAULT_AWAY_TEMP)
            ): _temp_selector(),
            vol.Optional(
                CONF_AWAY_DELAY,
                default=defaults.get(CONF_AWAY_DELAY, DEFAULT_AWAY_DELAY),
            ): _number_selector(240, 5, "min"),
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
    """Einstellungen eines Raums aendern."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            # Optionale Felder, die leer gelassen wurden, wirklich entfernen
            data = {
                k: v
                for k, v in self.config_entry.data.items()
                if k not in OPTIONAL_KEYS
            }
            data.update(user_input)
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)
            return self.async_create_entry(data={})
        return self.async_show_form(
            step_id="init", data_schema=_schema(dict(self.config_entry.data))
        )
