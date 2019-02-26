# shelly
Shelly plugin for Tellstick server (Telldus Net/ZNet)

[![Screenshot](https://raw.githubusercontent.com/StyraHem/tellstick-server-plugins/master/shelly/img/screencapture1.png)]

## Example of Lua comamnds to controll your shelly RGB devices
```lua
-- File: TestRGB.lua
local deviceName = "RGB"    -- Name of your RGB device
local deviceManager = require "telldus.DeviceManager"

function onInit()
	print("onInit")
	local rgb = deviceManager:findByName(deviceName)

	if rgb == nil then
		print("Could not find the device %s", deviceName)
		return
	end

	--Dim
	rgb:command("dim", 255, "RGB.lua") --Full brightness
	rgb:command("dim", 5, "RGB.lua")	 --Low brightness
	rgb:setDim(255) --Full brightness
	rgb:setDim(5) --Low brightness

	--White mode
	rgb:command("rgb", 0x1000000 + 6500, "RGB.lua") --White 6500K
	rgb:command("rgb", 0x1000000 + 3000, "RGB.lua") --White 3000K
	rgb.setWhite() -- switch to white mode
	rgb.setWhite(6500) -- switch to white mode, 6500K
	rgb.setWhite(3500, 255/2 ) -- switch to white mode, 3500K, half brightness
	
	--RGB mode
	rgb:command("rgb", 0xFF0000, "RGB.lua") --Red
	rgb:command("rgb", 0x00FF00) --Green
	rgb:command("rgb", 0x0000FF, "RGB.lua") --Blue'
	rgb:setRgb( 0xFF, 0, 0 ) -- Red
	rgb:setRgb( 0, 255, 0 , 255/2 ) -- Green, half brightness
	
	--Effects
	rgb:command("rgb", 0x2000000 + 0, "RGB.lua") --No effect
	rgb:command("rgb", 0x2000000 + 1, "RGB.lua") --meteor shower
	rgb:command("rgb", 0x2000000 + 2, "RGB.lua") --gradual change
	rgb:command("rgb", 0x2000000 + 3, "RGB.lua") --breath
	rgb:command("rgb", 0x2000000 + 4, "RGB.lua") --flash
	rgb:command("rgb", 0x2000000 + 5, "RGB.lua") --on/off gradual
	rgb:command("rgb", 0x2000000 + 6, "RGB.lua") --red/green flash
	rgb:setEffect(0) --No effect
	rgb:setEffect(6) --red/green flash
end 
```
