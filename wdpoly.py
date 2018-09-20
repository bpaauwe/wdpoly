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
import uom

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

        The nodes need to have thier drivers configured based on the user
        supplied configuration. To that end, we should probably create the
        node, update the driver list, set the units and then add the node.
        """
        LOGGER.info("Creating nodes.")

        if len(self.temperature_map) > 0:
            LOGGER.info("Creating Temperature node")
            node = TemperatureNode(self, self.address, 'temperature',
                    'Temperatures')
            LOGGER.info("Set units maybe?")
            node.SetUnits(self.units)

            # self.temperature_list - list of values with units
            # self.temperature_map - list driver/field pairs
            # if we added units to the driver/field list, that would help.
            for d in self.temperature_map:
                # {'driver': 'ST', 'value': 0, 'uom': 2},
                LOGGER.info("driver = {'driver': %s, 'value': 0, 'uom': %s}" % (d[0], uom.UOM[d[2]]))
                node.drivers.append(
                    {'driver': d[0], 'value': 0, 'uom': uom.UOM[d[2]]}
                    )
            self.addNode(node)

        if len(self.humidity_map) > 0:
            LOGGER.info("Creating Humidity node")
            node = HumidityNode(self, self.address, 'humidity', 'Humidity')
            for d in self.humidity_map:
                node.drivers.append(
                    {'driver': d[0], 'value': 0, 'uom': uom.UOM[d[2]]}
                    )
            self.addNode(node)

        if len(self.pressure_map) > 0:
            LOGGER.info("Creating Pressure node")
            node = PressureNode(self, self.address, 'pressure', 'Barometric Pressure')
            node.SetUnits(self.units)
            for d in self.pressure_map:
                node.drivers.append(
                    {'driver': d[0], 'value': 0, 'uom': uom.UOM[d[2]]}
                    )
            self.addNode(node)

        if len(self.wind_map) > 0:
            LOGGER.info("Creating Wind node")
            node = WindNode(self, self.address, 'wind', 'Wind')
            node.SetUnits(self.units)
            for d in self.wind_map:
                node.drivers.append(
                    {'driver': d[0], 'value': 0, 'uom': uom.UOM[d[2]]}
                    )
            self.addNode(node)

        if len(self.rain_map) > 0:
            LOGGER.info("Creating Precipitation node")
            node = PrecipitationNode(self, self.address, 'rain', 'Precipitation')
            node.SetUnits(self.units)
            for d in self.rain_map:
                node.drivers.append(
                    {'driver': d[0], 'value': 0, 'uom': uom.UOM[d[2]]}
                    )
            self.addNode(node)

        if len(self.light_map) > 0:
            LOGGER.info("Creating Light node")
            node = LightNode(self, self.address, 'light', 'Illumination')
            for d in self.light_map:
                node.drivers.append(
                    {'driver': d[0], 'value': 0, 'uom': uom.UOM[d[2]]}
                    )
            self.addNode(node)

        if len(self.lightning_map) > 0:
            LOGGER.info("Creating Lightning node")
            node = LightningNode(self, self.address, 'Lightning', 'Lightning')
            node.SetUnits(self.units)
            for d in self.lightning_map:
                node.drivers.append(
                    {'driver': d[0], 'value': 0, 'uom': uom.UOM[d[2]]}
                    )
            self.addNode(node)


        #self.addNode(HumidityNode(self, self.address, 'humidity', 'Humidity'))
        #self.addNode(PressureNode(self, self.address, 'pressure', 'Barometric Pressure'))
        #self.addNode(WindNode(self, self.address, 'wind', 'Wind'))
        #self.addNode(PrecipitationNode(self, self.address, 'rain', 'Precipitation'))
        #self.addNode(LightNode(self, self.address, 'light', 'Illumination'))
        #self.addNode(LightningNode(self, self.address, 'lightning', 'Lightning'))

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
                self.temperature_list[vmap[1]] = 'TEMP_F' if self.units == 'us' else 'TEMP_C'
                mapper = [ write_profile.TEMP_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key],
                        self.temperature_list[vmap[1]]
                        ]
                self.temperature_map.append(mapper)
            elif vmap[0] == 'humidity':
                self.humidity_list[vmap[1]] = 'I_HUMIDITY'
                mapper = [ write_profile.HUMD_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key],
                        self.humidity_list[vmap[1]]
                        ]
                self.humidity_map.append(mapper)
            elif vmap[0] == 'pressure':
                if vmap[1] == 'trend':
                    self.pressure_list[vmap[1]] = 'I_TREND'
                else:
                    self.pressure_list[vmap[1]] = 'I_INHG' if self.units == 'us' else 'I_MB'
                mapper = [ write_profile.PRES_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key],
                        self.pressure_list[vmap[1]]
                        ]
                self.pressure_map.append(mapper)
            elif vmap[0] == 'wind':
                if 'speed' in vmap[1]:
                    self.wind_list[vmap[1]] = 'I_KPH' if self.units == 'metric' else 'I_MPH'
                else:
                    self.wind_list[vmap[1]] = 'I_DEGREE'
                mapper = [ write_profile.WIND_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key],
                        self.wind_list[vmap[1]]
                        ]
                self.wind_map.append(mapper)
            elif vmap[0] == 'rain':
                if 'rate' in vmap[1]:
                    self.rain_list[vmap[1]] = 'I_MMHR' if self.units == 'metric' else 'I_INHR'
                else:
                    self.rain_list[vmap[1]] = 'I_MM' if self.units == 'metric' else 'I_INCH'
                mapper = [ write_profile.RAIN_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key],
                        self.rain_list[vmap[1]]
                        ]
                self.rain_map.append(mapper)
            elif vmap[0] == 'light':
                self.light_list[vmap[1]] = write_profile.LITE_EDIT[vmap[1]]
                mapper = [ write_profile.LITE_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key],
                        self.light_list[vmap[1]]
                        ]
                self.light_map.append(mapper)
            elif vmap[0] == 'lightning':
                if 'strike' in vmap[1]:
                    self.lightning_list[vmap[1]] = 'I_STRIKES'
                else:
                    self.lightning_list[vmap[1]] = 'I_KM' if self.units == 'metric' else 'I_MILE'
                mapper = [ write_profile.LTNG_DRVS[vmap[1]],
                        self.polyConfig['customParams'][key],
                        self.lightning_list[vmap[1]]
                        ]
                self.lightning_map.append(mapper)

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

        # push updated profile to ISY
        try:
            self.poly.installprofile()
        except:
            LOGGER.error('Failed up push profile to ISY')

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

            # loop through the various mappings and update the drivers.
            if len(self.temperature_map) > 0:
                for d in self.temperature_map:
                    self.nodes['temperature'].setDriver(d[0], float(fields[d[1]]))

                # both apparent temp and dewpoint are listed but at indexes
                # higher than what we're seeing in the data
                fl = self.nodes['temperature'].ApparentTemp(float(fields[4]),
                    float(fields[2]), float(fields[5]))
                self.nodes['temperature'].setDriver('GV3', fl)

                dp = self.nodes['temperature'].Dewpoint(float(fields[4]),
                    float(fields[5]))
                self.nodes['temperature'].setDriver('GV0', dp)

            if len(self.humidity_map) > 0:
                for d in self.humidity_map:
                    LOGGER.info("humidity: %s %s %s" % (d[0], d[1], d[2]))
                    self.nodes['humidity'].setDriver(d[0], int(fields[d[1]]))

            if len(self.pressure_map) > 0:
                for d in self.pressure_map:
                    self.nodes['pressure'].setDriver(d[0], float(fields[d[1]]))

            if len(self.lightning_map) > 0:
                for d in self.lightning_map:
                    self.nodes['lightning'].setDriver(d[0], int(fields[d[1]]))

            if len(self.wind_map) > 0:
                for d in self.wind_map:
                    self.nodes['wind'].setDriver(d[0], float(fields[d[1]]))

            if len(self.light_map) > 0:
                for d in self.light_map:
                    self.nodes['light'].setDriver(d[0], float(fields[d[1]]))

            if len(self.rain_map) > 0:
                for d in self.rain_map:
                    self.nodes['rain'].setDriver(d[0], float(fields[d[1]]))


    def SetUnits(self, u):
        self.units = u


    id = 'WeatherDisplay'
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
    drivers = [ ]

    def SetUnits(self, u):
        self.units = u

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
    drivers = [ ]
    mytrend = []


    def SetUnits(self, u):
        self.units = u

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
    drivers = [ ]

    def SetUnits(self, u):
        self.units = u

    def setDriver(self, driver, value):
        if (driver == 'ST' or driver == 'GV1' or driver == 'GV3'):
            if (self.units != 'metric'):
                value = round(value / 1.609344, 2)
        super(WindNode, self).setDriver(driver, value, report=True, force=True)

class PrecipitationNode(polyinterface.Node):
    id = 'precipitation'
    hint = 0xffffff
    units = 'metric'
    drivers = [ ]
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
    drivers = [ ]

    def SetUnits(self, u):
        self.units = u

    def setDriver(self, driver, value):
        super(LightNode, self).setDriver(driver, value, report=True, force=True)

class LightningNode(polyinterface.Node):
    id = 'lightning'
    hint = 0xffffff
    units = 'metric'
    drivers = [ ]

    def SetUnits(self, u):
        self.units = u

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
