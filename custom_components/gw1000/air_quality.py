""" GW1000 Air Quality Platform """

import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Loading...")

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.air_quality import PLATFORM_SCHEMA, AirQualityEntity

from homeassistant.const import (
    CONF_WEBHOOK_ID,
    CONF_NAME,
    ATTR_ATTRIBUTION,
    CONF_ENTITY_NAMESPACE,
)
from homeassistant.core import callback

from homeassistant.helpers.entity import Entity, generate_entity_id

from homeassistant.helpers.icon import icon_for_battery_level

from . import (
    GW1000EntityFactory
)

from .const import (
    DOMAIN
)

from .conversions import (
    CONVERT
)

DEPENDENCIES = ['gw1000']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DOMAIN): cv.string,
        vol.Optional(CONF_WEBHOOK_ID): cv.string,
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the webhook."""

    name = config.get(CONF_NAME)
    webhook_id = config.get(CONF_WEBHOOK_ID, name)

    _LOGGER.debug("Initializing Air Quality platform: name=%s webhook_id=%s", name, webhook_id)

    factory = GW1000AirQualityEntityFactory(hass, add_entities, webhook_id)
    #add_entities([GW1000PM25(name, webhook_id)], True)

class GW1000AirQualityEntityFactory(GW1000EntityFactory):
    """Air Quality Factory"""

    def __init__(self, hass, add_entities, webhook_id):
        super().__init__(hass, add_entities, "air_quality", "factory", "air", webhook_id)

    async def _async_handle_data(self, hass, webhook_id, entity_id, results: dict):



class GW1000PM25(AirQualityEntity):
    """Representation of an air quality sensor."""

    def __init__(self, name, webhook_id):
        """Initialize the entity."""
        self._name = name
        self._webhook_id = webhook_id

        self._ready = False
        self._units = "μg/m3"
        self._pm25 = None

    @property
    def should_poll(self):
        """ this is event driven so polling is unecessary """
        return False

    @property
    def available(self):
        """ return if weather data is available. """
        return self._ready

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._units

    @property
    def particulate_matter_2_5(self):
        """Return the particulate matter 2.5 level."""
        return self._pm25

    async def async_added_to_hass(self):
        self.hass.components.gw1000.async_register(
            "air_quality", self._name, self._webhook_id, self.entity_id, self._async_handle_data
        )

    async def async_will_remove_from_hass(self):
        self.hass.components.gw1000.async_unregister(
            self._webhook_id, self.entity_id
        )

    async def _async_handle_data(self, hass, webhook_id, entity_id, results: dict):
        self._ready = True

