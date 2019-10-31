from threading import 
import scheduler
import panel_web_app

def start_worker(self,worker):
    def forever():
        while True:
            try:
                return worker()
            except Exception as e:
                print(e)
                print('Failure of worker %s. Restarting.',worker.__name__)
                sleep(1)

    t = Thread()
    t = Thread(target=forever)
    t.daemon = True
    t.start()
    return t

start_worker(panel_web_app.run_web_app)
start_worker(scheduler.loop_scheduler)