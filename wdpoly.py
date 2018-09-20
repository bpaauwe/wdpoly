#!/usr/bin/env python3
"""
Polyglot v2 node server for WeatherDisplay weather data.
Copyright (c) 2018 Robert Paauwe
"""
import polyinterface
import sys
import time
import datetime
import urllib3
import json
import socket
import math
import threading
import struct
import write_profile

LOGGER = polyinterface.LOGGER

class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'WeatherDisplay'
        self.address = 'weather'
        self.primary = self.address
        self.udp_port = 1333
        self.mcast_ip = "231.31.31.31"
        self.units = ""
        self.temperature_list = {}
        self.humidity_list = {}
        self.pressure_list = {}
        self.wind_list = {}
        self.rain_list = {}
        self.light_list = {}
        self.lightning_list = {}
        self.temperature_map = []
        self.humidity_map = []
        self.pressure_map = []
        self.wind_map = []
        self.rain_map = []
        self.light_map = []
        self.lightning_map = []

        try:
            self.polyConfig
            LOGGER.info("polyConfig DOES exist what's going on?")
        except NameError:
            LOGGER.info("polyConfig doesn't exist yet")
            self.polyConfig = None

        #self.poly.onConfig(self.process_config)

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter");

        LOGGER.info("Finished with configuration.")

    def start(self):
        LOGGER.info('Starting WeatherDisplay Node Server')
        self.check_params()
        LOGGER.info('Calling discover')
        self.discover()

        LOGGER.info('starting thread for UDP data')
        threading.Thread(target = self.udp_data).start()
        #for node in self.nodes:
        #       LOGGER.info (self.nodes[node].name + ' is at index ' + node)
        LOGGER.info('WeatherDisplay Node Server Started.')

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        """
        Add nodes for basic sensor type data
                - Temperature (temp, dewpoint, heat index, wind chill, feels)
                - Humidity
                - Pressure (abs, sealevel, trend)
                - Wind (speed, gust, direction, gust direction, etc.)
                - Precipitation (rate, hourly, daily, weekly, monthly, yearly)
                - Light (UV, solar radiation, lux)
                - Lightning (strikes, distance)
        """
        LOGGER.info("Discovering/creating nodes.")
        self.addNode(TemperatureNode(self, self.address, 'temperature', 'Temperatures'))
        self.addNode(HumidityNode(self, self.address, 'humidity', 'Humidity'))
        self.addNode(PressureNode(self, self.address, 'pressure', 'Barometric Pressure'))
        self.addNode(WindNode(self, self.address, 'wind', 'Wind'))
        self.addNode(PrecipitationNode(self, self.address, 'rain', 'Precipitation'))
        self.addNode(LightNode(self, self.address, 'light', 'Illumination'))
        self.addNode(LightningNode(self, self.address, 'lightning', 'Lightning'))

    def delete(self):
        self.stopping = True
        LOGGER.info('Removing WeatherDisplay node server.')

    def stop(self):
        self.stopping = True
        LOGGER.debug('Stopping WeatherDisplay node server.')

    def check_params(self):
        default_port = 1333
        default_mcast_ip = "231.31.31.31"
        default_elevation = 0

        LOGGER.info("Check for existing configuration value")

        if 'UDPPort' in self.polyConfig['customParams']:
            self.udp_port = int(self.polyConfig['customParams']['UDPPort'])
        else:
            self.udp_port = default_port

        if 'IPAddress' in self.polyConfig['customParams']:
            self.mcast_ip = self.polyConfig['customParams']['IPAddress']
        else:
            self.mcast_ip = default_mcast_ip

        if 'Units' in self.polyConfig['customParams']:
            self.units = self.polyConfig['customParams']['Units']
        else:
            self.units = 'metric'

        # Build up our data mapping table. The customParams keys will
        # look like temperature.main and the value will be WD field #
        LOGGER.info("Trying to create a mapping")
        for key in self.polyConfig['customParams']:
            if not '-' in key:
                LOGGER.info("skipping " + key)
                continue

            vmap = key.split('-')

            # Mapping needs to be a list for each node and each list item
            # is a 2 element list (or a dictionary?)

            if vmap[0] == 'temperature':
                mapper = [ write_profile.TEMP_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key] ]
                self.temperature_map.append(mapper)
                self.temperature_list[vmap[1]] = 'TEMP_F' if self.units == 'us' else 'TEMP_C'
            elif vmap[0] == 'humidity':
                mapper = [ write_profile.HUMD_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key] ]
                self.humidity_map.append(mapper)
                self.humidity_list[vmap[1]] = 'I_HUMIDITY'
            elif vmap[0] == 'pressure':
                mapper = [ write_profile.PRES_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key] ]
                self.pressure_map.append(mapper)
                if vmap[1] == 'trend':
                    self.pressure_list[vmap[1]] = 'I_TREND'
                else:
                    self.pressure_list[vmap[1]] = 'I_INHG' if self.units == 'us' else 'I_MB'
            elif vmap[0] == 'wind':
                mapper = [ write_profile.WIND_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key] ]
                self.wind_map.append(mapper)
                if 'speed' in vmap[1]:
                    self.wind_list[vmap[1]] = 'I_MS' if self.units == 'metric' else 'I_MPH'
                else:
                    self.wind_list[vmap[1]] = 'I_DEGREE'
            elif vmap[0] == 'rain':
                mapper = [ write_profile.RAIN_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key] ]
                self.rain_map.append(mapper)
                if 'rate' in vmap[1]:
                    self.rain_list[vmap[1]] = 'I_MMHR' if self.units == 'metric' else 'I_INHR'
                else:
                    self.rain_list[vmap[1]] = 'I_MM' if self.units == 'metric' else 'I_INCH'
            elif vmap[0] == 'light':
                mapper = [ write_profile.LITE_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key] ]
                self.light_map.append(mapper)
                self.light_list[vmap[1]] = write_profile.LITE_EDIT[vmap[1]]
            elif vmap[0] == 'lightning':
                mapper = [ write_profile.LTNG_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key] ]
                self.lightning_map.append(mapper)
                if 'strike' in vmap[1]:
                    self.lightning_list[vmap[1]] = 'I_STRIKES'
                else:
                    self.lightning_list[vmap[1]] = 'I_KM' if self.units == 'metric' else 'I_MILE'

        # Make sure they are in the params
        LOGGER.info("Adding configuation")
        self.addCustomParam({
                    'UDPPort': self.udp_port,
                    'IPAddress': self.mcast_ip,
                    'Units': self.units,
                    'temperature-main': 4,
                    'temperature-heatindex': 45,
                    'temperature-windchill': 44,
                    'humidity-main': 5,
                    'pressure-sealevel': 6,
                    'pressure-trend': 50,
                    'wind-windspeed': 2,
                    'wind-winddir': 3,
                    'rain-rate': 10,
                    'rain-weekly': 7,
                    'rain-monthly': 8,
                    'rain-yearly': 9,
                    'light-uv': 34,
                    })

        # Build the node definition
        LOGGER.info('Try to create node definition profile based on config.')
        write_profile.write_profile(LOGGER, self.temperature_list,
                self.humidity_list, self.pressure_list, self.wind_list,
                self.rain_list, self.light_list, self.lightning_list)

        # Remove all existing notices
        LOGGER.info("remove all notices")
        self.removeNoticesAll()

        # Add a notice?

    def remove_notices_all(self,command):
        LOGGER.info('remove_notices_all:')
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self,command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    def udp_data(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.mcast_ip, self.udp_port))
        mreq = struct.pack("4sl", socket.inet_aton(self.mcast_ip), socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        windspeed = 0

        LOGGER.info("Starting UDP receive loop")
        while self.stopping == False:
            wd_data = s.recvfrom(1024)
            data = wd_data[0].decode("utf-8") # wd_data is a truple (data, ip, port)
            fields = data.split()

            # is there a good way to embed the field definition here?

            LOGGER.info('Got: ' + fields[4] + ', ' + fields[5] + ', ' + fields[6])
            self.nodes['pressure'].setDriver('GV0', float(fields[6]))
            self.nodes['pressure'].setDriver('GV1', fields[50])
            self.nodes['temperature'].setDriver('ST', float(fields[4]))
            self.nodes['temperature'].setDriver('GV2', float(fields[45]))
            self.nodes['temperature'].setDriver('GV3', float(fields[44]))

            # both apparent temp and dewpoint are listed but at indexes
            # higher than what we're seeing in the data
            fl = self.nodes['temperature'].ApparentTemp(float(fields[4]), float(fields[2]), float(fields[5]))
            self.nodes['temperature'].setDriver('GV0', fl)

            dp = self.nodes['temperature'].Dewpoint(float(fields[4]), float(fields[5]))
            self.nodes['temperature'].setDriver('GV1', dp)

            self.nodes['humidity'].setDriver('ST', int(fields[5]))

            self.nodes['lightning'].setDriver('ST', int(fields[33]))

            self.nodes['wind'].setDriver('ST', float(fields[2]))
            self.nodes['wind'].setDriver('GV0', int(fields[3]))

            self.nodes['light'].setDriver('GV0', float(fields[34]))

            self.nodes['rain'].setDriver('ST', float(fields[10]))
            self.nodes['rain'].setDriver('GV2', float(fields[7]))
            self.nodes['rain'].setDriver('GV3', float(fields[8]))
            self.nodes['rain'].setDriver('GV4', float(fields[9]))


    def SetUnits(self, u):
        self.units = u


    id = 'WDPoly'
    name = 'WeatherDisplayPoly'
    address = 'weather'
    stopping = False
    hint = 0xffffff
    units = 'metric'
    commands = {
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all
    }
    # Hub status information here: battery and rssi values.
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},
            {'driver': 'GV0', 'value': 0, 'uom': 72},  # Air battery level
            {'driver': 'GV1', 'value': 0, 'uom': 72},  # Sky battery level
            {'driver': 'GV2', 'value': 0, 'uom': 25},  # Air RSSI
            {'driver': 'GV3', 'value': 0, 'uom': 25}   # Sky RSSI
            ]


class TemperatureNode(polyinterface.Node):
    id = 'temperature'
    hint = 0xffffff
    units = 'metric'
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 17},
            {'driver': 'GV0', 'value': 0, 'uom': 17}, # feels like
            {'driver': 'GV1', 'value': 0, 'uom': 17}, # dewpoint
            {'driver': 'GV2', 'value': 0, 'uom': 17}, # heat index
            {'driver': 'GV3', 'value': 0, 'uom': 17}  # windchill
            ]

    def SetUnits(self, u):
        self.units = u
        if (u == 'metric'):  # C
            self.drivers[0]['uom'] = 4
            self.drivers[1]['uom'] = 4
            self.drivers[2]['uom'] = 4
            self.drivers[3]['uom'] = 4
            self.drivers[4]['uom'] = 4
            self.id = 'temperature'
        elif (u == 'uk'):  # C
            self.drivers[0]['uom'] = 4 
            self.drivers[1]['uom'] = 4
            self.drivers[2]['uom'] = 4
            self.drivers[3]['uom'] = 4
            self.drivers[4]['uom'] = 4
            self.id = 'temperatureUK'
        elif (u == 'us'):   # F
            self.drivers[0]['uom'] = 17
            self.drivers[1]['uom'] = 17
            selft.drivers[2]['uom'] = 17
            self.drivers[3]['uom'] = 17
            self.drivers[4]['uom'] = 17
            self.id = 'temperatureUS'

    def Dewpoint(self, t, h):
        b = (17.625 * t) / (243.04 + t)
        rh = h / 100.0
        c = math.log(rh)
        dewpt = (243.04 * (c + b)) / (17.625 - c - b)
        return round(dewpt, 1)

    def ApparentTemp(self, t, ws, h):
        wv = h / 100.0 * 6.105 * math.exp(17.27 * t / (237.7 + t))
        at =  t + (0.33 * wv) - (0.70 * ws) - 4.0
        return round(at, 1)

    def Windchill(self, t, ws):
        # really need temp in F and speed in MPH
        tf = (t * 1.8) + 32
        mph = ws / 0.44704

        wc = 35.74 + (0.6215 * tf) - (35.75 * math.pow(mph, 0.16)) + (0.4275 * tf * math.pow(mph, 0.16))

        if (tf <= 50.0) and (mph >= 5.0):
            return round((wc - 32) / 1.8, 1)
        else:
            return t

    def Heatindex(self, t, h):
        tf = (t * 1.8) + 32
        c1 = -42.379
        c2 = 2.04901523
        c3 = 10.1433127
        c4 = -0.22475541
        c5 = -6.83783 * math.pow(10, -3)
        c6 = -5.481717 * math.pow(10, -2)
        c7 = 1.22874 * math.pow(10, -3)
        c8 = 8.5282 * math.pow(10, -4)
        c9 = -1.99 * math.pow(10, -6)

        hi = (c1 + (c2 * tf) + (c3 * h) + (c4 * tf * h) + (c5 * tf *tf) + (c6 * h * h) + (c7 * tf * tf * h) + (c8 * tf * h * h) + (c9 * tf * tf * h * h))

        if (tf < 80.0) or (h < 40.0):
            return t
        else:
            return round((hi - 32) / 1.8, 1)

    def setDriver(self, driver, value):
        if (self.units == "us"):
            value = (value * 1.8) + 32  # convert to F

        super(TemperatureNode, self).setDriver(driver, round(value, 1), report=True, force=True)



class HumidityNode(polyinterface.Node):
    id = 'humidity'
    hint = 0xffffff
    units = 'metric'
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 22}]

    def SetUnits(self, u):
        self.units = u

    def setDriver(self, driver, value):
        super(HumidityNode, self).setDriver(driver, value, report=True, force=True)

class PressureNode(polyinterface.Node):
    id = 'pressure'
    hint = 0xffffff
    units = 'metric'
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 117},  # abs press
            {'driver': 'GV0', 'value': 0, 'uom': 117}, # rel press
            {'driver': 'GV1', 'value': 0, 'uom': 25}  # trend
            ]
    mytrend = []


    def SetUnits(self, u):
        # can we dynmically set the drivers here also?
        # what about the ID, can we dynamically change that to change
        # the node def?
        self.units = u
        if (u == 'metric'):  # millibar
            self.drivers[0]['uom'] = 117
            self.drivers[1]['uom'] = 117
            self.id = 'pressure'
        elif (u == 'uk'):  # millibar
            self.drivers[0]['uom'] = 117 
            self.drivers[1]['uom'] = 117
            self.id = 'pressureUK'
        elif (u == 'us'):   # inHg
            self.drivers[0]['uom'] = 23
            self.drivers[1]['uom'] = 23
            self.id = 'pressureUS'

    # convert station pressure in millibars to sealevel pressure
    def toSeaLevel(self, station, elevation):
        i = 287.05
        a = 9.80665
        r = 0.0065
        s = 1013.35 # pressure at sealevel
        n = 288.15

        l = a / (i * r)
        c = i * r / a
        u = math.pow(1 + math.pow(s / station, c) * (r * elevation / n), 1)

        return (round((station * u), 3))

    # track pressures in a queue and calculate trend
    def updateTrend(self, current):
        t = 0
        past = 0

        if len(self.mytrend) == 180:
            past = self.mytrend.pop()

        if self.mytrend != []:
            past = self.mytrend[0]

        # calculate trend
        if ((past - current) > 1):
            t = -1
        elif ((past - current) < -1):
            t = 1

        self.mytrend.insert(0, current)
        return t

    # We want to override the SetDriver method so that we can properly
    # convert the units based on the user preference.
    def setDriver(self, driver, value):
        if (self.units == 'us'):
            value = round(value * 0.02952998751, 3)
        super(PressureNode, self).setDriver(driver, value, report=True, force=True)


class WindNode(polyinterface.Node):
    id = 'wind'
    hint = 0xffffff
    units = 'metric'
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 32},  # speed
            {'driver': 'GV0', 'value': 0, 'uom': 76}, # direction
            {'driver': 'GV1', 'value': 0, 'uom': 32}, # gust
            {'driver': 'GV2', 'value': 0, 'uom': 76}, # gust direction
            {'driver': 'GV3', 'value': 0, 'uom': 32} # lull
            ]

    def SetUnits(self, u):
        self.units = u
        if (u == 'metric'):
            self.drivers[0]['uom'] = 32
            self.drivers[2]['uom'] = 32
            self.drivers[4]['uom'] = 32
            self.id = 'wind'
        elif (u == 'uk'): 
            self.drivers[0]['uom'] = 48
            self.drivers[2]['uom'] = 48
            self.drivers[4]['uom'] = 48
            self.id = 'windUK'
        elif (u == 'us'): 
            self.drivers[0]['uom'] = 48
            self.drivers[2]['uom'] = 48
            self.drivers[4]['uom'] = 48
            self.id = 'windUS'

    def setDriver(self, driver, value):
        if (driver == 'ST' or driver == 'GV1' or driver == 'GV3'):
            if (self.units != 'metric'):
                value = round(value / 1.609344, 2)
        super(WindNode, self).setDriver(driver, value, report=True, force=True)

class PrecipitationNode(polyinterface.Node):
    id = 'precipitation'
    hint = 0xffffff
    units = 'metric'
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 46},  # rate
            {'driver': 'GV0', 'value': 0, 'uom': 82}, # hourly
            {'driver': 'GV1', 'value': 0, 'uom': 82}, # daily
            {'driver': 'GV2', 'value': 0, 'uom': 82}, # weekly
            {'driver': 'GV3', 'value': 0, 'uom': 82}, # monthly
            {'driver': 'GV4', 'value': 0, 'uom': 82}  # yearly
            ]
    hourly_rain = 0
    daily_rain = 0
    weekly_rain = 0
    monthly_rain = 0
    yearly_rain = 0

    prev_hour = 0
    prev_day = 0
    prev_week = 0

    def SetUnits(self, u):
        self.units = u
        if (u == 'metric'):
            self.drivers[0]['uom'] = 46
            self.drivers[1]['uom'] = 82
            self.drivers[2]['uom'] = 82
            self.drivers[3]['uom'] = 82
            self.drivers[4]['uom'] = 82
            self.drivers[5]['uom'] = 82
            self.id = 'precipitation'
        elif (u == 'uk'): 
            self.drivers[0]['uom'] = 46
            self.drivers[1]['uom'] = 82
            self.drivers[2]['uom'] = 82
            self.drivers[3]['uom'] = 82
            self.drivers[4]['uom'] = 82
            self.drivers[5]['uom'] = 82
            self.id = 'precipitationUK'
        elif (u == 'us'): 
            self.drivers[0]['uom'] = 24
            self.drivers[1]['uom'] = 105
            self.drivers[2]['uom'] = 105
            self.drivers[3]['uom'] = 105
            self.drivers[4]['uom'] = 105
            self.drivers[5]['uom'] = 105
            self.id = 'precipitationUS'

    def hourly_accumulation(self, r):
        current_hour = datetime.datetime.now().hour
        if (current_hour != self.prev_hour):
            self.prev_hour = current_hour
            self.hourly = 0

        self.hourly_rain += r
        return self.hourly_rain

    def daily_accumulation(self, r):
        current_day = datetime.datetime.now().day
        if (current_day != self.prev_day):
            self.prev_day = current_day
            self.daily_rain = 0

        self.daily_rain += r
        return self.daily_rain

    def weekly_accumulation(self, r):
        current_week = datetime.datetime.now().day
        if (current_weekday != self.prev_weekday):
            self.prev_week = current_weekday
            self.weekly_rain = 0

        self.weekly_rain += r
        return self.weekly_rain

        
    def setDriver(self, driver, value):
        if (self.units == 'us'):
            value = round(value * 0.03937, 2)
        super(PrecipitationNode, self).setDriver(driver, value, report=True, force=True)

class LightNode(polyinterface.Node):
    id = 'light'
    units = 'metric'
    hint = 0xffffff
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 71},  # UV
            {'driver': 'GV0', 'value': 0, 'uom': 74},  # solar radiation
            {'driver': 'GV1', 'value': 0, 'uom': 36},  # Lux
            ]

    def SetUnits(self, u):
        self.units = u

    def setDriver(self, driver, value):
        super(LightNode, self).setDriver(driver, value, report=True, force=True)

class LightningNode(polyinterface.Node):
    id = 'lightning'
    hint = 0xffffff
    units = 'metric'
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 25},  # Strikes
            {'driver': 'GV0', 'value': 0, 'uom': 83},  # Distance
            ]

    def SetUnits(self, u):
        self.units = u
        if (u == 'metric'):
            self.drivers[0]['uom'] = 25
            self.drivers[1]['uom'] = 83
            self.id = 'lightning'
        elif (u == 'uk'): 
            self.drivers[0]['uom'] = 25
            self.drivers[1]['uom'] = 116
            self.id = 'lightningUK'
        elif (u == 'us'): 
            self.drivers[0]['uom'] = 25
            self.drivers[1]['uom'] = 116
            self.id = 'lightningUS'

    def setDriver(self, driver, value):
        if (driver == 'GV0'):
            if (self.units != 'metric'):
                value = round(value / 1.609344, 1)
        super(LightningNode, self).setDriver(driver, value, report=True, force=True)


if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('WeatherDisplay')
        """
        Instantiates the Interface to Polyglot.
        """
        polyglot.start()
        """
        Starts MQTT and connects to Polyglot.
        """
        control = Controller(polyglot)
        """
        Creates the Controller Node and passes in the Interface
        """
        control.runForever()
        """
        Sits around and does nothing forever, keeping your program running.
        """
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
