from datetime import timedelta
import logging
from typing import Any

import pypeblar

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, CONF_FRIENDLY_NAME, CONF_HOST
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .peblar_api_helper import PeblarApiHelper

_LOGGER = logging.getLogger(__name__)


class PeblarDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass,
        entry: ConfigEntry,
        default_interval: int,
        interval_during_charging: int,
    ):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=default_interval),
        )
        self.entry = entry
        self.entry_id = entry.entry_id

        configuration = pypeblar.Configuration(
            host=PeblarApiHelper.get_peblar_api_endpoint(entry.data[CONF_HOST]),
            api_key={"ApiToken": entry.data[CONF_API_TOKEN]},
        )
        self.api_client: pypeblar.ApiClient = pypeblar.ApiClient(configuration)

        self._sensors = []

        self._dynamic_update = False
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, self.entry_id)},
            name=self.entry.data[CONF_FRIENDLY_NAME],
            model="Peblar EV Charger",
            manufacturer="Peblar",
            sw_version="unknown",
            hw_version="unknown",
            configuration_url=entry.data[CONF_HOST],
        )

        self._default_interval = default_interval
        self._interval_during_charging = interval_during_charging

    @property
    def sensors(self) -> list[SensorEntity]:
        return self._sensors

    async def async_get_diagnostics(self) -> dict[str, Any]:
        return {
            "last_update_success": self.last_update_success,
            "last_exception": self.last_exception,
            "last_update": self.last_update_success,
            "update_interval": self.update_interval,
            "default_interval": self._default_interval,
            "interval_during_charging": self._interval_during_charging,
            "dynamic_update": self._dynamic_update,
            "entry_id": self.entry_id,
            "sensors": [sensor.name for sensor in self.sensors],
        }

    async def _async_update_data(self):
        self._sensors = []
        health_data, system_data, meter_data, ev_interface_data = {}, {}, {}, {}

        # Fetch health data
        try:
            health_data = await self.fetch_health_data()
            self._sensors.append(
                PeblarSensor(
                    self.entry,
                    self,
                    "Health Status",
                    "health",
                    health_data.api_version,
                    device_class="version",
                )
            )
            self._sensors.append(
                PeblarSensor(
                    self.entry, self, "Access Mode", "health", health_data.access_mode
                )
            )
        except Exception as e:
            _LOGGER.error(f"Failed to fetch health data: {e}")

        # Fetch system data and set device info
        try:
            system_data = await self.fetch_system_data()

            self.device_info["sw_version"] = system_data.firmware_version
            self.device_info["hw_version"] = system_data.product_pn

            # self.device_info = {
            #     "identifiers": {(DOMAIN, self.entry_id)},
            #     "name": "Peblar EV Charger",
            #     "model": "Peblar EV Charger",
            #     "manufacturer": "Peblar",
            #     "entry_type": DeviceEntryType.SERVICE,
            #     "sw_version": system_data.firmware_version,
            #     "hw_version": system_data.product_pn,
            #     "attributes": {
            #         "product_sn": system_data.product_sn,
            #         "phase_count": system_data.phase_count,
            #     },
            # }
            self._sensors.extend(
                [
                    PeblarSensor(
                        self.entry,
                        self,
                        "WLAN Signal Strength",
                        "system",
                        system_data.wlan_signal_strength,
                        unit_of_measurement="dBm",
                        device_class="signal_strength",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Cellular Signal Strength",
                        "system",
                        system_data.cellular_signal_strength,
                        unit_of_measurement="dBm",
                        device_class="signal_strength",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Uptime",
                        "system",
                        system_data.uptime,
                        unit_of_measurement="s",
                        device_class="duration",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Force 1 Phase Allowed",
                        "system",
                        system_data.force1_phase_allowed,
                    ),
                ]
            )
        except Exception as e:
            _LOGGER.error(f"Failed to fetch system data: {e}")

        # Fetch meter data
        try:
            meter_data = await self.fetch_meter_data()
            self._sensors.extend(
                [
                    PeblarSensor(
                        self.entry,
                        self,
                        "Current Phase 1",
                        "meter",
                        meter_data.current_phase1,
                        unit_of_measurement="mA",
                        device_class="current",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Current Phase 2",
                        "meter",
                        meter_data.current_phase2,
                        unit_of_measurement="mA",
                        device_class="current",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Current Phase 3",
                        "meter",
                        meter_data.current_phase3,
                        unit_of_measurement="mA",
                        device_class="current",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Voltage Phase 1",
                        "meter",
                        meter_data.voltage_phase1,
                        unit_of_measurement="V",
                        device_class="voltage",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Voltage Phase 2",
                        "meter",
                        meter_data.voltage_phase2,
                        unit_of_measurement="V",
                        device_class="voltage",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Voltage Phase 3",
                        "meter",
                        meter_data.voltage_phase3,
                        unit_of_measurement="V",
                        device_class="voltage",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Power Phase 1",
                        "meter",
                        meter_data.power_phase1,
                        unit_of_measurement="W",
                        device_class="power",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Power Phase 2",
                        "meter",
                        meter_data.power_phase2,
                        unit_of_measurement="W",
                        device_class="power",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Power Phase 3",
                        "meter",
                        meter_data.power_phase3,
                        unit_of_measurement="W",
                        device_class="power",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Power Total",
                        "meter",
                        meter_data.power_total,
                        unit_of_measurement="W",
                        device_class="power",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Energy Session",
                        "meter",
                        meter_data.energy_session,
                        unit_of_measurement="Wh",
                        device_class="energy",
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Energy Total",
                        "meter",
                        meter_data.energy_total,
                        unit_of_measurement="Wh",
                        device_class="energy",
                    ),
                ]
            )

            # Dynamic update rate adjustment based on total power so we can have acuate power readings when a car is charging but relax if it is not
            total_power = meter_data.power_total
            if total_power > 10:
                self.update_interval = timedelta(seconds=self._default_interval)
            else:
                self.update_interval = timedelta(seconds=self._interval_during_charging)
        except Exception as e:
            _LOGGER.error(f"Failed to fetch meter data: {e}")

        # Fetch EV interface data
        try:
            ev_interface_data = await self.fetch_ev_interface_data()
            self._sensors.extend(
                [
                    PeblarSensor(
                        self.entry,
                        self,
                        "EV Interface State",
                        "evInterface",
                        ev_interface_data.cp_state,
                    ),
                    PeblarSensor(
                        self.entry,
                        self,
                        "Charge Current Limit",
                        "evInterface",
                        ev_interface_data.charge_current_limit,
                        unit_of_measurement="mA",
                        device_class="current",
                    ),
                ]
            )
        except Exception as e:
            _LOGGER.error(f"Failed to fetch EV interface data: {e}")

    async def fetch_health_data(self) -> pypeblar.HealthGet200Response:
        return await pypeblar.HealthApi(self.api_client).health_get()

    async def fetch_system_data(self) -> pypeblar.SystemGet200Response:
        return await pypeblar.SystemApi(self.api_client).system_get()

    async def fetch_meter_data(self) -> pypeblar.MeterGet200Response:
        return await pypeblar.MeterApi(self.api_client).meter_get()

    async def fetch_ev_interface_data(self) -> pypeblar.EVInterfaceResponse:
        return await pypeblar.EVInterfaceApi(self.api_client).evinterface_get()


class PeblarSensor(SensorEntity):
    _attr_device_class: SensorDeviceClass | None = None
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: PeblarDataUpdateCoordinator,
        name: str,
        category,
        state,
        unit_of_measurement=None,
        device_class=None,
    ) -> None:
        """Initialize a Peblar sensor."""
        self._attr_unique_id = f"{entry.entry_id}_{name}".lower().replace(" ", "_")
        self._attr_device_info = coordinator.device_info
        self._attr_state = state
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_name = name
        self._attr_category = category
        self._state = state

        self.coordinator = coordinator

    @property
    def state(self):
        return self._state

    async def async_update(self):
        """Update the sensor."""
        try:
            await self.coordinator.async_request_refresh()
        except Exception as e:
            self._attr_available = False
            _LOGGER.error(f"Error updating sensor {self._attr_name}: {e}")
