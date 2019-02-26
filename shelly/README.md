# shelly
Shelly plugin for Tellstick server (Telldus Net/ZNet)

![Screenshot](https://raw.githubusercontent.com/StyraHem/tellstick-server-plugins/master/shelly/img/screencapture1.png)

## Example of Lua comamnds
```lua
-- File: TestRGB.lua
local deviceName = "RGB"    -- Name of your RGB device
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
### Shelly 1, Shelly 2, Shelly 4
```lua
--Switch
device:turnon()
device:turnoff()
```

### Shelly Bulb, Shelly RGBWW, Shelly RGBW2
```lua
--Dim
device:command("dim", 255, "RGB.lua") --Full brightness
device:command("dim", 5, "RGB.lua")	 --Low brightness
device:setDim(255) --Full brightness
device:setDim(5) --Low brightness

--White mode
device:command("rgb", 0x1000000 + 6500, "RGB.lua") --White 6500K
device:command("rgb", 0x1000000 + 3000, "RGB.lua") --White 3000K
device.setWhite() -- switch to white mode
device.setWhite(6500) -- switch to white mode, 6500K
device.setWhite(3500, 255/2 ) -- switch to white mode, 3500K, half brightness

--RGB mode
device:command("rgb", 0xFF0000, "RGB.lua") --Red
device:command("rgb", 0x00FF00) --Green
device:command("rgb", 0x0000FF, "RGB.lua") --Blue'
device:setRgb( 0xFF, 0, 0 ) -- Red
device:setRgb( 0, 255, 0 , 255/2 ) -- Green, half brightness

--Effects
device:command("rgb", 0x2000000 + 0, "RGB.lua") --No effect
device:command("rgb", 0x2000000 + 1, "RGB.lua") --meteor shower
device:command("rgb", 0x2000000 + 2, "RGB.lua") --gradual change
device:command("rgb", 0x2000000 + 3, "RGB.lua") --breath
device:command("rgb", 0x2000000 + 4, "RGB.lua") --flash
device:command("rgb", 0x2000000 + 5, "RGB.lua") --on/off gradual
device:command("rgb", 0x2000000 + 6, "RGB.lua") --red/green flash
device:setEffect(0) --No effect
device:setEffect(6) --red/green flash
```
