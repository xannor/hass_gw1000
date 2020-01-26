""" Conversion Helper Routines """

import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Loading...")

from homeassistant.const import (
    PRESSURE_HPA,
    PRESSURE_INHG,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    LENGTH_INCHES,
)

from .const import (
    LENGTH_MILLIMETERS,
    LIGHT_WATTS,
    LIGHT_LUX,
    SPEED_MILES,
    SPEED_KILOMETERS,
)

CONVERT = {
    TEMP_FAHRENHEIT: {
        TEMP_CELSIUS: lambda value: (float(value) - 32) / 1.8, 
    },
    PRESSURE_INHG: {
        PRESSURE_HPA: lambda value: float(value) * 33.86389, 
    },
    SPEED_MILES: {
        SPEED_KILOMETERS: lambda value: float(value) / 0.62137, 
    },
    LENGTH_INCHES: {
        LENGTH_MILLIMETERS: lambda value: float(value) * 25.4, 
    },
    LIGHT_WATTS: {
        LIGHT_LUX: lambda value: float(value) / 0.0079, 
    },
}
