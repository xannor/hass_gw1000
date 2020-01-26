"""Support for Ecowitt GW1000 data push"""

import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Loading...")

import asyncio

from homeassistant.core import callback
from homeassistant.loader import bind_hass

from aiohttp.web import Request

from homeassistant.const import (
    PRESSURE_HPA,
    PRESSURE_INHG,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    LENGTH_INCHES,
)

from .const import (
    DOMAIN,
    LENGTH_MILLIMETERS,
    LIGHT_WATTS,
    LIGHT_LUX,
    SPEED_MILES,
    SPEED_KILOMETERS,
) 

DEPENDENCIES = ['webhook']

@callback
@bind_hass
def async_register(hass, domain, name, webhook_id, entity_id, handler):
    hooks = hass.data.setdefault(DOMAIN, {})

    if not webhook_id in hooks:
        _LOGGER.info("Registering Webhook %s", webhook_id)
        hass.components.webhook.async_register(
            DOMAIN, DOMAIN + "DATA", webhook_id, async_handle_webook
        )

    handlers = hooks.setdefault(webhook_id, {})

    if entity_id in handlers:
        raise ValueError("Handler is already defined!")

    _LOGGER.info("Registered Webhook %s handler %s", webhook_id, entity_id)
    handlers[entity_id] = { "domain": domain, "name": name, "handler": handler }


@callback
@bind_hass
def async_unregister(hass, webhook_id, entity_id):
    """ remove webhook """

    _LOGGER.info("Unregistering Webhook %s handler %s", webhook_id, entity_id)

    hooks = hass.data.setdefault(DOMAIN, {})
    handlers = hooks.get(webhook_id, {})
    handlers.pop(entity_id, None)
    if len(handlers) == 0:
        _LOGGER.info("Unregistering Webhook %s", webhook_id)
        hooks.pop(webhook_id, None)
        hass.components.webhook.async_unregister(webhook_id)

@bind_hass
async def async_handle_webook(hass, webhook_id, request: Request):
    """ process data push """

    _LOGGER.debug("Webhook %s handler firing", webhook_id)

    hooks = hass.data.get(DOMAIN)
    if webhook_id not in hooks:
        return
    
    handlers = hooks.get(webhook_id)
    if not handlers:
        return

    post = await request.post()
    results = {
        "key": post['PASSKEY'],
        "stationtype": post['stationtype'],
        "dateutc": post['dateutc'],
        "freq": post['freq'],
        "model": post['model'],
        "indoor": {
            "units": TEMP_FAHRENHEIT,
            "temperature": float(post['tempinf']),
            "humidity": int(post['humidityin']),
        },
        "outdoor": {
            "units": TEMP_FAHRENHEIT,
            "temperature": float(post['tempf']),
            "humidity": int(post['humidity']),
        },
        "pressure": {
            "units": PRESSURE_INHG,
            "relative": float(post['baromrelin']),
            "absolute": float(post['baromabsin'])
        },
        "rain": {
            "units": LENGTH_INCHES,
            "rate": float(post['rainratein']),
            "event": float(post['eventrainin']),
            "hourly": float(post['hourlyrainin']),
            "daily": float(post['dailyrainin']),
            "weekly": float(post['weeklyrainin']),
            "monthly": float(post['monthlyrainin']),
            "yearly": float(post['yearlyrainin']),
            "total": float(post['totalrainin']),
        },
        "wind": {
            "units": SPEED_MILES,
            "bearing": int(post['winddir']),
            "speed": float(post['windspeedmph']),
            "gust": float(post['windgustmph']),
            "maxgust": float(post['maxdailygust']),
        },
        "solar": {
            "units": LIGHT_WATTS,
            "radiation": float(post['solarradiation']),
            "uv": int(post['uv']),
        },
#        "temperature": {},
#        "air": {},
#        "soil": {},
#        "lightning": {},
#        "leak": {},
    }

    for i in range(1,9):
        temp = post.get('temp{}f'.format(i))
        if temp is not None:
            results.setdefault("temperature", {})[format(i)] = {
                    "id": i, 
                    "temperature": temp, 
                    "humidity": int(post['humidity{}'.format(i)]), 
                    "lowbatt": post['batt{}'.format(i)] != '0' 
                }

    for i in range(1,5):
        air = post.get('pm25_ch{}'.format(i))
        if air is not None:
            results.setdefault("air", {})[format(i)] = {
                "id": i, 
                "current": float(air),
                "avg_24h": float(post['pm25_avg_24h_ch{}'.format(i)]),
                "battery": (int(post['pm25batt{}'.format(i)]) / 5) * 100
            }

    batt = post.get('wh65batt')
    if batt is not None:
        batt = batt != '0'
        results['outdoor']['lowbatt'] = batt
        results['rain']['lowbatt'] = batt
        results['wind']['lowbatt'] = batt

    _LOGGER.debug("Webhook %s handler fired: %s", webhook_id, results)

    await asyncio.wait([handlers[entity_id]["handler"](hass, webhook_id, entity_id, results) for entity_id in handlers])

async def async_setup(hass, config):
    """Set up the gw1000 platform."""

    _LOGGER.debug("Initialized module")

    return True

class GW1000EntityFactory(object):

    """Factory to create/remove entities based on webhook data """

    def __init__(self, hass, add_entities, domain, name, webhook_id):
        self._domain = domain
        self._name = name
        self._webhook_id = webhook_id
        self._add_entities = add_entities
        self.entities = {}

        hass.components.gw1000.async_register(
            self._domain, self._name, self._webhook_id, "factory", self._async_handle_data
        )

    async def _async_handle_data(self, hass, webhook_id, entity_id, results: dict):
