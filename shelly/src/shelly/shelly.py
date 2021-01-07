# -*- coding: utf-8 -*-

from base import (Application, Plugin, implements, Settings)
from datetime import timedelta 
from threading import Thread
from telldus import DeviceManager, Device
from telldus.web import IWebReactHandler
from web.base import IWebRequestHandler, Server, WebResponseJson
import logging
from logging import StreamHandler
import httplib
import urllib
import json
from pyShelly import pyShelly
import threading

__name__ = 'Shelly'
__version__ = '0.2.0b7'

PING_INTERVAL = 3600
LOG_LEVEL = 100

LOGGER = logging.getLogger('pyShelly')

CONFIG = "Shelly.config"


class ShellyDevice(Device):

    def __init__(self, dev, plugin):
        super(ShellyDevice, self).__init__()
        self._localid = dev.id
        self.dev = dev
        self.plugin = plugin
        self.ip_addr = getattr(dev, 'ip_addr', '')
        self.device_type = getattr(dev, 'device_type', '')
        self.device_sub_type = getattr(dev, 'device_sub_type', '')
        self.firmware_version = None
        self.latest_fw_version = None
        self.has_firmware_update = None
        self.type_name = dev.type_name()# + " " + dev.device_type        
        self.local_name = None
        self._lastState = None
        self._lastSensorValue = None
        self.update_name()
        dev.cb_updated.append( self._updated )
        self._updated(self.dev)

    def localId(self):
        return self._localid
    
    def methods(self):
        methods = 0
        if hasattr(self.dev, 'turn_on'):
            methods = methods | Device.TURNON
        if hasattr(self.dev, 'turn_off'):
            methods = methods | Device.TURNOFF
        if hasattr(self.dev, 'up'):
            methods = methods | Device.UP
        if hasattr(self.dev, 'down'):
            methods = methods | Device.DOWN
        if hasattr(self.dev, 'stop'):
            methods = methods | Device.STOP
        #if self.dev.device_type == 'LIGHT':
        if hasattr(self.dev, 'rgb') and self.dev.rgb is not None:
            methods = methods | Device.RGB
        if hasattr(self.dev, 'set_dim_value'):
            methods = methods | Device.DIM
        return methods

    def isDevice(self):
        return self.dev.is_device

    def isSensor(self):
        return self.dev.is_sensor
 
    def turnOn(self):
        LOGGER.debug("TURN ON!!")
        self.dev.turn_on()

    def turnOff(self):
        LOGGER.debug("TURN OFF!!")
        self.dev.turn_off()

    def up(self):
        self.dev.up()

    def down(self):
        self.dev.down()

    def stop(self):
        self.dev.stop()

    def setDim(self, value):
        LOGGER.debug("set effect")
        self.dev.set_dim_value(int(value/2.55))

    def getDim(self):
        return self.dev.get_dim_value()

    def setEffect(self, value):
        LOGGER.debug("set effect")
        self.dev.turn_on(effect=value)

    def setRgb(self, r, g, b, brightness=None):
        LOGGER.debug("set rgb")
        self.dev.turn_on(rgb=[r, g, b], mode='color', brightness=brightness)

    def setWhite(self, temp=None, brightness=None):
        LOGGER.debug("set white")
        self.dev.turn_on(mode='white', temp=temp, brightness=brightness)

    def _command(self, action, value, success, failure, **__kwargs):        
        if action == Device.TURNON and hasattr(self.dev, 'turn_on'):
            if hasattr(self.dev, 'set_dim_value'):
                self.dev.turn_on(brightness=100)
            else:
                self.dev.turn_on()
        elif action == Device.TURNOFF and hasattr(self.dev, 'turn_off'):
            self.dev.turn_off()
        elif action == Device.UP and hasattr(self.dev, 'up'):
            self.dev.up()
        elif action == Device.DOWN and hasattr(self.dev, 'down'):
            self.dev.down()
        elif action == Device.STOP and hasattr(self.dev, 'stop'):
            self.dev.stop()
        elif action == Device.DIM:
            self.dev.set_dim_value(int(value/2.55))
        elif action == Device.RGB:
            if value & 0x1000000:    #WhiteMode
                self.dev.turn_on(mode='withe', temp=value&0xFFFFFF)
            elif value & 0x2000000:    #Effect
                self.dev.turn_on(effect=value&0xFF)
            else:
                LOGGER.debug("RGB %s", [(value>>16)&0xFF, (value>>8)&0xFF, value&0xFF])
                self.dev.turn_on(
                    rgb=[(value>>16)&0xFF, (value>>8)&0xFF, value&0xFF],
                    mode='color')
        else:
            failure(Device.FAILED_STATUS_UNKNOWN)
        success()

    def _setState(self, state, value=None):        
        self.setState(state, value, onlyUpdateIfChanged=True)
    
    def _setSensorValue(self, values, valueType, value, scale):        
        values.append({'type': valueType, 'value':value, 'scale': scale})

    def update_name(self):
        name = self.local_name or self.dev.friendly_name()
        if self._name != name:
            self.setName(name)
            self.plugin.refreshClient()

    def _updated(self, _device):
        sensorValues = []
        refreshClient = False
        _lastUpdated = self.lastUpdated

        if hasattr(self.dev, 'state'):
            newState = Device.TURNON if self.dev.state else Device.TURNOFF
            if self.dev.state  \
                    and hasattr(self.dev, 'rgb') and self.dev.rgb is not None:
                rgb = self.dev.rgb
                rgb_value = (rgb[0]<<16) | (rgb[1]<<8) | rgb[2]
                self._setState(Device.RGB, rgb_value)
                self._setState(Device.DIM, int(self.dev.get_dim_value()*2.55))
                #self.plugin.refreshClient()
            elif self.dev.state and hasattr(self.dev, 'get_dim_value') \
                              and self.dev.get_dim_value() < 100:
                self._setState(Device.DIM, int(self.dev.get_dim_value()*2.55))
                #self.plugin.refreshClient()
            elif self.device_type == "POWERMETER":
                self._setSensorValue(sensorValues, Device.POWER,
                                     round(self.dev.state,1),
                                     Device.SCALE_POWER_WATT)
            elif self.device_type == "SENSOR":
                if self.device_sub_type == "temperature":
                    self._setSensorValue(sensorValues, Device.TEMPERATURE,
                                     round(self.dev.state,1),
                                     Device.SCALE_TEMPERATURE_CELCIUS)
                if self.device_sub_type == "voltage":
                    self._setSensorValue(sensorValues, Device.POWER,
                                     round(self.dev.state,1),
                                     Device.SCALE_POWER_VOLT)
            elif self._state != newState: #or (self.stateValue() if not hasattr(self, "_stateValue") else self._stateValue) != newStateValue:
                self._setState(newState)
                #self.plugin.refreshClient()
        if self.lastUpdated != _lastUpdated:
            refreshClient = True
        self.ip_addr = getattr(self.dev, 'ip_addr', '')
        self.update_name()
        if hasattr(self.dev, 'info_values') \
           and self.dev.info_values is not None:
            iv = self.dev.info_values                       
            if 'current_consumption' in iv:
                if iv['current_consumption'] is not None: #temp fix
                    self._setSensorValue(sensorValues, Device.POWER, 
                                        round(iv['current_consumption'],1),
                                        Device.SCALE_POWER_WATT)
            if 'humidity' in iv:
                 self._setSensorValue(sensorValues, Device.HUMIDITY,
                                     round(iv['humidity']),
                                     Device.SCALE_HUMIDITY_PERCENT)
            if 'temperature' in iv:
                 self._setSensorValue(sensorValues, Device.TEMPERATURE,
                                     round(iv['temperature'],1),
                                     Device.SCALE_TEMPERATURE_CELCIUS)
        if sensorValues != self._lastSensorValue:
            self._lastSensorValue = sensorValues
            refreshClient = True            
            self.setSensorValues(sensorValues)
        if self.dev.block and hasattr(self.dev.block, 'info_values') \
           and self.dev.block.info_values is not None:
            iv = self.dev.block.info_values
            self.firmware_version = iv.get("firmware_version", "")
            self.has_firmware_update = iv.get("has_firmware_update", "")
            self.latest_fw_version = iv.get("latest_fw_version", "") 
        if refreshClient:
            self.plugin.refreshClient()

    def params(self):
        return { 
            'ipAddr' : self.ip_addr,
            'typeName' : self.type_name,
            'deviceType' : self.device_type,
            'firmwareVersion' : self.firmware_version,
            'latestFwVersion' : self.latest_fw_version,
            'hasFirmwareUpdate' : self.has_firmware_update,
            'localName': self.local_name
        }

    def setParams(self, params):
        self.local_name = params.get('localName')
        self.firmware_version = params.get('firmwareVersion')

    @staticmethod
    def typeString():
        return 'Shelly'

class Shelly(Plugin):
    implements(IWebReactHandler)
    implements(IWebRequestHandler)

    def __init__(self):
        self.last_sent_data = None
        self.stop_ping_loop = threading.Event()

        self.deviceManager = DeviceManager(self.context)

        Application().registerShutdown(self.shutdown)

        settings = Settings('tellduslive.config')
        self.uuid = settings['uuid']       

        self.logHandler = ShellyLogger(self.uuid)
        LOGGER.addHandler(self.logHandler)

        self.setupPing()

        LOGGER.info('Init Shelly ' + __version__)
        self._initPyShelly()

    def setupPing(self):
        self.ping_count = 0
        self.ping_interval = PING_INTERVAL        

        self.ping()

        def loop():
            while not self.stop_ping_loop.wait(self.ping_interval):
                self.ping()

        self.ping_thread = threading.Thread(target=loop)
        self.ping_thread.daemon = True
        self.ping_thread.start()

    def _read_settings(self):
        settings = Settings(CONFIG)
        pys = self.pyShelly
        pys.set_cloud_settings(settings["cloud_server"], settings["cloud_auth_key"])
        pys.update_status_interval = timedelta(seconds=30)
        pys.only_device_id = settings["only_device_id"]
        pys.mdns_enabled = False #settings.get('mdns', True)

    def _initPyShelly(self):
        try:
            self.pyShelly.close()
        except:
            pass
        pys = self.pyShelly = pyShelly()
        pys.igmpFixEnabled = True    #Enable IGMP fix for ZNet
        pys.cb_device_added.append(self._device_added)
        pys.update_status_interval = timedelta(seconds=30)

        self._read_settings()  
        ######
        # pys.cb_block_added.append(self._block_added)
        # pys.cb_device_added.append(self._device_added)
        # pys.cb_device_removed.append(self._device_removed)
        pys.cb_save_cache = self._save_cache
        pys.cb_load_cache = self._load_cache
        # pys.username = conf.get(CONF_USERNAME)
        # pys.password = conf.get(CONF_PASSWORD)
        # pys.cloud_auth_key = conf.get(CONF_CLOUD_AUTH_KEY)
        # pys.cloud_server = conf.get(CONF_CLOUD_SERVER)
        # if zeroconf_async_get_instance:
        #     pys.zeroconf = await zeroconf_async_get_instance(self.hass)
        # tmpl_name = conf.get(CONF_TMPL_NAME)
        # if tmpl_name:
        #     pys.tmpl_name = tmpl_name
        # if additional_info:
        #     pys.update_status_interval = timedelta(seconds=update_interval)
        
        # if pys.only_device_id:
        #     pys.only_device_id = pys.only_device_id.upper()
        # pys.igmp_fix_enabled = conf.get(CONF_IGMPFIX)
        # pys.mdns_enabled = conf.get(CONF_MDNS)
        ###
        pys.start()
        pys.discover()

    def _save_cache(self, name, data):
        settings = Settings('Shelly.cache')
        settings[name] = data

    def _load_cache(self, name):
        settings = Settings('Shelly.cache')
        return json.loads(settings[name])

    def ping(self):
        try:
            headers = {"Content-type": "application/x-www-form-urlencoded",
                       "Accept": "text/plain", "Connection": "close"}
            self.ping_count += 1
            params = urllib.urlencode({'shelly':__version__,
                                       'pyShelly':self.pyShelly.version(), 
                                       'uuid':self.uuid, 
                                       'pluginid':1,
                                       'ping': self.ping_count, 
                                       'devices': len(self.pyShelly.blocks),
                                       'level' : self.logHandler.logLevel,
                                       'interval': self.ping_interval })
            conn = httplib.HTTPConnection("api.tarra.se")
            conn.request("POST", "/telldus/ping", params, headers)
            resp = conn.getresponse()
            body = resp.read()
            resp = json.loads(body)
            self.logHandler.logLevel = resp['level']
            self.ping_interval = resp['interval']
            conn.close()
        except:
            pass

    @staticmethod
    def getReactComponents():
        return {
            'shelly': {
                'title': 'Shelly',
                'script': 'shelly/shelly.js',
                'tags': ['menu'],
            }
        }

    def matchRequest(self, plugin, path):
        LOGGER.debug("MATCH %s %s", plugin, path)
        if plugin != 'shelly':
            return False
        #if path in ['reset', 'state']:
        #return True
        return True

    def _getConfig(self):
        settings = Settings(CONFIG)
        return {
            'cloud_server' : settings["cloud_server"],
            'cloud_auth_key' : settings["cloud_auth_key"]
        }

    def _getData(self, all_devs=False):
        shellyDevices = \
            self.deviceManager.retrieveDevices(None if all_devs else "Shelly")
        devices = []
        for d in shellyDevices:
            try:
                buttons = {}
                methods = d.methods()
                if methods & Device.TURNON:
                    buttons["on"]=True
                    buttons["off"]=True
                if methods & Device.UP:
                    buttons["up"]=True
                    buttons["down"]=True
                    buttons["stop"]=True
                buttons["firmware"]=getattr(d,"has_firmware_update", False)
                dev = {'id': d.id(),
                       'localid': d.localId(),
                       'name': d.name(),
                       'isDevice':d.isDevice(),
                       'state': d.state()[0],
                       'params': d.params(),
                       'available': False,
                       'buttons': buttons,
                       'typeName': getattr(d, 'type_name', '')
                      }                
                if hasattr(d, 'dev'):
                    _dev = d.dev
                    dev["available"] = _dev.available()
                    if (hasattr(_dev, 'rgb') and _dev.rgb is not None):
                        dev['rgb'] = '#' + ''.join('%02x'%v for v in _dev.rgb)
                    if hasattr(_dev, "get_dim_value"):
                        dev["brightness"] = _dev.get_dim_value()
                sensors = {}
                values = d.sensorValues()
                if 1 in values:
                    sensors['temp'] = \
                        "%.1f" % float(values[1][0]['value'])
                if 2 in values:
                    sensors['hum'] = \
                        "%.1f" % float(values[2][0]['value'])
                if 256 in values:
                    sensors['consumption'] = \
                        "%.1f" % float(values[256][0]['value'])
                if sensors:
                    dev["sensors"] = sensors
                devices.append(dev)
            except Exception as ex:
                LOGGER.exception("Error reading cache")
        devices.sort(key=lambda x: x['name'])
        return {'devices': devices,
                'pyShellyVer' : self.pyShelly.version() if self.pyShelly else "",
                'ver' : __version__,
                'id': self.uuid
                }

    def refreshClient(self):
        data = self._getData()
        if self.last_sent_data != data:
            self.last_sent_data = data
            Server(self.context).webSocketSend('shelly', 'refresh', data)

    def handleRequest(self, plugin, path, __params, **__kwargs):
        if path == 'list':
            return WebResponseJson(self._getData())

        if path == "config":
            if __params:
                settings = Settings(CONFIG)
                for param in __params:
                    if param in ['cloud_server', 'cloud_auth_key']:
                        settings[param]=__params[param]
                self._read_settings()
            return WebResponseJson(self._getConfig())

        if path == 'devices':            
            devices = list(map(lambda d: {                
                'id':d.id,
                'name': d.friendly_name(),
                'unit_id':d.unit_id,
                'type':d.type,
                'ip_addr': d.ip_addr,
                'is_device': d.is_device,
                'is_sensor':d.is_sensor,
                'sub_name':d.sub_name,
                'state_values':d.state_values,
                'state':d.state,
                'device_type':d.device_type,
                'device_sub_type':d.device_sub_type,
                'device_nr': d.device_nr,
                'master_unit': d.master_unit,
                'ext_sensor': d.ext_sensor,
                'info_values': d.info_values,
                'friendly_name': d.friendly_name()
            }, self.pyShelly.devices))
            return WebResponseJson(devices)

        if path == 'blocks':
            blocks = list(map(lambda d: {                
                'id':d.id,
                'unit_id':d.unit_id,
                'type':d.type,
                'ip_addr': d.ip_addr,
                'info_values': d.info_values
            }, self.pyShelly.blocks.values()))
            return WebResponseJson(blocks)

        if path == 'dump':
            shellyDevices = self.deviceManager.retrieveDevices()
            devices = list(map(lambda d: {'id':d.id(),
                                          'localid': d.localId(),
                                          'name': d.name(),
                                          'state': d.state(), 
                                          'params': d.params(),
                                          'stateValues' : d.stateValues(),
                                          'sensorValues' : d.sensorValues(),
                                          'isDevice': d.isDevice(),
                                          'isSensor': d.isSensor(),
                                          'methods' : d.methods(),
                                          'parameters': d.parameters(),
                                          'metadata': d.metadata(),
                                          'type': d.typeString()
                                          },
                               shellyDevices))
            return WebResponseJson({'devices': devices })

        if path in ['turnon', 'turnoff', 'up', 'down', 'stop', 'firmware_update']:
            LOGGER.info('Request ' + path)
            id = __params['id']
            device = self.deviceManager.device(int(id))
            if path == 'turnon':
                if hasattr(device.dev, 'brightness'):
                    device.dev.turn_on(brightness=100)
                else:
                    device.dev.turn_on()
            elif path == 'turnoff':
                device.dev.turn_off()
            elif path == 'up':
                device.dev.up()
            elif path == 'down':
                device.dev.down()
            elif path == 'stop':
                device.dev.stop()
            elif path == 'firmware_update':
                if device.dev.block:
                    device.dev.block.update_firmware()
            return WebResponseJson({})

        if path == "rgb":
            id = __params['id']
            r = __params['r']
            g = __params['g']
            b = __params['b']
            device = self.deviceManager.device(int(id))
            device.dev.set_values(rgb=[r,g,b])
            self.refreshClient()
            return WebResponseJson({})

        if path == "rename":
            id = __params['id']
            name = __params['name']
            device = self.deviceManager.device(int(id))
            device.local_name = name            
            device.update_name()
            self.refreshClient()
            return WebResponseJson({})

        if path == "clean":
            self.deviceManager.removeDevicesByType('Shelly')
            self._initPyShelly()
            self.refreshClient()
            return WebResponseJson({'msg':'Clean done'})

        if path == "discover":
            self.pyShelly.discover()
            return WebResponseJson({})

        if path == "addMember":
            LOGGER.debug("Add membership")
            import socket
            import struct
            mreq = struct.pack("=4sl",
                               socket.inet_aton("224.0.1.187"),
                               socket.INADDR_ANY)
            self.pyShelly._socket.setsockopt(socket.IPPROTO_IP,
                                             socket.IP_ADD_MEMBERSHIP,
                                             mreq)
            return WebResponseJson({})

        if path == "dropMember":
            LOGGER.debug("Drop membership")
            import socket
            import struct
            mreq = struct.pack("=4sl",
                               socket.inet_aton("224.0.1.187"),
                               socket.INADDR_ANY)
            self.pyShelly._socket.setsockopt(socket.IPPROTO_IP,
                                             socket.IP_DROP_MEMBERSHIP,
                                             mreq)
            return WebResponseJson({})

        if path == "initSocket":
            self.pyShelly.init_socket()
            return WebResponseJson({'msg':'init socket done'})

    def _device_added(self, dev, code):
        LOGGER.info('Add device ' + dev.id + ' ' + str(code))
        if (dev.device_type != "POWERMETER" and dev.device_type != "SWITCH" \
            and dev.device_sub_type != "humidity") \
           or dev.master_unit or dev.major_unit:
            device = ShellyDevice(dev, self)
            self.deviceManager.addDevice(device)

    def shutdown(self):
        if self.pyShelly is not None:
            self.pyShelly.close()
            self.pyShelly = None
        if self.stop_ping_loop is not None:
            self.stop_ping_loop.set()  

    def tearDown(self):
		deviceManager = DeviceManager(self.context)
		deviceManager.removeDevicesByType('shelly')  

class ShellyLogger(StreamHandler):
    def __init__(self, uuid):
        StreamHandler.__init__(self)
        self.cnt = 0
        self.uuid = uuid
        self.logLevel = LOG_LEVEL

    def emit(self, record):        
        if record.levelno >= self.logLevel:
            try:
                msg = self.format(record)
                self.cnt += 1
                headers = {"Content-type": "application/x-www-form-urlencoded",
                           "Accept": "text/plain", "Connection": "close"}
                params = urllib.urlencode({
                    'level':record.levelno,
                    'uuid':self.uuid,
                    'pluginid':1,
                    'cnt': self.cnt,
                    'msg': msg})
                conn = httplib.HTTPConnection("api.tarra.se")
                conn.request("POST", "/telldus/log", params, headers)
                resp = conn.getresponse()
                conn.close()
            except:
                pass
