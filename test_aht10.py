import utime
from machine import Pin, SoftI2C
import ahtx0,bmp180

# I2C for the Wemos D1 Mini with ESP8266
i2c = SoftI2C(scl=Pin(3), sda=Pin(2))
# Create the sensor object using I2C
sensor = ahtx0.AHT10(i2c)

# BMP180
# bus = SoftI2C(scl=Pin(10), sda=Pin(6), freq=100000)   # on esp8266
# bmp180 = bmp180.BMP180(bus)
# bmp180.oversample_sett = 2
# bmp180.baseline = 101325

Pin(13).on()

while True:
    print("\nTemperature: %0.2f C" % sensor.temperature)
    print("Humidity: %0.2f %%" % sensor.relative_humidity)
    
#     temp = bmp180.temperature
#     p = bmp180.pressure
#     altitude = bmp180.altitude
#     print(temp, p, altitude)
    utime.sleep(5)


Pin(11).off()
while True:
    utime.sleep(5)