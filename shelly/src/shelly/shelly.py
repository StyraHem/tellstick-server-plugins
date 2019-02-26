# -*- coding: utf-8 -*-

from base import Application, Plugin, implements
from threading import Thread
from telldus import DeviceManager, Device
from telldus.web import IWebReactHandler
from web.base import IWebRequestHandler, Server, WebResponseJson
import logging
import json
from pyShelly import pyShelly

__name__ = 'Shelly'
__version__ = '0.0.6'

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
        if self.dev.devType == 'RGB':
            methods = methods | Device.RGB | Device.DIM
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
        self.dev.dim(int(value/2.55))

    def getDim(self):
        return self.dev.brightness

    def setEffect(self, value):
        self.dev.turnOn(effect=value)

    def setRgb(self, r, g, b, brightness=None):
        self.dev.turnOn(rgb=[r, g, b], isModeWhite=False, brightness=brightness)

    def setWhite(self, temp=None, brightness=None):
        self.dev.turnOn(isModeWhite=True, temp=temp, brightness=brightness)

    def _command(self, action, value, success, failure, **__kwargs):

        if action == Device.TURNON and hasattr(self.dev, 'turnOn'):
            self.dev.turnOn()
        elif action == Device.TURNOFF and hasattr(self.dev, 'turnOff'):
            self.dev.turnOff()
        elif action == Device.UP and hasattr(self.dev, 'up'):
            self.dev.up()
        elif action == Device.DOWN and hasattr(self.dev, 'down'):
            self.dev.down()
        elif action == Device.STOP and hasattr(self.dev, 'stop'):
            self.dev.stop()
        elif action == Device.DIM:
            self.dev.dim(int(value/2.55))
        elif action == Device.RGB:
            if value & 0x1000000:    #WhiteMode
                self.dev.turnOn(isModeWhite=True, temp=value&0xFFFFFF)
            elif value & 0x2000000:    #Effect
                self.dev.turnOn(effect=value&0xFF)
            else:
                print("RGB", [(value>>16)&0xFF, (value>>8)&0xFF, value&0xFF])
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
            if self.dev.state and hasattr(self.dev, 'brightness') and self.dev.brightness < 100:
                newState = Device.DIM
                newStateValue = int(self.dev.brightness*2.55)
                            
            if self._state != newState or self._stateValue != newStateValue:
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
        self.logQueue = ['Init Shelly']

        self.deviceManager = DeviceManager(self.context)
        #deviceManager.removeDevicesByType('Shelly')
        #deviceManager.removeDevicesByType('')

        self.pyShelly = pyShelly()
        self.pyShelly.igmpFixEnabled = True    #Enable IGMP fix for ZNet
        self.pyShelly.cb_deviceAdded = self._deviceAdded
        self.pyShelly.open()
        self.pyShelly.discover()

        Application().registerShutdown(self.shutdown)

    def log(self, msg):
        logging.info(msg)
        self.logQueue.append(msg)

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
        print "MATCH ", plugin, path
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
                if hasattr(dev, 'rgb') and dev.rgb is not None:
                    rgb = '#' + ''.join('%02x'%v for v in dev.rgb)
            dev = {'id': d.id(), 'localid': d.localId(), 'name': d.name(),
                   'state': d.state(), 'params': d.params(), 'ipaddr': getattr(d, 'ipaddr', ''),
                   'available': available, 'sensors': d.sensorValues(),
                   'buttons': buttons, 'typeName': getattr(d, 'typeName', ''), 'rgb': rgb
                  }
            devices.append(dev)
        devices.sort(key=lambda x: x['name'])
        return {'devices': devices, 'pyShellyVer' : self.pyShelly.version(), 'ver' : __version__}

    def refreshClient(self):
        Server(self.context).webSocketSend('shelly', 'refresh', self._getData())

    def handleRequest(self, plugin, path, __params, **__kwargs):
        if path == 'list':
            return WebResponseJson(self._getData())

        if path == 'log':
            return WebResponseJson({'log' : self.logQueue})

        if path == 'dump':
            shellyDevices = self.deviceManager.retrieveDevices()
            devices = list(map(lambda d: {'id':d.id(), 'localid': d.localId(),
                                          'name': d.name(), 'state': d.state(), 
                                          'params': d.params()},
                               shellyDevices))
            return WebResponseJson({'devices': devices, 'log': self.logQueue})

        if path in ['turnon', 'turnoff', 'up', 'down', 'stop']:
            logging.info('Request ' + path)
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

        if path == "rename":
            id = __params['id']
            name = __params['name']
            device = self.deviceManager.device(int(id))
            device.setName(name)
            self.refreshClient()
            return WebResponseJson({})

        if path == "clean":
            self.deviceManager.removeDevicesByType('Shelly')
            self.pyShelly.close()
            self.pyShelly = pyShelly()
            self.pyShelly.igmpFixEnabled = True    #Enable IGMP fix for ZNet
            self.pyShelly.cb_deviceAdded = self._deviceAdded
            self.pyShelly.discover()
            self.refreshClient()
            return WebResponseJson({})

        if path == "discover":
            self.pyShelly.discover()
            return WebResponseJson({})

        if path == "addMember":
            print "Add membership"
            import socket
            import struct
            mreq = struct.pack("=4sl", socket.inet_aton("224.0.1.187"), socket.INADDR_ANY)
            print self.pyShelly._socket.setsockopt(socket.IPPROTO_IP,
                                                   socket.IP_ADD_MEMBERSHIP, mreq)
            return WebResponseJson({})

        if path == "dropMember":
            print "Drop membership"
            import socket
            import struct
            mreq = struct.pack("=4sl", socket.inet_aton("224.0.1.187"), socket.INADDR_ANY)
            print self.pyShelly._socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP,
                                                   mreq)
            return WebResponseJson({})

        if path == "initSocket":
            self.pyShelly.initSocket()
            return WebResponseJson({})

    def _deviceAdded(self, dev, code):
        self.log('Add device ' + dev.id + ' ' + str(code))
        device = ShellyDevice(dev, self)
        self.deviceManager.addDevice(device)

    def shutdown(self):
        if self.pyShelly is not None:
            self.pyShelly.close()
            self.pyShelly = None
