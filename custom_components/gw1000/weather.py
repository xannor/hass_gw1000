""" GW1000 Weather Component """

import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Loading...")

from homeassistant.core import callback

import voluptuous as vol

from homeassistant.components.weather import (
    PLATFORM_SCHEMA,
    WeatherEntity,
)
from homeassistant.const import (
    CONF_WEBHOOK_ID,
    CONF_NAME,
    PRESSURE_HPA,
    PRESSURE_INHG,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    ATTR_ENTITY_ID,
    LENGTH_KILOMETERS,
    LENGTH_MILES,
    LENGTH_INCHES,
)
import homeassistant.helpers.config_validation as cv

from homeassistant.helpers.event import async_track_state_change

DEPENDENCIES = ['gw1000']

from .const import (
    DOMAIN,
    LENGTH_MILLIMETERS,
    LIGHT_WATTS,
    LIGHT_LUX
) 

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DOMAIN): cv.string,
        vol.Optional(CONF_WEBHOOK_ID): cv.string,
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the webhook."""

    name = config.get(CONF_NAME)
    webhook_id = config.get(CONF_WEBHOOK_ID, name)
    entity_id = config.get(ATTR_ENTITY_ID)

    _LOGGER.debug("Initializing Weather platform: name=%s webhook_id=%s entity_id=%s", name, webhook_id, entity_id)

    add_entities([GW1000Weather(name, webhook_id, entity_id)], True)

class GW1000Weather(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, name, webhook_id, weather_entity_id):
        self._name = name
        if weather_entity_id:
            self._tracking = tuple(ent_id.lower() for ent_id in weather_entity_id)
        else:
            self._tracking = tuple()
        self._webhook_id = webhook_id

        self._ready = False
        self._ozone = None
        self._visibility = None
        self._condition = None
        self._forecast = None
        self._attribution = None

        self._async_unsub_state_changed = None

    @property
    def should_poll(self):
        """ this is event driven so polling is unecessary """
        return False

    @property
    def available(self):
        """ return if weather data is available. """
        return self._ready

    @property
    def attribution(self):
        """Return the attribution."""
        return self._attribution

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def temperature(self):
        """Return the temperature."""
        return self._temp

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._tempUnits

    @property
    def humidity(self):
        """Return the humidity."""
        return self._humidity

    @property
    def wind_speed(self):
        """Return the wind speed."""
        return self._windspeed

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        return self._windbearing

    @property
    def ozone(self):
        """Return the ozone level."""
        return self._ozone

    @property
    def pressure(self):
        """Return the pressure."""
        return self._pressure

    @property
    def visibility(self):
        """Return the visibility."""
        return self._visibility

    @property
    def condition(self):
        """Return the weather condition."""
        return self._condition

    @property
    def forecast(self):
        """Return the forecast array."""
        return self._forecast

    async def async_added_to_hass(self):
        self.hass.components.gw1000.async_register(
            "weather", self._name, self._webhook_id, self.entity_id, self._async_handle_data
        )

        if self._tracking and self._async_unsub_state_changed is None:
            self._async_unsub_state_changed = async_track_state_change(
                self.hass, self._tracking, self._async_state_changed_listener
            )        

    async def async_will_remove_from_hass(self):
        self.hass.components.gw1000.async_unregister(
            self._webhook_id, self.entity_id
        )
        if self._async_unsub_state_changed:
            self._async_unsub_state_changed()
            self._async_unsub_state_changed = None        

    @callback
    def _async_update_weather_state(self, tr_state=None):
        """ update tracked weather state """

        if tr_state is None:
            return

        self._condition = tr_state.state
        self._ozone = tr_state.attributes['ozone']
        self._visibility = tr_state.attributes['visibility']
        self._forecast = tr_state.attributes['forecast']
        self._attribution = tr_state.attributes['attribution']

    async def _async_handle_data(self, hass, webhook_id, entity_id, results: dict):
        self._ready = True

        temp = results["outdoor"]
        self._temp = temp["temperature"]
        self._tempUnits = temp["units"]
        self._humidity = temp["humidity"]

        temp = results["pressure"]
        self._pressure = temp["absolute"]

        temp = results["wind"]
        self._windspeed = temp["speed"]
        self._windbearing = temp["bearing"]

        self.async_schedule_update_ha_state()

    async def _async_state_changed_listener(self, entity_id, old_state, new_state):
        # removed
        if self._async_unsub_state_changed is None:
            return

        self._async_update_weather_state(new_state)
        self.async_schedule_update_ha_state()

#    async def async_update(self):
#        """Get the latest data from GW1000."""
#        
#        if self._weather is None and self._weather_id is not None and len(self._weather_id) > 0:
#            weather_id = self._weather_id[0]
#            if weather_id is not None:
#                self._weather = self.hass.states.get(weather_id)
