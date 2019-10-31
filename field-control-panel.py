from threading import Thread
from time import sleep
import scheduler
import panel_web_app
import vedirect_interface

t1 = Thread(target=panel_web_app.run_server, args=(panel_web_app.run_web_app(),))
t2 = Thread(target=scheduler.loop_scheduler)
t3 = Thread(target=vedirect_interface.mppt_loop)
t1.start()
t2.start()
t3.start()
