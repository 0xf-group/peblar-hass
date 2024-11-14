"""Config flow to configure Peblar component."""

import logging
from typing import Optional

from aiohttp import ClientConnectionError
from pypeblar import ApiClient, ApiError, Configuration, HealthApi, SystemApi
import voluptuous as vol

from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.config_entries import (
    CONN_CLASS_LOCAL_POLL,
    HANDLERS,
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_FRIENDLY_NAME,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
)

# from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_SCAN_INTERVAL_WHILE_CHARGING,
    DEFAULT_FRIENDLY_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_WHILE_CHARGING,
    DOMAIN,
    SUPPORTED_PEBLAR_API_VERSION,
)
from .peblar_api_helper import PeblarApiHelper

_LOGGER = logging.getLogger(__name__)


@HANDLERS.register(DOMAIN)
class PeblarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Peblar config flow"""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Set up the config flow."""

        self.data = {}
        self.entry = {}

    async def async_step_user(self, user_input: Optional[ConfigType] = None):
        """Handle a flow start."""
        errors = {}

        defaults = {
            CONF_FRIENDLY_NAME: DEFAULT_FRIENDLY_NAME,
            CONF_HOST: "",
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_SCAN_INTERVAL_WHILE_CHARGING: DEFAULT_SCAN_INTERVAL_WHILE_CHARGING,
        }

        if hasattr(self, "data"):
            defaults.update(
                {
                    CONF_FRIENDLY_NAME: self.data.get(
                        CONF_FRIENDLY_NAME, DEFAULT_FRIENDLY_NAME
                    ),
                    CONF_HOST: self.data.get(CONF_HOST, ""),
                    CONF_SCAN_INTERVAL: self.data.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                    CONF_SCAN_INTERVAL_WHILE_CHARGING: self.data.get(
                        CONF_SCAN_INTERVAL_WHILE_CHARGING,
                        DEFAULT_SCAN_INTERVAL_WHILE_CHARGING,
                    ),
                }
            )

        if user_input is not None:
            scan_interval = user_input[CONF_SCAN_INTERVAL]
            scan_interval_while_charging = user_input[CONF_SCAN_INTERVAL_WHILE_CHARGING]

            # Validate intervals
            if scan_interval < 1:
                errors["base"] = "scan_interval_invalid"
            if scan_interval_while_charging < 1:
                errors["base"] = "scan_interval_while_charging_invalid"

            # Configure API connection settings
            peblar_host = PeblarApiHelper.get_peblar_api_endpoint(user_input[CONF_HOST])
            peblar_api_key = user_input[CONF_API_TOKEN]
            friendly_name = (
                user_input[CONF_FRIENDLY_NAME].strip() or DEFAULT_FRIENDLY_NAME
            )

            try:
                configuration = Configuration(
                    host=peblar_host, api_key={"ApiToken": peblar_api_key}
                )
                client = ApiClient(configuration)

                _LOGGER.debug("Trying to connect to Peblar API on %s", peblar_host)

                health_response = await HealthApi(client).health_get()
                if health_response.api_version != SUPPORTED_PEBLAR_API_VERSION:
                    errors["base"] = "unsupported_api_version"
                    _LOGGER.debug("Unsupported API version")

                system_response = await SystemApi(client).system_get()
                _LOGGER.debug(
                    "System response after initial config flow check: %s",
                    system_response,
                )

                return self.async_create_entry(
                    title=friendly_name,
                    data={
                        CONF_FRIENDLY_NAME: friendly_name,
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_API_TOKEN: peblar_api_key,
                        CONF_SCAN_INTERVAL: scan_interval,
                        CONF_SCAN_INTERVAL_WHILE_CHARGING: scan_interval_while_charging,
                    },
                )

            except (ApiError, ConnectionRefusedError, ClientConnectionError):
                errors["base"] = "connection_failure"
                _LOGGER.debug("Connection failure during API connection")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_FRIENDLY_NAME, default=defaults.get(CONF_FRIENDLY_NAME)
                    ): str,
                    vol.Required(CONF_HOST, default=defaults.get(CONF_HOST)): str,
                    vol.Required(CONF_API_TOKEN): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=defaults.get(CONF_SCAN_INTERVAL)
                    ): int,
                    vol.Optional(
                        CONF_SCAN_INTERVAL_WHILE_CHARGING,
                        default=defaults.get(CONF_SCAN_INTERVAL_WHILE_CHARGING),
                    ): int,
                }
            ),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""

        if (
            not discovery_info.name.startswith("PBLR")
            or discovery_info.type != "_http._tcp.local."
        ):
            return self.async_abort(reason="not_peblar_device")

        if discovery_info.ip_address.version == 6:
            return self.async_abort(reason="ipv6_not_supported")

        _LOGGER.debug("Discovered Peblar device: %s", discovery_info)

        # Extract the friendly name and set unique ID for the device
        friendly_name = discovery_info.name.split("._")[0]
        await self.async_set_unique_id(friendly_name)
        self._abort_if_unique_id_configured()

        # Prepare context and stored data for when the user clicks "configure"
        self.context["title_placeholders"] = {"name": friendly_name}
        self.data = {
            CONF_FRIENDLY_NAME: friendly_name,
            CONF_HOST: f"http://{discovery_info.host}:{discovery_info.port}",
        }

        # Show the discovered button to the user
        return self.async_show_form(step_id="user")
