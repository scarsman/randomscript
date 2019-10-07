import socket
import time
import os
import time
import sys

import random
from pathlib import Path

from subprocess import Popen, PIPE
import subprocess

import win32serviceutil
import servicemanager
import win32event
import win32service

import logging, operator, datetime
from threading import Thread, Event, Lock


LOG_FILE = "C:\\ipfss.log"
logging.basicConfig(filename=LOG_FILE,level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


class SCLUpdaterWinService(win32serviceutil.ServiceFramework):

	_svc_name_ = 'SCLInstUpdater'
	_svc_display_name_ = 'Installer-Updater Service'
	_svc_description_ = 'SCL Updater Service'

	def __init__(self, *args):
		win32serviceutil.ServiceFramework.__init__(self, *args)
		self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
		self.is_running = True
		socket.setdefaulttimeout(60)

	@classmethod
	def parse_command_line(cls):
		win32serviceutil.HandleCommandLine(cls)

	def SvcStop(self):

		self.is_running = False
		#remove service lock file
		os.remove(os.path.join(os.getcwd(), "service-updater.lock"))
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.hWaitStop)


	def SvcDoRun(self):

		#self_path = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
		self_path = os.path.dirname(sys.executable)

		log.info(self_path)

		self.is_running = True
		servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
		self.main(self_path)

	def main(self, app_path):

		updater_exe = os.path.join(app_path , "inst_updater.exe")

		while self.is_running:

			if not os.path.exists(os.path.join(os.getcwd(), "service-updater.lock")):
				#create a lock file
				open(os.path.join(os.getcwd(), "service-updater.lock"), "w").close()

				#invoked updater and run every 6 hours
				task = Task("scl_updater", datetime.datetime.now(), every_x_mins(360), RunUntilSuccess(run_updater,updater_exe,app_path, num_tries=2))
				scheduler = Scheduler()
				receipt = scheduler.schedule_task(task)
				scheduler.start()

			time.sleep(5)


def run_updater(args):
	updater_exe = args[0]
	app_path = args[1]
	cmd = "%s runas_service %s" % (updater_exe, app_path)
	cmd = cmd.split(" ")

	env_vars=os.environ.copy()
	si = subprocess.STARTUPINFO()
	si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	proc = Popen(cmd, env=env_vars, startupinfo=si, stdin=PIPE, stdout=PIPE, stderr=PIPE)
	stdout, stderr = proc.communicate()

	print(stdout)

	return stdout, stderr

class Task(object):
    def __init__(self, name, start_time, calc_next_time, func):
        self.name = name
        self.start_time = start_time
        self.scheduled_time = start_time
        self.calc_next_time = calc_next_time
        self.func = func
        self.halt_flag = Event()

    def run(self):
        print("Running %s task, scheduled at: %s" % (self.name, self.scheduled_time,))
        if not self.halt_flag.isSet():
            try:
                try:
                    self.func()
                except:
                    raise
            finally:
                self.scheduled_time = self.calc_next_time(self.scheduled_time)
                print("Scheduled next run of %s for: %s" % (self.name, self.scheduled_time,))

    def halt(self):
        self.halt_flag.set()

class Scheduler(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.tasks = {}
        self.tasks_lock = Lock()
        self.halt_flag = Event()

    def schedule(self, name, start_time, calc_next_time, func):
        task = Task(name, start_time, calc_next_time, func)
        receipt = self.schedule_task(task)
        return receipt

    def schedule_task(self, task):
        receipt = random.random()
        self.tasks_lock.acquire()
        self.tasks[receipt] = task
        self.tasks_lock.release()

        return receipt

    def drop(self, task_receipt):

        self.tasks_lock.acquire()

        try:
            print(self.tasks)
            self.tasks[task_receipt].halt()
            del self.tasks[task_receipt]
        except KeyError:
            print('Invalid task receipt: %s' % (task_receipt,))

        self.tasks_lock.release()

    def halt(self):
        self.halt_flag.set()
        map(Task.halt, self.tasks.iteritems())

    def __find_next_task(self):

        self.tasks_lock.acquire()

        items = self.tasks.items()
        by_time = lambda x: operator.getitem(x, 1).scheduled_time

        sorted(items, key=by_time)
        items = list(items)

        print("items >>  %s " % items)

        receipt = items[0][0]
        print("receipt >> %s" % receipt)
        self.tasks_lock.release()

        return receipt

    def run(self):
        while 1:
            receipt = self.__find_next_task()
            task_time = self.tasks[receipt].scheduled_time
            time_to_wait = task_time - datetime.datetime.now()
            secs_to_wait = 0.
            # Check if time to wait is in the future
            if time_to_wait > datetime.timedelta():
                secs_to_wait = time_to_wait.seconds

            print("Next task is %s in %s seconds" % (self.tasks[receipt].name, time_to_wait))

            self.halt_flag.wait(secs_to_wait)
            try:
                try:
                    self.tasks_lock.acquire()
                    task = self.tasks[receipt]
                    print("task is %s " % task)
                    print("Running %s..." % (task.name,))
                    task.run()
                finally:
                    self.tasks_lock.release()
            except Exception as e:
                logging.exception(e)

def every_x_secs(x):
    return lambda last: last + datetime.timedelta(seconds=x)

def every_x_mins(x):
    return lambda last: last + datetime.timedelta(minutes=x)

def daily_at(time):
    return lambda last: datetime.datetime.combine(last + datetime.timedelta(days=1), time)

class RunUntilSuccess(object):
    def __init__(self, func, *args, num_tries=10):
        self.func = func
        self.num_tries = num_tries
        self.args = args

    def __call__(self):

        try_count = 0
        is_success = False

        while not is_success and try_count < self.num_tries:
            try_count += 1
            try:
                if self.args:
                    self.func(self.args)
                else:
                    self.func()

                is_success = True
            except Exception as e:  # Some exception occurred, try again
                logging.exception(e)
                logging.error("Task failed on try #%s" % (try_count,))
                continue

        if is_success:
            logging.info("Task %s was run successfully." % (self.func.__name__,))
        else:
            logging.error("Success was not achieved!")
if __name__ == '__main__':

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SCLUpdaterWinService)
        servicemanager.StartServiceCtrlDispatcher()

    else:
        SCLUpdaterWinService.parse_command_line()

#dist\SCLUpdaterWinService.exe install
#dist\SCLUpdaterWinService.exe --startup auto update
#dist\SCLUpdaterWinService.exe start
#pyinstaller --onefile myupdater.py --hidden-import win32timezone --clean
