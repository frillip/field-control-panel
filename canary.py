import requests
from requests.auth import HTTPBasicAuth
from getpass import getpass
import time
import sys
import signal
import schedule
from datetime import datetime,timedelta
import global_vars
from yaml_config import load_config,config
from clickatell import send_sms
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger('canary')
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

run_scheduler = True


class Canary(object):
    def __init__(self, hostname, url):
        self.hostname = hostname
        self.url = url
        self.string = None
        self.alive = True
        self.interval = 5
        self.timeout = 60
        self.last_successful_request = '1970-01-01T00:00:00'
        self.last_successful_request_timestamp = 0
        self.connection_fail_count = 0
        self.stats = {'total': 0,'success': 0,'fail': 0}
        self.credentials = None


    def set_auth(self,user,password):
        self.credentials = HTTPBasicAuth(user,password)


    def set_interval(self,interval):
        self.interval = interval


    def set_timeout(self,timeout):
        self.timeout = timeout


    def set_string(self, canary_string):
        self.string = canary_string


    def test(self):
        self.stats['total'] += 1
        if self.request():
            self.stats['success'] += 1
            self.last_successful_request = datetime.now().replace(microsecond=0).isoformat()
            self.last_successful_request_timestamp = int(time.time())
            self.alive = True
            return True
        else:
            self.stats['fail'] += 1
            return False


    def request(self):
        r = requests.get(self.url,auth=self.credentials)
        if r.status_code == 200:
            if self.string and r.text != self.string and self.alive:
                    logger.error("Canary string does not match expected value!")
            else:
                return True
        elif self.alive:
            if r.status_code == 401:
                logger.error("Recieved status code " + str(r.status_code))
                logger.error("Are the basic username and password correct?")
            elif r.status_code == 500:
                logger.error("Recieved status code " + str(r.status_code))
                logger.error("Is the host behind the proxy down?")
            else:
                logger.error("Recieved status code " + str(r.status_code))
        return False


    def check(self):
        self.stats['total'] += 1
        unix_time_int = int(time.time())
        now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
        human_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')

        if not self.request():
            self.stats['fail'] += 1
            self.connection_fail_count += 1
            if self.alive and self.last_successful_request_timestamp:
                if (unix_time_int - self.last_successful_request_timestamp) > self.timeout:
                    self.alive = False
                    logger.error(self.hostname + " offline! Sending warning SMS!")
                    warn_sms_text = human_datetime + ": " + self.hostname + " has disconnected from Darksky!"
                    send_sms(config['remote']['warn_sms_list'], warn_sms_text)
                else:
                    logger.warning("Remote request to " + self.hostname + " failed!")

        else:
            self.stats['success'] += 1
            if not self.alive and self.last_successful_request_timestamp:
                disconnect_seconds = unix_time_int - self.last_successful_request_timestamp
                disconnect_time = str(timedelta(seconds=disconnect_seconds))
                logger.info(self.hostname + " back online after " + disconnect_time + " disconnected")
                self.connection_fail_count = 0
                warn_sms_text = human_datetime + ": " + self.hostname + " has reconnected to Darksky!"
                send_sms(config['remote']['warn_sms_list'], warn_sms_text)

            if self.connection_fail_count:
                logger.info("Remote request to " + self.hostname + " succeeded!")

            self.last_successful_request = now_iso_stamp
            self.last_successful_request_timestamp = unix_time_int
            self.connection_fail_count = 0
            self.alive = True


    def show_stats(self):
        if self.stats['total']:
            success_rate = round(self.stats['success'] / (self.stats['total'] * 0.01),2)
        else:
            success_rate = 0.0

        logger.info("Stats for: " + self.hostname)
        logger.info(" - Total requests:      " + str(self.stats['total']))
        logger.info(" - Failed requests:     " + str(self.stats['fail']))
        logger.info(" - Successful requests: " + str(self.stats['success']))
        logger.info(" - Success rate:        " + str(success_rate) + "%")


    def reset_stats(self):
        self.show_stats()
        self.stats['total'] = 0
        self.stats['success'] = 0
        self.stats['fail'] = 0


def main():
    logger.info("Starting remote canary monitoring")
    load_config()
    logger.info("Using hostname: " + config['remote']['hostname'])
    full_url = config['remote']['base_url'] + config['remote']['canary_url']
    logger.info("Using URL: " + full_url)
    sheepnet = Canary(config['remote']['hostname'],full_url)

    if config['remote']['basic_user']:
        if config['remote']['basic_pass']:
            sheepnet.set_auth(config['remote']['basic_user'], config['remote']['basic_pass'])
        else:
            print("Using username from config.yaml: " + config['remote']['basic_user'])
            password = getpass()
            sheepnet.set_auth(config['remote']['basic_user'], password)

    sheepnet.set_interval(config['remote']['interval'])
    sheepnet.set_timeout(config['remote']['timeout'])
    sheepnet.set_string = config['remote']['canary_string']

    if sheepnet.test():
        logger.info("Successfully detected the canary!")
        logger.info("Now monitoring " + config['remote']['hostname'])
    else:
        logger.error("Unable to detect the canary!")
        logger.warning("Exiting")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    logger.info("Setting up scheduler")
    logger.info("Starting canary checking task")
    schedule.every(config['remote']['interval']).seconds.do(sheepnet.check)
    logger.info("Starting stats task")
    schedule.every().hour.do(sheepnet.reset_stats)

    logger.info("Starting scheduler")
    while run_scheduler:
        schedule.run_pending()
        time.sleep(0.5)

    sheepnet.show_stats()
    sys.exit(0)


def signal_handler(sig, frame):
    global run_scheduler
    logger.warning("Caught CTRL-C interrupt! Stopping...")
    run_scheduler = False

if __name__ == '__main__':
    from yaml_config import load_config
    main()
