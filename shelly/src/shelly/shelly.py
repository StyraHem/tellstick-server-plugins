# -*- coding: utf-8 -*-

from base import Application, Plugin, implements, Settings
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
__version__ = '0.1.0b1'

PING_INTERVAL = 60
LOG_LEVEL = 20

logger = logging.getLogger('pyShelly')

class ShellyDevice(Device):

    def __init__(self, dev, plugin):
        super(ShellyDevice, self).__init__()
        self._localid = dev.id
        self.dev = dev
        self.plugin = plugin
        self.ip_addr = getattr(dev, 'ip_addr', '')
        self.type_name = dev.type_name()# + " " + dev.device_type
        if self._name is None:
            self.setName(dev.type_name() + " (" + dev.id + ")")
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
        logger.debug("TURN ON!!")
        self.dev.turn_on()

    def turnOff(self):
        logger.debug("TURN OFF!!")
        self.dev.turn_off()

    def up(self):
        self.dev.up()

    def down(self):
        self.dev.down()

    def stop(self):
        self.dev.stop()

    def setDim(self, value):
        logger.debug("set effect")
        self.dev.set_dim_value(int(value/2.55))

    def getDim(self):
        return self.dev.get_dim_value()

    def setEffect(self, value):
        logger.debug("set effect")
        self.dev.turn_on(effect=value)

    def setRgb(self, r, g, b, brightness=None):
        logger.debug("set rgb")
        self.dev.turn_on(rgb=[r, g, b], mode='color', brightness=brightness)

    def setWhite(self, temp=None, brightness=None):
        logger.debug("set white")
        self.dev.turn_on(mode='white', temp=temp, brightness=brightness)

    def _command(self, action, value, success, failure, **__kwargs):        
        if action == Device.TURNON and hasattr(self.dev, 'turn_on'):
            print("TURN ON-----------------------------------")
            print(value)                    
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
                logger.debug("RGB %s", [(value>>16)&0xFF, 
                             (value>>8)&0xFF, value&0xFF])
                self.dev.turn_on(
                    rgb=[(value>>16)&0xFF, (value>>8)&0xFF, value&0xFF],
                    mode='color')
        else:
            failure(Device.FAILED_STATUS_UNKNOWN)
        success()

    def _updated(self, _device):
        if hasattr(self.dev, 'state'):
            #Not implemented yet in ZNet
            #self.setState(Device.TURNON if self.dev.state else Device.TURNOFF,
            #               onlyUpdateIfChanged=True)
            newState = Device.TURNON if self.dev.state else Device.TURNOFF
            newStateValue = None
            if self.dev.state  \
                    and hasattr(self.dev, 'rgb') and self.dev.rgb is not None:
                rgb = self.dev.rgb
                rgb_value = (rgb[0]<<16) | (rgb[1]<<8) | rgb[2]
                self.setState(Device.RGB, rgb_value)
                self.setState(Device.DIM, int(self.dev.get_dim_value()*2.55))
                self.plugin.refreshClient()
            elif self.dev.state and hasattr(self.dev, 'get_dim_value') \
                              and self.dev.get_dim_value() < 100:
                self.setState(Device.DIM, int(self.dev.get_dim_value()*2.55))
                self.plugin.refreshClient()
            elif self._state != newState or (self.stateValue() if not hasattr(self, "_stateValue") else self._stateValue) != newStateValue:
                self.setState(newState, newStateValue)
                self.plugin.refreshClient()
        if hasattr(self.dev, 'sensor_values') \
           and self.dev.sensor_values is not None:
            if 'consumption' in self.dev.sensor_values:
                if self.dev.sensor_values['consumption'] is not None: #temp fix
                    self.setSensorValue(Device.WATT, 
                                        self.dev.sensor_values['consumption'],
                                        Device.SCALE_POWER_WATT)
                self.plugin.refreshClient()
            if 'temperature' in self.dev.sensor_values:
                self.setSensorValue(Device.TEMPERATURE,
                                    self.dev.sensor_values['temperature'],
                                    Device.SCALE_TEMPERATURE_CELCIUS)
                self.plugin.refreshClient()
            if 'humidity' in self.dev.sensor_values:
                self.setSensorValue(Device.HUMIDITY,
                                    self.dev.sensor_values['humidity'],
                                    Device.SCALE_HUMIDITY_PERCENT)
                self.plugin.refreshClient()

    def params(self):
        return { 
            'ipAddr' : self.ip_addr,
            'typeName' : self.type_name
        }

    #def setParams(self, params):
        #self.ip_addr = params.get('ipAddr') + '?'
        #self.type_name = params.get('typeName')

    @staticmethod
    def typeString():
        return 'Shelly'

class Shelly(Plugin):
    implements(IWebReactHandler)
    implements(IWebRequestHandler)

    def __init__(self):
        self.stop_ping_loop = threading.Event()

        self.deviceManager = DeviceManager(self.context)

        Application().registerShutdown(self.shutdown)

        settings = Settings('tellduslive.config')
        self.uuid = settings['uuid']

        self.logHandler = ShellyLogger(self.uuid)
        logger.addHandler(self.logHandler)

        self.setupPing()

        logger.info('Init Shelly ' + __version__)
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

    def _initPyShelly(self):
        try:
            self.pyShelly.close()
        except:
            pass
        self.pyShelly = pyShelly()
        self.pyShelly.igmpFixEnabled = True    #Enable IGMP fix for ZNet
        self.pyShelly.cb_device_added.append(self._device_added)
        self.pyShelly.open()
        self.pyShelly.discover()

    def ping(self):
        try:
            headers = {"Content-type": "application/x-www-form-urlencoded",
                       "Accept": "text/plain"}
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
        logger.debug("MATCH %s %s", plugin, path)
        if plugin != 'shelly':
            return False
        #if path in ['reset', 'state']:
        #return True
        return True

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
                        "%.0f" % float(values[2][0]['value'])
                if 256 in values:
                    sensors['consumption'] = \
                        "%.2f" % float(values[256][0]['value'])
                if sensors:
                    dev["sensors"] = sensors
                devices.append(dev)
            except:
                logger.exception("Error reading cache")
        devices.sort(key=lambda x: x['name'])
        return {'devices': devices,
                'pyShellyVer' : self.pyShelly.version(),
                'ver' : __version__,
                'id': self.uuid
                }

    def refreshClient(self):
        Server(self.context).webSocketSend('shelly', 'refresh', self._getData())

    def handleRequest(self, plugin, path, __params, **__kwargs):
        if path == 'list':
            return WebResponseJson(self._getData())

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

        if path in ['turnon', 'turnoff', 'up', 'down', 'stop']:
            logger.info('Request ' + path)
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
            device.setName(name)
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
            logger.debug("Add membership")
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
            logger.debug("Drop membership")
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
        logger.info('Add device ' + dev.id + ' ' + str(code))
        if dev.device_type != "POWERMETER" and dev.device_type != "SWITCH":
            device = ShellyDevice(dev, self)
            self.deviceManager.addDevice(device)

    def shutdown(self):
        if self.pyShelly is not None:
            self.pyShelly.close()
            self.pyShelly = None
        if self.stop_ping_loop is not None:
            self.stop_ping_loop.set()    

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
                           "Accept": "text/plain"}
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
