""" GW1000 Sensor Platform """

import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Loading...")

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.sensor import ENTITY_ID_FORMAT, PLATFORM_SCHEMA

from homeassistant.const import (
    CONF_WEBHOOK_ID,
    ATTR_ATTRIBUTION,
    CONF_ENTITY_NAMESPACE,
    CONF_MONITORED_CONDITIONS,
)
from homeassistant.core import callback

from homeassistant.helpers.entity import Entity, generate_entity_id

from homeassistant.helpers.icon import icon_for_battery_level

from .const import (
    DOMAIN,
    DEFAULT_ENTITY_NAMESPACE,
    LENGTH_MILLIMETERS,
    LIGHT_WATTS,
    LIGHT_LUX
)

from .conversions import (
    CONVERT
)

DEPENDENCIES = ['gw1000']

# Sensor types: Name, units, class, icon, key, part
SENSOR_TYPES = {
    "uv": ("uv", "Index", None, None, "solar", "uv"),
    "solarradiation": ("Solar Rad", LIGHT_LUX, "illuminance", None, "solar", "radiation"),
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(
            CONF_ENTITY_NAMESPACE, default=DEFAULT_ENTITY_NAMESPACE
        ): cv.string,
        vol.Optional(CONF_WEBHOOK_ID): cv.string,
        vol.Required(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        ),
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensors."""

    _LOGGER.debug('Start')

    namespace = config.get(CONF_ENTITY_NAMESPACE)
    webhook_id = config.get(CONF_WEBHOOK_ID, namespace)

    _LOGGER.debug("Initializing Sensor platform: namespace=%s webhook_id=%s", namespace, webhook_id)

    sensors = []    
    for sensor_type in config[CONF_MONITORED_CONDITIONS]:
        sensors.append(GW1000Sensor(hass, namespace, webhook_id, sensor_type))

    _LOGGER.debug("Initialized %s entities", len(sensors))

    add_entities(sensors, True)

class GW1000Sensor(Entity):
    """ GW1000 Sensor """

    def __init__(self, hass, namespace, webhook_id, sensor_type):
        """ Initialize Sensor """
        
        self._sensor_type = sensor_type
        self._name = SENSOR_TYPES[sensor_type][0]
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, '{} {}'.format(namespace, SENSOR_TYPES[sensor_type][0]), hass=hass)
        self._icon = "mdi:{}".format(SENSOR_TYPES.get(sensor_type)[3])
        self._key = SENSOR_TYPES[sensor_type][4]
        self._part = SENSOR_TYPES[sensor_type][5]
        self._device_class = SENSOR_TYPES[sensor_type][2]
        self._units = SENSOR_TYPES[sensor_type][1]
        self._ready = False
        self._webhook_id = webhook_id

    async def async_added_to_hass(self):
        self.hass.components.gw1000.async_register(
            "sensor", self._name, self._webhook_id, self.entity_id, self._async_handle_data
        )

    async def async_will_remove_from_hass(self):
        self.hass.components.gw1000.async_unregister(
            self._webhook_id, self.entity_id
        )

    async def _async_handle_data(self, hass, webhook_id, entity_id, results: dict):
        self._ready = True

        block = results.get(self._key, {})
        value = block.get(self._part)
        convert = CONVERT.get(block.get("units"), {}).get(self._units)
        if convert is not None:
            value = convert(value)
        self._state = value

        self.async_schedule_update_ha_state()

    @property
    def should_poll(self):
        """ this is event driven so polling is unecessary """
        return False

    @property
    def available(self):
        """ return if weather data is available. """
        return self._ready

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if self._sensor_type == "battery" and self._state is not None:
            return icon_for_battery_level(
                battery_level=int(self._state), charging=False
            )
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._units
    
    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class
