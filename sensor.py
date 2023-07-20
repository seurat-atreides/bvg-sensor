"""Sensor for the Berlin BVG data."""

from urllib.request import urlopen
import json
import pytz

import os.path

from datetime import datetime, timedelta
from urllib.error import URLError

import logging
import voluptuous as vol
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA

_LOGGER = logging.getLogger(__name__)

ATTR_STOP_ID = "stop_id"
ATTR_STOP_NAME = "stop_name"
ATTR_DUE_IN = "due_in"
ATTR_REAL_TIME = "departure_time"
ATTR_DESTINATION_NAME = "direction"
ATTR_TRANS_TYPE = "type"
ATTR_TRIP_ID = "trip"
ATTR_LINE_NAME = "line_namdirectione"
ATTR_CONNECTION_STATE = "connection_status"

CONF_NAME = "name"
CONF_STOP_ID = "stop_id"
CONF_DIRECTION_ID = "direction_id"
CONF_MIN_DUE_IN = "walking_distance"
CONF_CACHE_PATH = "file_path"
CONF_CACHE_SIZE = "cache_size"

CONNECTION_STATE = "connection_state"
CON_STATE_ONLINE = "online"
CON_STATE_OFFLINE = "offline"
CON_REST_URL = "https://v6.bvg.transport.rest"

ICONS = {
    "suburban": "mdi:subway-variant",
    "subway": "mdi:subway",
    "tram": "mdi:tram",
    "bus": "mdi:bus",
    "regional": "mdi:train",
    "ferry": "mdi:ferry",
    "express": "mdi:train",
    "n/a": "mdi:clock",
    None: "mdi:clock",
}

SCAN_INTERVAL = timedelta(seconds=20)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_STOP_ID): cv.string,
        vol.Required(CONF_DIRECTION_ID): cv.string,
        vol.Optional(CONF_MIN_DUE_IN, default=10): cv.positive_int,
        vol.Optional(CONF_CACHE_PATH, default="/"): cv.string,
        vol.Optional(CONF_NAME, default="BVG"): cv.string,
        vol.Optional(CONF_CACHE_SIZE, default=60): cv.positive_int,
    }
)


def getNameFromIBNR(ibnr):
    name = ""
    payload = f"/stops/{ibnr}"

    try:
        stop = json.loads(urlopen(CON_REST_URL + payload).read().decode("utf8"))
        if stop["type"] == "stop" or stop["type"] == "station":
            name = stop["name"]

    except URLError as errormsg:
        _LOGGER.debug(errormsg)
        _LOGGER.warning("Failed to get the station IBNR")

    return name


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the sensor platform."""
    stop_id = config[CONF_STOP_ID]
    direction_id = config[CONF_DIRECTION_ID]
    min_due_in = config.get(CONF_MIN_DUE_IN)
    file_path = config.get(CONF_CACHE_PATH)
    name = config.get(CONF_NAME)
    cache_size = config.get(CONF_CACHE_SIZE)
    add_entities(
        [
            Bvgsensor(
                name, stop_id, direction_id, min_due_in, file_path, hass, cache_size
            )
        ]
    )


class Bvgsensor(Entity):
    """Representation of a Sensor."""

    def __init__(
        self, name, stop_id, direction_id, min_due_in, file_path, hass, cache_size
    ):
        """Initialize the sensor."""
        self.hass_config = hass.config.as_dict()
        self._cache_size = cache_size
        self._cache_creation_date = None
        self._isCacheValid = True
        self._timezone = self.hass_config.get("time_zone")
        self._name = name
        self._state = None
        self.stop = getNameFromIBNR(stop_id)
        self._stop_id = stop_id
        self.direction = getNameFromIBNR(direction_id)
        self._direction_id = direction_id
        self.min_due_in = min_due_in
        self.data = None
        self.connectionInfo = None
        self.file_path = self.hass_config.get("config_dir") + file_path
        self.file_name = f"bvg_{self._stop_id}.json"
        self._con_state = {CONNECTION_STATE: CON_STATE_ONLINE}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if self.connectionInfo is not None:
            return {
                ATTR_STOP_ID: self._stop_id,
                ATTR_STOP_NAME: self.connectionInfo.get(ATTR_STOP_NAME),
                ATTR_REAL_TIME: self.connectionInfo.get(ATTR_REAL_TIME),
                ATTR_DESTINATION_NAME: self.connectionInfo.get(ATTR_DESTINATION_NAME),
                ATTR_TRANS_TYPE: self.connectionInfo.get(ATTR_TRANS_TYPE),
                ATTR_LINE_NAME: self.connectionInfo.get(ATTR_LINE_NAME),
            }
        else:
            return {
                ATTR_STOP_ID: "n/a",
                ATTR_STOP_NAME: "n/a",
                ATTR_REAL_TIME: "n/a",
                ATTR_DESTINATION_NAME: "n/a",
                ATTR_TRANS_TYPE: "n/a",
                ATTR_LINE_NAME: "n/a",
            }

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "min"

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if self.connectionInfo is not None:
            return ICONS.get(self.connectionInfo.get(ATTR_TRANS_TYPE))
        else:
            return ICONS.get(None)

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        # self.fetchDataFromAPI
        self.connectionInfo = self.getConnectionInfo(self.direction, self.min_due_in)
        if self.connectionInfo is not None and len(self.connectionInfo) > 0:
            self._state = self.connectionInfo.get(ATTR_DUE_IN)
        else:
            self._state = "n/a"

    # only custom code beyond this line

    def getConnectionInfo(self, direction, min_due_in):
        # define the REST payload
        payload = f"/stops/{self._stop_id}/departures?direction={self._direction_id}&duration={self._cache_size}&remarks=false"
        # payload = f"/stops/{self._stop_id}/departures?direction={self._direction_id}"
        try:
            with urlopen(
                CON_REST_URL + payload
            ) as response:  # Get the data from the REST API
                source = response.read().decode("utf8")
                self.data = json.loads(source)  # JSON format the data
                if self._con_state.get(CONNECTION_STATE) is CON_STATE_OFFLINE:
                    _LOGGER.warning("Connection to BVG API re-established")
                    self._con_state.update({CONNECTION_STATE: CON_STATE_ONLINE})
                # write the response to a file for caching if connection is not available
                try:
                    with open(
                        f"{self.file_path}{self.file_name}", "w", encoding="utf8"
                    ) as fd:
                        # self.data = json.load(fd)
                        json.dump(self.data, fd, ensure_ascii=False)
                        # json.writes(response)
                        self._cache_creation_date = datetime.now(
                            pytz.timezone(self._timezone)
                        )
                except IOError as errormsg:
                    _LOGGER.warning(
                        f"Couldn't write file. Please check your configuration and read/write access for path: {self.file_path}"
                    )
                    _LOGGER.error(errormsg)
        except URLError as errormsg:
            if self._con_state.get(CONNECTION_STATE) is CON_STATE_ONLINE:
                _LOGGER.warning("Connection to BVG API lost, using local cache instead")
                self._con_state.update({CONNECTION_STATE: CON_STATE_OFFLINE})
                _LOGGER.error(errormsg)
            try:
                with open(
                    f"{self.file_path}{self.file_name}", "r", encoding="utf8"
                ) as fd:
                    self.data = json.load(fd)
            except IOError as errmsg:
                _LOGGER.warning(
                    "Could not read file. Please check your configuration and read/write access for path: {self.file_path}"
                )
                _LOGGER.error(errmsg)
                return None

        timetable_l = list()
        date_now = datetime.now(pytz.timezone(self.hass_config.get("time_zone")))
        for pos in self.data["departures"]:
            if pos:  # if pos not empty
                if pos["when"] is None:
                    continue
                dep_time = datetime.strptime(pos["when"][:-6], "%Y-%m-%dT%H:%M:%S")
                dep_time = pytz.timezone("Europe/Berlin").localize(dep_time)
                departure_td = dep_time - date_now
                # check if connection is not in the past
                if departure_td > timedelta(days=0):
                    departure_td = departure_td.seconds // 60
                    if departure_td >= min_due_in:
                        timetable_l.append(
                            {
                                ATTR_DESTINATION_NAME: pos["direction"],
                                ATTR_REAL_TIME: dep_time,
                                ATTR_DUE_IN: departure_td,
                                ATTR_TRIP_ID: pos["tripId"],
                                ATTR_STOP_NAME: pos["stop"]["name"],
                                ATTR_TRANS_TYPE: pos["line"]["product"],
                                ATTR_LINE_NAME: pos["line"]["name"],
                            }
                        )
                        _LOGGER.debug("Connection found")
                    else:
                        _LOGGER.debug(
                            f"Connection is due in under {min_due_in} minutes"
                        )
                else:
                    _LOGGER.debug("Connection lies in the past")
            else:
                _LOGGER.debug("No connection for specified direction")

            _LOGGER.debug("Valid connection found")
            _LOGGER.debug(f"Connection: {timetable_l}")

        if timetable_l:  # if timetable_l not empty
            return timetable_l[0]

        if self.isCacheValid():
            _LOGGER.warning(
                f"No valid connection found for the sensor named {self.name}. Please check your configuration."
            )
            self._isCacheValid = True
        else:
            self._isCacheValid = False

    def isCacheValid(self):
        date_now = datetime.now(pytz.timezone(self.hass_config.get("time_zone")))
        # If the component is starting without internet connection
        if self._cache_creation_date is None:
            self._cache_creation_date = datetime.fromtimestamp(
                os.path.getmtime(f"{self.file_path}{self.file_name}"),
                pytz.timezone(self._timezone),
            )
        td = (date_now - self._cache_creation_date).total_seconds()
        _LOGGER.debug(f"td is: {td}")
        if td > (self._cache_size * 60):
            _LOGGER.debug(f"Cache is outdated by: {td // 60} min.")
            return False
        else:
            return True
