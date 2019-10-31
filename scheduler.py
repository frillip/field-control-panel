import time
import schedule
from megaio_get_data import get_relay_data
from e3372_interface import get_modem_data,connection_checker
from bme_env_data import get_bme_data
from environment_agency import check_river

def setup_scheduler():
	schedule.every.second.do(get_modem_data)
	schedule.every.second.do(get_bme_data)
	schedule.every.second.do(get_relay_data)
	schedule.every(5).seconds.do(connection_checker)
	schedule.every().hour.at(‘:01’).do(check_river)
	schedule.every().hour.at(‘:16’).do(check_river)
	schedule.every().hour.at(‘:31’).do(check_river)
	schedule.every().hour.at(‘:46’).do(check_river)
	pass


def loop_scheduler():
	while True:
	    schedule.run_pending()
	    time.sleep(1)
	pass # Should never get here...