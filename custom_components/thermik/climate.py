"""Thermik: eine Thermostat-Entitaet pro Raum."""
from __future__ import annotations

from datetime import datetime, timedelta
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
    STATE_HOME,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

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
    DEFAULT_TARGET,
    DEFAULT_WINDOW_DELAY,
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
    """Regelt ein Ventil nach einem externen Raumsensor.

    Optional: Fenster-offen (Ventil zu), Zeitplan (Absenkung) und
    Anwesenheit (Absenkung, wenn niemand zu Hause ist).
    """

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
        data = entry.data
        self._valve = data[CONF_VALVE]
        self._sensor = data[CONF_SENSOR]

        self._windows: list[str] = list(data.get(CONF_WINDOWS) or [])
        self._window_delay = float(data.get(CONF_WINDOW_DELAY, DEFAULT_WINDOW_DELAY)) * 60  # intern Sekunden

        self._schedule: str | None = data.get(CONF_SCHEDULE) or None
        self._eco_temp = float(data.get(CONF_ECO_TEMP, DEFAULT_ECO_TEMP))

        self._presence: list[str] = list(data.get(CONF_PRESENCE) or [])
        self._away_temp = float(data.get(CONF_AWAY_TEMP, DEFAULT_AWAY_TEMP))
        self._away_delay = int(data.get(CONF_AWAY_DELAY, DEFAULT_AWAY_DELAY))

        self._window_open_since: datetime | None = None
        self._away_since: datetime | None = None
        self._recheck_unsub = None

        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=data[CONF_NAME],
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

        tracked = [self._sensor, self._valve, *self._windows, *self._presence]
        if self._schedule:
            tracked.append(self._schedule)

        self.async_on_remove(
            async_track_state_change_event(self.hass, tracked, self._on_change)
        )
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._on_tick, timedelta(seconds=POLL_SECONDS)
            )
        )
        self._read_sensor()
        self._update_flags()
        await self._async_control()
        self._schedule_recheck()

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_recheck()
        await super().async_will_remove_from_hass()

    # ---- Eingaben ----

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._attr_target_temperature = float(temp)
        await self._async_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        self._attr_hvac_mode = hvac_mode
        await self._async_refresh()

    # ---- Zustaende einlesen ----

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

    def _any_window_open(self) -> bool:
        for entity_id in self._windows:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state == STATE_ON:
                return True
        return False

    def _everyone_away(self) -> bool:
        """Alle bekannten Personen/Tracker sind nicht zu Hause."""
        if not self._presence:
            return False
        known = []
        for entity_id in self._presence:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in (
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                known.append(state.state)
        if not known:
            return False  # nichts bekannt: lieber normal heizen
        return all(s != STATE_HOME for s in known)

    def _schedule_is_off(self) -> bool:
        if not self._schedule:
            return False
        state = self.hass.states.get(self._schedule)
        return state is not None and state.state == STATE_OFF

    @callback
    def _update_flags(self) -> None:
        """Zeitstempel fuer Fenster-offen und Abwesenheit pflegen."""
        now = dt_util.utcnow()

        if self._any_window_open():
            if self._window_open_since is None:
                self._window_open_since = now
        else:
            self._window_open_since = None

        if self._everyone_away():
            if self._away_since is None:
                self._away_since = now
        else:
            self._away_since = None

    # ---- abgeleitete Werte ----

    @property
    def _window_blocked(self) -> bool:
        """Fenster ist laenger als die Verzoegerung offen."""
        if self._window_open_since is None:
            return False
        waited = (dt_util.utcnow() - self._window_open_since).total_seconds()
        return waited >= self._window_delay

    @property
    def _away_active(self) -> bool:
        """Niemand zu Hause, und zwar laenger als die Verzoegerung."""
        if self._away_since is None:
            return False
        waited = (dt_util.utcnow() - self._away_since).total_seconds()
        return waited >= self._away_delay * 60

    @property
    def _effective_target(self) -> float | None:
        """Soll-Temperatur nach Zeitplan und Anwesenheit."""
        soll = self._attr_target_temperature
        if soll is None:
            return None
        if self._schedule_is_off():
            soll = min(soll, self._eco_temp)
        if self._away_active:
            soll = min(soll, self._away_temp)
        return soll

    # ---- Ereignisse ----

    async def _async_refresh(self) -> None:
        self._read_sensor()
        self._update_flags()
        self.async_write_ha_state()
        await self._async_control()
        self._schedule_recheck()

    async def _on_change(self, event: Event[EventStateChangedData]) -> None:
        await self._async_refresh()

    async def _on_tick(self, _now) -> None:
        await self._async_refresh()

    async def _on_recheck(self, _now) -> None:
        self._recheck_unsub = None
        await self._async_refresh()

    def _cancel_recheck(self) -> None:
        if self._recheck_unsub is not None:
            self._recheck_unsub()
            self._recheck_unsub = None

    @callback
    def _schedule_recheck(self) -> None:
        """Genau zum Ablauf der Fenster-/Abwesenheits-Verzoegerung neu pruefen."""
        self._cancel_recheck()
        now = dt_util.utcnow()
        waits: list[float] = []
        if self._window_open_since is not None and not self._window_blocked:
            waits.append(
                self._window_delay - (now - self._window_open_since).total_seconds()
            )
        if self._away_since is not None and not self._away_active:
            waits.append(
                self._away_delay * 60 - (now - self._away_since).total_seconds()
            )
        if waits:
            self._recheck_unsub = async_call_later(
                self.hass, max(1.0, min(waits)) + 0.5, self._on_recheck
            )

    # ---- Regelung ----

    async def _async_control(self) -> None:
        """Ventil auf voll auf oder zu stellen, je nach Raumtemperatur."""
        valve = self.hass.states.get(self._valve)
        if valve is None or valve.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        if self._attr_hvac_mode == HVACMode.OFF or self._window_blocked:
            wanted = VALVE_CLOSED
        else:
            ist = self._attr_current_temperature
            soll = self._effective_target
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
        if self._window_blocked:
            return HVACAction.IDLE
        ist = self._attr_current_temperature
        soll = self._effective_target
        if ist is None or soll is None:
            return None
        return HVACAction.HEATING if ist < soll else HVACAction.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"effective_target": self._effective_target}
        if self._windows:
            attrs["window_open"] = self._window_blocked
        if self._schedule:
            attrs["schedule_eco"] = self._schedule_is_off()
        if self._presence:
            attrs["away"] = self._away_active
        return attrs
