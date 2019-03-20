# -*- coding: utf-8 -*-

from base import Application, Plugin, implements, Settings
from threading import Thread
from telldus import DeviceManager, Device
from telldus.web import IWebReactHandler
from web.base import IWebRequestHandler, Server, WebResponseJson
import logging
from logging import StreamHandler
import httplib, urllib
import json
from pyShelly import pyShelly
import threading

__name__ = 'Shelly'
__version__ = '0.0.21'

PING_INTERVAL = 60
LOG_LEVEL = 20

logger = logging.getLogger('pyShelly')

class ShellyDevice(Device):

    def __init__(self, dev, plugin):
        super(ShellyDevice, self).__init__()
        self._localid = dev.id
        self.dev = dev
        self.plugin = plugin
        self.ipaddr = getattr(dev, 'ipaddr', '')
        self.typeName = dev.typeName()
        if self._name is None:
            self.setName(dev.typeName() + " (" + dev.id + ")")
        dev.cb_updated = self._updated

    def localId(self):
        return self._localid

    def methods(self):
        methods = 0
        if hasattr(self.dev, 'turnOn'):
            methods = methods | Device.TURNON
        if hasattr(self.dev, 'turnOff'):
            methods = methods | Device.TURNOFF
        if hasattr(self.dev, 'up'):
            methods = methods | Device.UP
        if hasattr(self.dev, 'down'):
            methods = methods | Device.DOWN
        if hasattr(self.dev, 'stop'):
            methods = methods | Device.STOP
        if self.dev.devType == 'LIGHT':
            methods = methods | Device.RGB |Device.DIM
        return methods

    def isDevice(self):
        return self.dev.isDevice

    def isSensor(self):
        return self.dev.isSensor
 
    def turnOn(self):
        self.dev.turnOn()

    def turnOff(self):
        self.dev.turnOff()

    def up(self):
        self.dev.up()

    def down(self):
        self.dev.down()

    def stop(self):
        self.dev.stop()

    def setDim(self, value):
        self.dev.setDimValue(int(value/2.55))

    def getDim(self):
        return self.dev.getDimValue()

    def setEffect(self, value):
        self.dev.turnOn(effect=value)

    def setRgb(self, r, g, b, brightness=None):
        self.dev.turnOn(rgb=[r, g, b], isModeWhite=False, brightness=brightness)

    def setWhite(self, temp=None, brightness=None):
        self.dev.turnOn(isModeWhite=True, temp=temp, brightness=brightness)

    def _command(self, action, value, success, failure, **__kwargs):

        if action == Device.TURNON and hasattr(self.dev, 'turnOn'):
            self.dev.turnOn(brightness=100)
        elif action == Device.TURNOFF and hasattr(self.dev, 'turnOff'):
            self.dev.turnOff()
        elif action == Device.UP and hasattr(self.dev, 'up'):
            self.dev.up()
        elif action == Device.DOWN and hasattr(self.dev, 'down'):
            self.dev.down()
        elif action == Device.STOP and hasattr(self.dev, 'stop'):
            self.dev.stop()
        elif action == Device.DIM:
            self.dev.setDimValue(int(value/2.55))
        elif action == Device.RGB:
            if value & 0x1000000:    #WhiteMode
                self.dev.turnOn(isModeWhite=True, temp=value&0xFFFFFF)
            elif value & 0x2000000:    #Effect
                self.dev.turnOn(effect=value&0xFF)
            else:
                logger.debug("RGB %s", [(value>>16)&0xFF, (value>>8)&0xFF, value&0xFF])
                self.dev.turnOn(rgb=[(value>>16)&0xFF, (value>>8)&0xFF, value&0xFF],
                                isModeWhite=False)
        else:
            failure(Device.FAILED_STATUS_UNKNOWN)

    def _updated(self):
        if hasattr(self.dev, 'state'):
            #Not implemented yet in ZNet
            #self.setState(Device.TURNON if self.dev.state else Device.TURNOFF,
            #               onlyUpdateIfChanged=True)
            newState = Device.TURNON if self.dev.state else Device.TURNOFF
            newStateValue = ''
            if self.dev.state and hasattr(self.dev, 'getDimValue') and self.dev.getDimValue() < 100:
                newState = Device.DIM
                newStateValue = int(self.dev.getDimValue()*2.55)
            if hasattr(self.dev, 'getDimValue'):
                logger.debug("getDimValue %s %s %s %s", newState, newStateValue, self._stateValue, self.dev.getDimValue())
            if self._state != newState or self._stateValue != newStateValue:
                logger.debug("UPDATE")
                self.setState(newState, newStateValue)
                self.plugin.refreshClient()
        if hasattr(self.dev, 'sensorValues'):
            if 'watt' in self.dev.sensorValues:
                self.setSensorValue(Device.WATT, self.dev.sensorValues['watt'],
                                    Device.SCALE_POWER_WATT)
                self.plugin.refreshClient()
            if 'temperature' in self.dev.sensorValues:
                self.setSensorValue(Device.TEMPERATURE, self.dev.sensorValues['temperature'],
                                    Device.SCALE_TEMPERATURE_CELCIUS)
                self.plugin.refreshClient()
            if 'humidity' in self.dev.sensorValues:
                self.setSensorValue(Device.HUMIDITY, self.dev.sensorValues['humidity'],
                                    Device.SCALE_HUMIDITY_PERCENT)
                self.plugin.refreshClient()

    @staticmethod
    def typeString():
        return 'Shelly'


class Shelly(Plugin):
    implements(IWebReactHandler)
    implements(IWebRequestHandler)

    def __init__(self):
        logger.info('Init Shelly')

        self.deviceManager = DeviceManager(self.context)
        #deviceManager.removeDevicesByType('Shelly')
        #deviceManager.removeDevicesByType('')

        self._initPyShelly()

        Application().registerShutdown(self.shutdown)

        settings = Settings('tellduslive.config')
        self.uuid = settings['uuid']
                
        host = 'api.tarra.se'
        url = '/telldus/log'
        
        self.logHandler = ShellyLogger(self.uuid)
        logger.addHandler(self.logHandler)        
        
        self.setupPing()

    def setupPing(self):        
        logger.info("PING setup")
        
        self.ping();
        
        logger.info("PING setup 2")
        
        def loop():
            logger.info("PING Loop starting")
            while not self.stopPingLoop.wait(self.pingInterval):
                logger.debug("PING Loop inside")
                self.ping();
        
        self.pingCnt = 0
        self.pingInterval = PING_INTERVAL
        self.stopPingLoop = threading.Event()
        self.pingThread = threading.Thread(target=loop)
        self.pingThread.daemon = True
        self.pingThread.start()

    def _initPyShelly(self):
        try:
            self.pyShelly.close()    
        except:
            pass
        self.pyShelly = pyShelly()
        self.pyShelly.igmpFixEnabled = True    #Enable IGMP fix for ZNet
        self.pyShelly.cb_deviceAdded = self._deviceAdded
        self.pyShelly.open()
        self.pyShelly.discover()
        
            
    def ping(self):
        try:
            headers = {"Content-type": "application/x-www-form-urlencoded",
                       "Accept": "text/plain"}
            self.pingCnt += 1
            params = urllib.urlencode({'shelly':__version__, 'pyShelly':self.pyShelly.version(), 
                                       'uuid':self.uuid, 'ping': self.pingCnt, 
                                       'devices': len(self.pyShelly.blocks),
                                       'level' : self.logHandler.logLevel, 'interval': self.pingInterval })
            conn = httplib.HTTPConnection("api.tarra.se")
            conn.request("POST", "/telldus/ping", params, headers)
            resp = conn.getresponse()
            body = resp.read()
            resp = json.loads(body)
            self.logHandler.logLevel = resp['level']
            self.pingInterval = resp['interval']
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

    def _getData(self, all=False):
        shellyDevices = self.deviceManager.retrieveDevices("" if all else "Shelly")
        devices = []
        for d in shellyDevices:
            #ip = d.ipaddr if hasattr(d, 'ipaddr') else ''
            available = False
            rgb = None
            mode = None
            methods = d.methods()
            buttons = {'on' : (methods & Device.TURNON) > 0,
                       'off' : (methods & Device.TURNOFF) > 0,
                       'up' : (methods & Device.UP) > 0,
                       'down' : (methods & Device.DOWN) > 0,
                       'stop' : (methods & Device.STOP) > 0
                      }
            if hasattr(d, 'dev'):
                dev = d.dev
                available = d.dev.available()
                mode = getattr(dev, 'mode', '')
                if mode=='color' and hasattr(dev, 'rgb') and dev.rgb is not None:
                    rgb = '#' + ''.join('%02x'%v for v in dev.rgb)
                
            sensors = {}
            values = d.sensorValues()
            if 1 in values:
                sensors['temp']="%.1f" % float(values[1][0]['value'])
            if 2 in values:
                sensors['hum']="%.0f" % float(values[2][0]['value'])
            if 256 in values:
                sensors['watt']="%.2f" % float(values[256][0]['value'])
                
            
            dev = {'id': d.id(), 'localid': d.localId(), 'name': d.name(), 'isDevice':d.isDevice(),
                   'state': d.state(), 'params': d.params(), 'ipaddr': getattr(d, 'ipaddr', ''),
                   'available': available, 'sensors': sensors, 'debug': values, 
                   'buttons': buttons, 'typeName': getattr(d, 'typeName', ''),
                   'rgb': rgb, 'mode': getattr(d, 'mode', mode)
                  }
            devices.append(dev)
        devices.sort(key=lambda x: x['name'])
        return {'devices': devices, 'pyShellyVer' : self.pyShelly.version(), 'ver' : __version__}

    def refreshClient(self):
        Server(self.context).webSocketSend('shelly', 'refresh', self._getData())

    def handleRequest(self, plugin, path, __params, **__kwargs):
        if path == 'list':
            return WebResponseJson(self._getData())

        #if path == 'loglevel':
        #    self.logHandler
        #    return WebResponseJson({'log' : })

        if path == 'dump':
            shellyDevices = self.deviceManager.retrieveDevices()
            devices = list(map(lambda d: {'id':d.id(), 'localid': d.localId(),
                                          'name': d.name(), 'state': d.state(), 
                                          'params': d.params()},
                               shellyDevices))
            return WebResponseJson({'devices': devices })

        if path in ['turnon', 'turnoff', 'up', 'down', 'stop']:
            logger.info('Request ' + path)
            id = __params['id']
            device = self.deviceManager.device(int(id))
            if path == 'turnon':
                device.dev.turnOn()
            elif path == 'turnoff':
                device.dev.turnOff()
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
            device.dev.setValues(rgb=[r,g,b])
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
            mreq = struct.pack("=4sl", socket.inet_aton("224.0.1.187"), socket.INADDR_ANY)
            self.pyShelly._socket.setsockopt(socket.IPPROTO_IP,
                                                   socket.IP_ADD_MEMBERSHIP, mreq)
            return WebResponseJson({})

        if path == "dropMember":
            logger.debug("Drop membership")
            import socket
            import struct
            mreq = struct.pack("=4sl", socket.inet_aton("224.0.1.187"), socket.INADDR_ANY)
            self.pyShelly._socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP,
                                                   mreq)
            return WebResponseJson({})

        if path == "initSocket":
            self.pyShelly.initSocket()
            return WebResponseJson({'msg':'init socket done'})

    def _deviceAdded(self, dev, code):
        logger.info('Add device ' + dev.id + ' ' + str(code))
        device = ShellyDevice(dev, self)
        self.deviceManager.addDevice(device)

    def shutdown(self):
        if self.pyShelly is not None:
            self.pyShelly.close()
            self.pyShelly = None
        self.stopPingLoop.set()    

class ShellyLogger(StreamHandler):
    def __init__(self, uuid):
        StreamHandler.__init__(self)
        self.cnt = 0
        self.uuid = uuid
        self.logLevel = LOG_LEVEL
        
    def emit(self, record):        
        if record.levelno >= self.logLevel:
            msg = self.format(record)
            self.cnt += 1
            headers = {"Content-type": "application/x-www-form-urlencoded",
                       "Accept": "text/plain"}
            params = urllib.urlencode({'level':record.levelno, 'uuid':self.uuid, 'cnt': self.cnt, 'msg': msg})                       
            conn = httplib.HTTPConnection("api.tarra.se")
            conn.request("POST", "/telldus/log", params, headers)
            resp = conn.getresponse()
            conn.close()

