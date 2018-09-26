
# Weather Display Polyglot

This is the Weather Display Poly for the Universal Devices ISY994i](https://www.universal-devices.com/residential/ISY) [Polyglot interface](http://www.universal-devices.com/developers/polyglot/docs/) with  [Polyglot V2](https://github.com/Einstein42/udi-polyglotv2)
(c) 2018 Robert Paauwe
MIT license.

This node server is intended to support the [Weather Display software](http://www.weather-display.com/).

## Installation

1. Backup Your ISY in case of problems!
   * Really, do the backup, please
2. Go to the Polyglot Store in the UI and install.
3. Add NodeServer in Polyglot Web
   * After the install completes, Polyglot will reboot your ISY, you can watch the status in the main polyglot log.
4. Once your ISY is back up open the Admin Console.
5. The node server should automatically run and find your hub(s) and start adding weather sensors.  It can take a couple of minutes to discover the sensors. Verify by checking the nodeserver log. 
   * While this is running you can view the nodeserver log in the Polyglot UI to see what it's doing
6. This should find your Air/Sky sensors and add them to the ISY with all the sensor values.

### Node Settings
The settings for this node are:

#### Short Poll
   * Not used
#### Long Poll
   * Not currently used
#### UDPport
   * Configure the port Weather Display sends data on (TBD).
#### IPAddress
   * Configure the multicast IP address used by Weather Display (TBD).
#### Units
   * Configure the units used when displaying data. Choices are:
   *   metric - SI / metric units
   *   us     - units generally used in the U.S.
   *   uk     - units generally used in the U.K.
#### Data Configuration
   * Configure which data fields to pass to the ISY. The key is node-fieldname
     and the value is the Weather Display field number.  The following is 
     the complete list:

```
        temperature-main : 4
        temperature-dewpoint : 72
        temperature-windchill : 44
        temperature-heatindex : 112
        temperature-apparent : 130
        temperature-inside : 12
        temperature-extra1 : 16
        temperature-extra2 : 20
        temperature-extra3 : 21
        temperature-extra4 : 22
        temperature-extra5 : 23
        temperature-extra6 : 24
        temperature-extra7 : 25
        temperature-extra8 : n/a
        temperature-extra9 : n/a
        temperature-extra10 : n/a
        temperature-max : 46
        temperature-min : 47
        temperature-soil : 14 

        humidiy-main : 5
        humidiy-inside : 13
        humidiy-extra1 : 17
        humidiy-extra2 : 26
        humidiy-extra3 : 27
        humidiy-extra4 : 28
        humidiy-extra5 : n/a

        pressure-station : n/a
        pressure-sealevel : 6
        pressure-trend : 50

        wind-windspeed : 2
        wind-winddir : 3
        wind-gustspeed : n/a
        wind-gustdir : n/a
        wind-lullspeed : n/a
        wind-avgwindspeed : 1

        rain-rate : 10
        rain-hourly : n/a
        rain-daily : 7
        rain-weekly : n/a
        rain-monthly : 8
        rain-yearly : 9
        rain-maxrate : 11
        rain-yesterday : 19

        light-uv : 79
        light-solar_radiation : 127
        light-illuminace : n/a
	light-solar_percent: 34

        lightning-strikes : 33
        lightning-distance : 118
```


## Requirements

1. Polyglot V2 itself should be run on Raspian Stretch.
  To check your version, ```cat /etc/os-release``` and the first line should look like
  ```PRETTY_NAME="Raspbian GNU/Linux 9 (stretch)"```. It is possible to upgrade from Jessie to
  Stretch, but I would recommend just re-imaging the SD card.  Some helpful links:
   * https://www.raspberrypi.org/blog/raspbian-stretch/
   * https://linuxconfig.org/raspbian-gnu-linux-upgrade-from-jessie-to-raspbian-stretch-9
2. This has only been tested with ISY 5.0.13 so it is not guaranteed to work with any other version.

# Upgrading

Open the Polyglot web page, go to nodeserver store and click "Update" for "WeatherFlow".

For Polyglot 2.0.35, hit "Cancel" in the update window so the profile will not be updated and ISY rebooted.  The install procedure will properly handle this for you.  This will change with 2.0.36, for that version you will always say "No" and let the install procedure handle it for you as well.

Then restart the Weather Display nodeserver by selecting it in the Polyglot dashboard and select Control -> Restart, then watch the log to make sure everything goes well.

The Weather Display nodeserver keeps track of the version number and when a profile rebuild is necessary.  The profile/version.txt will contain the Weather Display profile_version which is updated in server.json when the profile should be rebuilt.

# Release Notes

- 0.1.0 09/14/2018
   - Initial version released published to github
