"""Thermik: eine Thermostat-Entitaet pro Raum."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_NAME,
    CONF_SENSOR,
    CONF_VALVE,
    DEFAULT_TARGET,
    DOMAIN,
    HYSTERESIS,
    MAX_TEMP,
    MIN_TEMP,
    POLL_SECONDS,
    TARGET_STEP,
    VALVE_CLOSED,
    VALVE_OPEN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RoomThermostat(entry)])


class RoomThermostat(ClimateEntity, RestoreEntity):
    """Regelt ein Ventil nach einem externen Raumsensor."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = TARGET_STEP

    def __init__(self, entry: ConfigEntry) -> None:
        self._valve = entry.data[CONF_VALVE]
        self._sensor = entry.data[CONF_SENSOR]
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_NAME],
            manufacturer="Thermik",
        )
        self._attr_target_temperature = DEFAULT_TARGET
        self._attr_hvac_mode = HVACMode.HEAT
        self._attr_current_temperature: float | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (old := await self.async_get_last_state()) is not None:
            if old.state in (HVACMode.HEAT, HVACMode.OFF):
                self._attr_hvac_mode = HVACMode(old.state)
            if (t := old.attributes.get(ATTR_TEMPERATURE)) is not None:
                self._attr_target_temperature = float(t)

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._sensor, self._valve], self._on_change
            )
        )
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._on_tick, timedelta(seconds=POLL_SECONDS)
            )
        )
        self._read_sensor()
        await self._async_control()

    # ---- Eingaben ----

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._attr_target_temperature = float(temp)
        self.async_write_ha_state()
        await self._async_control()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()
        await self._async_control()

    # ---- Regelung ----

    @callback
    def _read_sensor(self) -> None:
        state = self.hass.states.get(self._sensor)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._attr_current_temperature = None
            return
        try:
            self._attr_current_temperature = float(state.state)
        except ValueError:
            self._attr_current_temperature = None

    async def _on_change(self, event: Event[EventStateChangedData]) -> None:
        self._read_sensor()
        self.async_write_ha_state()
        await self._async_control()

    async def _on_tick(self, _now) -> None:
        self._read_sensor()
        self.async_write_ha_state()
        await self._async_control()

    async def _async_control(self) -> None:
        """Ventil auf voll auf oder zu stellen, je nach Raumtemperatur."""
        valve = self.hass.states.get(self._valve)
        if valve is None or valve.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        if self._attr_hvac_mode == HVACMode.OFF:
            wanted = VALVE_CLOSED
        else:
            ist = self._attr_current_temperature
            soll = self._attr_target_temperature
            if ist is None or soll is None:
                return
            if ist < soll - HYSTERESIS:
                wanted = VALVE_OPEN
            elif ist >= soll:
                wanted = VALVE_CLOSED
            else:
                return  # Hysterese: Ventil unveraendert lassen

        current = valve.attributes.get(ATTR_TEMPERATURE)
        if current is not None and float(current) == wanted:
            return

        _LOGGER.debug("%s: Ventil %s auf %s", self.entity_id, self._valve, wanted)
        await self.hass.services.async_call(
            "climate",
            "set_temperature",
            {"entity_id": self._valve, ATTR_TEMPERATURE: wanted},
            blocking=False,
        )

    @property
    def hvac_action(self) -> HVACAction | None:
        if self._attr_hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        ist = self._attr_current_temperature
        soll = self._attr_target_temperature
        if ist is None or soll is None:
            return None
        return HVACAction.HEATING if ist < soll else HVACAction.IDLE
