#!/usr/bin/env python3

import collections
import re
import os
import zipfile
import json

pfx = "write_profile:"

VERSION_FILE = "profile/version.txt"

# define templates for the various sensor nodes we have available. Each
# sensor node will have a pre-defined list of drivers. When we build
# the node definition, we get to pick which drivers we include based on
# the user's configuration.

# Configuration will be something like this:
#
#   temperature.main = <wdtemp>
#   temperature.dewpoint = <>
#   temperature.windchill = <>
#   temperature.heatindex = <>
#   temperature.apparent = <>
#   temperature.inside = <>
#   temperature.extra1 = <>
#   temperature.extra2 = <>
#   temperature.extra3 = <>
#   temperature.extra4 = <>
#   temperature.extra5 = <>
#   temperature.extra6 = <>
#   temperature.extra7 = <>
#   temperature.extra8 = <>
#   temperature.extra9 = <>
#   temperature.extra10 = <>

TEMP_DRVS = {
        'main' : 'ST',
        'dewpoint' : 'GV0',
        'windchill' : 'GV1',
        'heatindex' : 'GV2',
        'apparent' : 'GV3',
        'inside' : 'GV4',
        'extra1' : 'GV5',
        'extra2' : 'GV6',
        'extra3' : 'GV7',
        'extra4' : 'GV8',
        'extra5' : 'GV9',
        'extra6' : 'GV10',
        'extra7' : 'GV11',
        'extra8' : 'GV12',
        'extra9' : 'GV13',
        'extra10' : 'GV14',
        'max' : 'GV15',
        'min' : 'GV16',
        'soil' : 'GV17',
        }

HUMD_DRVS = {
        'main' : 'ST',
        'inside' : 'GV0',
        'extra1' : 'GV1',
        'extra2' : 'GV2',
        'extra3' : 'GV3',
        'extra4' : 'GV4',
        'extra5' : 'GV5',
        }

PRES_DRVS = {
        'station' : 'ST',
        'sealevel' : 'GV0',
        'trend' : 'GV1'
        }

WIND_DRVS = {
        'windspeed' : 'ST',
        'winddir' : 'GV0',
        'gustspeed' : 'GV1',
        'gustdir' : 'GV2',
        'lullspeed' : 'GV3',
        'avgwindspeed' : 'GV4',
        }

RAIN_DRVS = {
        'rate' : 'ST',
        'hourly' : 'GV0',
        'daily' : 'GV1',
        'weekly' : 'GV2',
        'monthly' : 'GV3',
        'yearly' : 'GV4',
        'maxrate' : 'GV5',
        'yesterday' : 'GV6',
        }

LITE_DRVS = {
        'uv' : 'ST',
        'solar_radiation' : 'GV0',
        'illuminace' : 'GV1',
        'solar_percent' : 'GV2'
        }
LITE_EDIT = {
        'uv' : 'I_UV',
        'solar_radiation' : 'I_RADIATION',
        'illuminace' : 'I_LUX',
        'solar_percent' : 'I_HUMIDITY'
        }


LTNG_DRVS = {
        'strikes' : 'ST',
        'distance' : 'GV0'
        }


NODEDEF_TMPL = "  <nodeDef id=\"%s\" nodeType=\"139\" nls=\"%s\">\n"
STATUS_TMPL = "      <st id=\"%s\" editor=\"%s\" />\n"

# As long as we provide proper dictionary lists for each type of node
# this will generate the node definitions.
#
# Assumes that the NLS exist for the nodes and that the editors exist.

def write_profile(logger, temperature_list, humidity_list, pressure_list,
        wind_list, rain_list, light_list, lightning_list):
    sd = get_server_data(logger)
    if sd is False:
        logger.error("Unable to complete without server data...")
        return False

    logger.info("{0} Writing profile/nodedef/nodedefs.xml".format(pfx))
    nodedef = open("profile/nodedef/nodedefs.xml", "w")
    nodedef.write("<nodeDefs>\n")

    # First, write the controller node definition
    nodedef.write(NODEDEF_TMPL % ('WeatherDisplay', 'ctl'))
    nodedef.write("    <sts>\n")
    nodedef.write("      <st id=\"ST\" editor=\"bool\" />\n")
    nodedef.write("      <st id=\"GV0\" editor=\"I_VOLTS\" />\n")
    nodedef.write("      <st id=\"GV1\" editor=\"I_VOLTS\" />\n")
    nodedef.write("    </sts>\n")
    nodedef.write("    <cmds>\n")
    nodedef.write("      <sends />\n")
    nodedef.write("      <accepts>\n")
    nodedef.write("        <cmd id=\"DISCOVER\" />\n")
    nodedef.write("        <cmd id=\"REMOVE_NOTICES_ALL\" />\n")
    nodedef.write("        <cmd id=\"UPDATE_PROFILE\" />\n")
    nodedef.write("      </accepts>\n")
    nodedef.write("    </cmds>\n")
    nodedef.write("  </nodeDef>\n\n")

    # Need to translate temperature.main into <st id="ST" editor="TEMP_C" />
    # and     translate temperature.extra1 into <st id="GV5" editor="TEMP_C" />

    if (len(temperature_list) > 0):
        nodedef.write(NODEDEF_TMPL % ('temperature', '139T'))
        nodedef.write("    <sts>\n")
        for t in temperature_list:
            nodedef.write(STATUS_TMPL % (TEMP_DRVS[t], temperature_list[t]))
        nodedef.write("    </sts>\n")
        nodedef.write("  </nodeDef>\n")

    if (len(humidity_list) > 0):
        nodedef.write(NODEDEF_TMPL % ('humidity', '139H'))
        nodedef.write("    <sts>\n")
        for t in humidity_list:
            nodedef.write(STATUS_TMPL % (HUMD_DRVS[t], humidity_list[t]))
        nodedef.write("    </sts>\n")
        nodedef.write("  </nodeDef>\n")

    if (len(pressure_list) > 0):
        nodedef.write(NODEDEF_TMPL % ('pressure', '139P'))
        nodedef.write("    <sts>\n")
        for t in pressure_list:
            nodedef.write(STATUS_TMPL % (PRES_DRVS[t], pressure_list[t]))
        nodedef.write("    </sts>\n")
        nodedef.write("  </nodeDef>\n")

    if (len(wind_list) > 0):
        nodedef.write(NODEDEF_TMPL % ('wind', '139W'))
        nodedef.write("    <sts>\n")
        for t in wind_list:
            nodedef.write(STATUS_TMPL % (WIND_DRVS[t], wind_list[t]))
        nodedef.write("    </sts>\n")
        nodedef.write("  </nodeDef>\n")

    if (len(rain_list) > 0):
        nodedef.write(NODEDEF_TMPL % ('precipitation', '139R'))
        nodedef.write("    <sts>\n")
        for t in rain_list:
            nodedef.write(STATUS_TMPL % (RAIN_DRVS[t], rain_list[t]))
        nodedef.write("    </sts>\n")
        nodedef.write("  </nodeDef>\n")

    if (len(light_list) > 0):
        nodedef.write(NODEDEF_TMPL % ('light', '139L'))
        nodedef.write("    <sts>\n")
        for t in light_list:
            nodedef.write(STATUS_TMPL % (LITE_DRVS[t], light_list[t]))
        nodedef.write("    </sts>\n")
        nodedef.write("  </nodeDef>\n")

    if (len(lightning_list) > 0):
        nodedef.write(NODEDEF_TMPL % ('lightning', '139S'))
        nodedef.write("    <sts>\n")
        for t in lightning_list:
            nodedef.write(STATUS_TMPL % (LTNG_DRVS[t], lightning_list[t]))
        nodedef.write("    </sts>\n")
        nodedef.write("  </nodeDef>\n")

    nodedef.write("</nodeDefs>")

    nodedef.close()

    # Update the profile version file with the info from server.json
    with open(VERSION_FILE, 'w') as outfile:
        outfile.write(sd['profile_version'])
    outfile.close()

    # Create the zip file that can be uploaded to the ISY
    write_profile_zip(logger)

    logger.info(pfx + " done.")


def write_profile_zip(logger):
    src = 'profile'
    abs_src = os.path.abspath(src)
    with zipfile.ZipFile('profile.zip', 'w') as zf:
        for dirname, subdirs, files in os.walk(src):
            # Ignore dirs starint with a dot, stupid .AppleDouble...
            if not "/." in dirname:
                for filename in files:
                    if filename.endswith('.xml') or filename.endswith('txt'):
                        absname = os.path.abspath(os.path.join(dirname, filename))
                        arcname = absname[len(abs_src) + 1:]
                        logger.info('write_profile_zip: %s as %s' %
                                (os.path.join(dirname, filename), arcname))
                        zf.write(absname, arcname)
    zf.close()


def get_server_data(logger):
    # Read the SERVER info from the json.
    try:
        with open('server.json') as data:
            serverdata = json.load(data)
    except Exception as err:
        logger.error('get_server_data: failed to read {0}: {1}'.format('server.json',err), exc_info=True)
        return False
    data.close()
    # Get the version info
    try:
        version = serverdata['credits'][0]['version']
    except (KeyError, ValueError):
        logger.info('Version not found in server.json.')
        version = '0.0.0.0'
    # Split version into two floats.
    sv = version.split(".");
    v1 = 0;
    v2 = 0;
    if len(sv) == 1:
        v1 = int(v1[0])
    elif len(sv) > 1:
        v1 = float("%s.%s" % (sv[0],str(sv[1])))
        if len(sv) == 3:
            v2 = int(sv[2])
        else:
            v2 = float("%s.%s" % (sv[2],str(sv[3])))
    serverdata['version'] = version
    serverdata['version_major'] = v1
    serverdata['version_minor'] = v2
    return serverdata

# If we wanted to call this as a stand-alone script to generate the profile
# files, we'd do something like what's below but we'd need some way to 
# set the configuration.

if __name__ == "__main__":
    import logging,json
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=10,
        format='%(levelname)s:\t%(name)s\t%(message)s'
    )
    logger.setLevel(logging.DEBUG)

    # Test dictionaries to generate a custom nodedef file.
    tl = {'main' : 'TEMP_F', 'dewpoint' : 'TEMP_F', 'apparent' : 'TEMP_F',
            'extra3' : 'TEMP_F'}
    hl = {'main' : 'I_HUMIDITY'}
    pl = {'station' : 'I_INHG', 'trend' : 'I_TREND'}
    wl = {'windspeed' : 'I_MPH', 'gustspeed' : 'I_MPH', 'winddir' : 'I_DEGREE'}
    rl = {'hourly': 'I_MM', 'monthly': 'I_MM', 'yearly': 'I_MM'}
    ll = {'solar_percent' : 'I_HUMIDITY'}
    sl = {}

    # Only write the profile if the version is updated.
    sd = get_server_data(logger)
    if sd is not False:
        local_version = None
        try:
            with open(VERSION_FILE,'r') as vfile:
                local_version = vfile.readline()
                local_version = local_version.rstrip()
                vfile.close()
        except (FileNotFoundError):
            pass
        except (Exception) as err:
            logger.error('{0} failed to read local version from {1}: {2}'.format(pfx,VERSION_FILE,err), exc_info=True)

        if local_version == sd['profile_version']:
            #logger.info('{0} Not Generating new profile since local version {1} is the same current {2}'.format(pfx,local_version,sd['profile_version']))
            write_profile(logger, tl, hl, pl, wl, rl, ll, sl)
        else:
            logger.info('{0} Generating new profile since local version {1} is not current {2}'.format(pfx,local_version,sd['profile_version']))
            write_profile(logger, tl, hl, pl, wl, rl, ll, sl)
