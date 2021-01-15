# BVG Sensor Component for Home Assistant
**NOTE: this HA sensor is Work-In-Progress, being teste under HassIO ver. 2021.2.0.dev0!<br>
        This sensor is based on the now abandoned sensor: [fluffykraken/bvg-sensor](https://github.com/fluffykraken/bvg-sensor), and has to be modified to use the newer v5.bvg.transport.rest API. The multi-destination capabilitiy has been<br>
        strippe away because I couldn't figure out how it was supposed to work.**

# Abstract
While setting up my RPI-base Hassio system I wondered how I could display the time in minutes till next departure of the BVG transport line I most use.
My requirement is to be able to show al transport lines of interest in a single Entities-Card. I will need one instance of this sensor per transport line.
The BVG Sensor is used to display real-time public transport data for the city of Berlin within the BVG (Berliner Verkehrsbetriebe) route network.
The sensor will display the minutes until the next departure for the configured station and line direction. The sensor provided real-time data and includes actual delays. You can also define a walking distance from your home/work, so only departures times that are reachable will be shown.

During testing I found that the API frequently becomes unavailable, possibly to keep the amount of requests low. Therefore this component keeps a local copy of the data (90 minutes). The local data will only be used while "offline" and is refreshed as soon as the API endpoint becomes available again.

You can check the status of the API Endpoint here: https://status.transport.rest/784879513

This component uses the API provided by the [v5.bvg.transport.rest](https://v5.bvg.transport.rest).

Read the [REST API documentation](https://v5.bvg.transport.rest/api.html).

# Characteristics
This sensor will pull departure information for a particular travel direction from the [v5.bvg.transport.rest API](https://v5.bvg.transport.rest/).
This information contains all departures for the stop/station and travel direction of interest. It spans a period of 90 min. (default) and is stored in a file: <file_path>/bvg_<stop_id>.
If the REST API is unavailable the local file will be used as the source of data.

# Installation

Simply clone this repo into a ``/config/custom_components/`` folder and rename it to ``sensor.py``.

**Only valid for HomeAssistant Version lower than 0.89 as there were some breaking changes on how custom components will integrate with HomeAssistant from Version 0.89 and beyond...**

Simply copy the file bvgsensor.py into your ``/config/custom_components/sensor/`` folder. If it does not already exist, create the missing folders.

# Prerequisites

You will need to specify at least a ``stop_id`` and a ``direction`` for the connection you would like to display.

To find your station IBNR use the following link: https://v5.bvg.transport.rest/locations?query=``string`` and replace ``string`` with an aproximate name for your station.
Get your IBNR (`id:`) within the json repsonse in your browser.

### Examples:
```
curl https://v5.vbb.transport.rest/locations?query=Rosa -s | jq
[
  {
    "type": "stop",
    "id": "900000100016",
    "name": "U Rosa-Luxemburg-Platz",
    "location": {
      "type": "location",
      "id": "900100016",
      "latitude": 52.528187,
      "longitude": 13.410405
    },
```
You want to display the departure times from "U Rosa-Luxemburg-Platz" in direction to "Pankow" type :

```
curl https://v5.bvg.transport.rest/stops/900000100016/departures?direction=900000130002 -s | jq
```

Your **stop_id** IBNR for **U Rosa-Luxemburg-Platz** is: **900000100016**

The **direction** IBNR for **S-U Pankow** is: **900000130002**

# Configuration

To add the BVG Sensor Component to Home Assistant, add the following to your configuration.yaml file:

```yaml
# Example configuration.yaml entry
- platform: bvg-sensor
    name: A distinctive route name
    stop_id: The stop IBNR of your station
    direction_id: The final destination IBNR for your connection
    walking_distance: how many minutes walk to the stop
```

- **stop_id** *(Required)*: The stop IBNR for your station.
- **direction_id** *(Required)*: The destination IBNR for your route.
- **name** *(optional)*: Name your sensor, especially if you create multiple instances of the sensor give them different names. * (Default=BVG)*
- **walking_distance** *(optional)*: specify the walking distance in minutes from your home/location to the station. Only connections that are reachable in a timley manner will be shown. Set it to ``0`` if you want to disable this feature. *(Default=10)*
- **file_path** *(optional)*: path where you want your station specific data to be saved. *(Default= your home assistant config directory e.g. "conf/" )*

You can configure the instantiation of multiple sensors by adding more platform entries, each with a different name.

### Example Configuration:
```yaml
sensor:
  - platform: bvg-sensor
    name: U2 -> S+U Pankow
    stop_id: "900000100016"      # U Rosa-Luxemburg-Platz
    direction_id: "900000130002" # S+U Pankow
    walking_distance: 5
    file_path: "/tmp/"

  - platform: bvg-sensor
    name: U2 -> S Ostbahnhof
    stop_id: "900000100016"      # U Rosa-Luxemburg-Platz
    direction_id: "900000120005" # S Ostbahnhof
    walking_distance: 5
    file_path: "/tmp/"
```