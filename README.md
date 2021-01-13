# BVG Sensor Component for Home Assistant
**NOTE: this fork is Work-In-Progress because it's not functional under HassIO ver. 2020.12.07!<br>
        The 1.bvg.transport.rest API has been deprecated and this sensor has to be modified to<br>
        use the newer v5.bvg.transport.rest API**

The BVG Sensor can be used to display real-time public transport data for the city of Berlin within the BVG (Berliner Verkehrsbetriebe) route network.
The sensor will display the minutes until the next departure for the configured station and direction. The provided data is in real-time and does include actual delays. If you want to customize the sensor you can use the provided sensor attributes. You can also define a walking distance from your home/work, so only departures that are reachable will be shown.

During testing I found that the API frequently becomes unavailable, possibly to keep the amount of requests low. Therefore this component keeps a local copy of the data (90 minutes). The local data is only beeing used while "offline" and is beeing refreshed when the API endpoint becomes available again.

You can check the status of the API Endpoint here: https://status.transport.rest/784879513

This component uses the API provided by the [v5.bvg.transport.rest](https://v5.bvg.transport.rest)

Read the [API documentation](https://v5.bvg.transport.rest/api.html)


# Installation

Simply clone this repo into a ``/config/custom_components/`` folder and rename it to ``sensor.py``.

**Only valid for HomeAssistant Version lower than 0.89 as there were some breaking changes on how custom components will integrate with HomeAssistant from Version 0.89 and beyond...**

Simply copy the file bvgsensor.py into your ``/config/custom_components/sensor/`` folder. If it does not already exist, create the missing folders.

# Prerequisites

You will need to specify at least a ``stop_id`` and a ``direction`` for the connection you would like to display.

To find your ``stop_id`` use the following link: https://v5.bvg.transport.rest/locations?query="string" and replace ``string`` with an aproximate name for your station.
Find your `stop_id` within the json repsonse in your browser.

### Example:
You want to display the departure times from "U Rosa-Luxemburg-Platz" in direction to "Pankow" type :

> curl https://v5.bvg.transport.rest/stops/900000100016/departures?direction=900000130002 -s

Your **stop_id** IBNR for **U Rosa-Luxemburg-Platz** is: **900000100016**

The **direction** IBNR for **S-U Pankow** is: **900000130002**

# Configuration

To add the BVG Sensor Component to Home Assistant, add the following to your configuration.yaml file:

```yaml
# Example configuration.yaml entry
- platform: bvgsensor
    stop_id: your stop id
    direction: the final destination for your connection
```

- **stop_id** *(Required)*: The stop_id for your station.
- **direction** *(Required)*: One or more destinations for your route.
- **name** *(optional)*: Name your sensor, especially if you create multiple instances of the sensor give them different names. * (Default=BVG)*
- **walking_distance** *(optional)*: specify the walking distance in minutes from your home/location to the station. Only connections that are reachable in a timley manner will be shown. Set it to ``0`` if you want to disable this feature. *(Default=10)*
- **file_path** *(optional)*: path where you want your station specific data to be saved. *(Default= your home assistant config directory e.g. "conf/" )*

### Example Configuration:
```yaml
sensor:
  - platform: bvg-sensor
    name: U2 Rosa-Luxemburg-Platz
    stop_id: "900000100016"
    direction: "S+U Pankow"
    walking_distance: 5
    file_path: "/tmp/"
`