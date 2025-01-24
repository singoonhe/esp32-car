# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

from machine import Pin
# 使用指定引脚的电平来判断是否上传模式
upload_pin = Pin(7, Pin.IN, Pin.PULL_UP)
if upload_pin.value() == 1:
    import main_c3
    main_c3.run_main()
else:
    # 上传代码模式，不自启动
    pass