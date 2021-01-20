# Shelly plugin för Telldus Tellstick
Shelly plugin for Telldus Tellstick Net/ZNet v1/v2 (white box, Net,ZNet v1, v2)

Shelly devices will show as a device in Telldus Live and mobile app. It
support on/off, dimming, rgb, sensors (power, temp etc)

## Features

- Automatically discover all Shelly devices
- Monitor status (state, temperature, humidity, power, ip, fw etc.)
- Control (turn on/off, dim, color, effects, up/down etc.)
- Switch sensors to show status of switch button
- Works with Shelly default settings, no extra configuration
- Runs locally, you don't have to add the device to Shelly Cloud
- Coexists with Shelly Cloud so you can continue to use Shelly Cloud and Shelly apps
- Using CoAP and REST for communication (not MQTT)
- Working with both static or dynamic ip addresses on your devices
- Using events so very fast response (no polling)
- Device configuration (name)
- Support firmware update
- Support proxy to allow Shelly devices in other LANs.
- Receive device names from Shelly Cloud (cloud_auth_key/cloud_server)

## Devices supported
- Shelly 1
- Shelly 1L
- Shelly 1PM
- Temperature addon for Shelly 1(PM)
- Shelly 2 (relay or roller mode)
- Shelly 2.5 (relay or roller mode)
- Shelly 2LED (not verified)
- Shelly 3EM
- Shelly 4
- Shelly Air
- Shelly Bulb
- Shelly Button-1
- Shelly Duo
- Shelly Duo GU10
- Shelly Dimmer / Dimmer SL
- Shelly Dimmer 2
- Shelly Door/Window
- Shelly Door/Window 2
- Shelly EM
- Shelly Flood
- Shelly Gas
- Shelly H&T
- Shelly i3
- Shelly Plug
- Shelly Plug S
- Shelly Plug US
- Shelly RGBW2 (rgb or 4 channels)
- Shelly RGBWW
- Shelly UNI
- Shelly Vintage

Full support for all firmware versions.

## Requirement
This plugin need Tellstick version 1.3.1.

## Installation
[Se wiki pages (only swedish)](https://github.com/StyraHem/tellstick-server-plugins/wiki/Shelly-plugin-f%C3%B6r-Telldus-Tellstick)

## Screen shots
![Screenshot](https://raw.githubusercontent.com/StyraHem/tellstick-server-plugins/master/shelly/img/screencapture1.png)

## Example of Lua comamnds
```lua
-- File: TestShelly.lua
local deviceName = "Shelly1" -- Name of your Shelly device
local deviceManager = require "telldus.DeviceManager"

function onInit()
	print("onInit")
	local device = deviceManager:findByName(deviceName)

	if device == nil then
		print("Could not find the device %s", deviceName)
		return
	end

	--Here you can do command on your device, see below
	device:turnon()
end 
```
### Shelly 1, Shelly 2, Shelly 4, Shelly PLUG
```lua
--On and off
device:turnon()
device:turnoff()
```
### Shelly 2, roller mode
```lua
--Roller
device:up()
device:down()
device:stop()
```
### Shelly Bulb, Shelly RGBWW, Shelly RGBW2
```lua
--On and off
device:turnon()
device:turnoff()

--Dim
device:command("dim", 255) --Full brightness
device:command("dim", 5)	 --Low brightness
device:setDim(255) --Full brightness
device:setDim(5) --Low brightness

--White mode
device:command("rgb", 0x1000000 + 6500) --White 6500K
device:command("rgb", 0x1000000 + 3000) --White 3000K
device.setWhite() -- switch to white mode
device.setWhite(6500) -- switch to white mode, 6500K
device.setWhite(3500, 255/2 ) -- switch to white mode, 3500K, half brightness

--RGB mode
device:command("rgb", 0xFF0000) --Red
device:command("rgb", 0x00FF00) --Green
device:command("rgb", 0x0000FF) --Blue'
device:setRgb( 0xFF, 0, 0 ) -- Red
device:setRgb( 0, 255, 0 , 255/2 ) -- Green, half brightness

--Effects
device:command("rgb", 0x2000000 + 0) --No effect
device:command("rgb", 0x2000000 + 1) --meteor shower
device:command("rgb", 0x2000000 + 2) --gradual change
device:command("rgb", 0x2000000 + 3) --breath
device:command("rgb", 0x2000000 + 4) --flash
device:command("rgb", 0x2000000 + 5) --on/off gradual
device:command("rgb", 0x2000000 + 6) --red/green flash
device:setEffect(0) --No effect
device:setEffect(6) --red/green flash
```
