import os
from subprocess import Popen, PIPE
import subprocess
import simplejson as json
import platform
import shlex
import requests

import sys
import zipfile
import shutil
import time

import logging
from logging.handlers import TimedRotatingFileHandler

import psutil

IPFS_CONFIG_FILE = "config"
WIN_IPFS_64_BIT =  "https://dist.ipfs.io/go-ipfs/v0.4.18/go-ipfs_v0.4.18_windows-amd64.zip"
WIN_IPFS_32_BIT = "https://dist.ipfs.io/go-ipfs/v0.4.18/go-ipfs_v0.4.18_windows-386.zip"
WINSW_EXE = "https://raw.githubusercontent.com/scarsman/advance-installer/master/WinSW.NET4.exe"
IPFS_SERVICE_XML = "ipfs_service.xml"
IPFS_SERVICE_EXE = "ipfs_service.exe"
IPFS_SERVICE_NAME = "Ipfs Service"

IPFS_SWARM_PORT = 40405
IPFS_API_PORT = 40505 
IPFS_GATEWAY_PORT = 40805

FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_DIR  = os.path.join(os.getcwd(), "log")
LOG_FILE = "ipfs.log"

if not os.path.exists(LOG_DIR):
	os.makedirs(LOG_DIR)

def get_console_handler():
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(FORMATTER)
	return console_handler

def get_file_handler(log_path):
	file_handler = TimedRotatingFileHandler(log_path, when='midnight')
	file_handler.setFormatter(FORMATTER)
	return file_handler

def get_logger(logger_name, log_path):
	logger = logging.getLogger(logger_name)

	logger.setLevel(logging.DEBUG) # better to have too much log than not enough

	logger.addHandler(get_console_handler())
	logger.addHandler(get_file_handler(log_path))
	
	logger.propagate = False

	return logger
	
log = get_logger("ipfs-setup", os.path.join(LOG_DIR, LOG_FILE))

class IPFSServer:
	
	def __init__(self, param_dir, param_swarm_port, param_api_port, param_gateway_port, ipfs_dest):
		
		self.target_dir = param_dir
		self.swarm_port = param_swarm_port
		self.api_port = param_api_port
		self.gateway_port = param_gateway_port
		self.ipfs_dest = ipfs_dest 

	def download_file(self,file_path,url): #download the ipfs zip file, service wrapper

		with requests.get(url, stream=True) as r:
			with open(file_path, 'wb') as f:
				for chunk in r.iter_content(chunk_size=8192): 
					if chunk: # filter out keep-alive new chunks
						f.write(chunk)
						f.flush()
	
	def unzipping(self, zip_source, destination):
		
		log.debug("> Unzipping %s into this destination %s " % (zip_source, destination))

		base_filename = os.path.basename(zip_source)
		
		if base_filename.find(".zip") < 0:
			log.debug("> Error no zip file given.")
			sys.exit(1)

		if not os.path.exists(zip_source):
			log.debug("> Error zip path not exist")
			sys.exit(1)
			
		source_temp_dir = os.path.expanduser("~")

		with zipfile.ZipFile(zip_source, "r") as zip_ref:
			
			members = zip_ref.namelist()
			#print(members)
			
			with open(os.path.join(source_temp_dir, "ipfs.exe"), 'wb') as f: #extract only one file
				f.write(zip_ref.read('go-ipfs/ipfs.exe'))
		
		source = os.path.join(source_temp_dir, "ipfs.exe")
		
		log.debug("> Copying %s to %s" %(source, destination))
		
		shutil.copy(source, destination)
	
	def get_ipfs_and_extract(self, ipfs_url=WIN_IPFS_32_BIT):
		
		if self.is_64_bit:
			ipfs_url = WIN_IPFS_64_BIT
		
		filename = ipfs_url.split("/")[-1]
		ipfs_zip_path = os.path.join(self.ipfs_dest, filename)
		
		if not os.path.exists(ipfs_zip_path):
			#download
			log.debug("> Downloading %s " %ipfs_url)
			self.download_file(ipfs_zip_path, ipfs_url)
			log.debug(".. Done")
		#extract	zip file
		log.debug("> Extracting %s" % ipfs_zip_path)
		self.unzipping(ipfs_zip_path, self.ipfs_dest)
		log.debug(".. Done")

	def get_winsw_exe(self):
		filename = WINSW_EXE.split("/")[-1] #original filename
		filename = IPFS_SERVICE_EXE #rename
		win_exe_path = os.path.join(self.ipfs_dest, filename) 
		
		if not os.path.exists(win_exe_path):
			log.debug("> Downloading %s " % WINSW_EXE)
			self.download_file(win_exe_path, WINSW_EXE)
			log.debug(".. Done")

	def uninstall_ipfs_existing_service(self):
		
		env_vars = os.environ.copy()
		env_vars["IPFS_PATH"] = self.target_dir
		si = subprocess.STARTUPINFO()
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		
		ipfs_service = os.path.join(self.ipfs_dest, IPFS_SERVICE_EXE)
		
		log.debug("> Uninstall %s if already installed." % IPFS_SERVICE_NAME)
		
		try:
			service = psutil.win_service_get(IPFS_SERVICE_NAME)
			
			_ipfs = service.as_dict()
			
			if _ipfs["status"] == "running": # stop it
				
				log.debug("> Service `%s` already running. Stopping" % IPFS_SERVICE_NAME)
				
				cmd_stop = "%s stop" % ipfs_service
				cmd_tokens_stop = cmd_stop.split(" ")
				pid = Popen(cmd_tokens_stop, cwd=self.ipfs_dest, env=env_vars, startupinfo=si, stdin=PIPE, stdout=PIPE, stderr=PIPE)
				
				log.debug(".. Done")
				time.sleep(5) #to finished the process
				
				log.debug("> Uninstalling the service `%s` " % IPFS_SERVICE_NAME)
				
				cmd_uninstall = "%s uninstall" % ipfs_service
				cmd_tokens_uninstall = cmd_uninstall.split(" ")
				pid = Popen(cmd_tokens_uninstall, cwd=self.ipfs_dest, env=env_vars, startupinfo=si, stdin=PIPE, stdout=PIPE, stderr=PIPE)		
				
				log.debug(".. Done")
				
			else: #if stop uninstall it
				log.debug("> Service `%s` is stop. Uninstalling the service" % IPFS_SERVICE_NAME)
				cmd_uninstall = "%s uninstall" % ipfs_service
				cmd_tokens_uninstall = cmd_uninstall.split(" ")
				pid = Popen(cmd_tokens_uninstall, cwd=self.ipfs_dest, env=env_vars, startupinfo=si, stdin=PIPE, stdout=PIPE, stderr=PIPE)					

				log.debug(".. Done")
				time.sleep(5) #to finished the process
				
		except Exception as e: # no service installed
			if e is not None:
				log.debug(".. %s" % e)
				#print("Will retry when running the service")
			pass
			
	def run_ipfs_service(self):
		
		self.uninstall_ipfs_existing_service()
		
		env_vars = os.environ.copy()
		env_vars["IPFS_PATH"] = self.target_dir
		
		ipfs_service = os.path.join(self.ipfs_dest, IPFS_SERVICE_EXE)
		
		si = subprocess.STARTUPINFO()
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		
		#install the service
		log.debug("> Installing `%s` service " % IPFS_SERVICE_NAME)
		cmd_install = "%s install" % ipfs_service
		cmd_tokens_install = cmd_install.split(" ")
		pid = Popen(cmd_tokens_install, cwd=self.ipfs_dest, env=env_vars, startupinfo=si, stdin=PIPE, stdout=PIPE, stderr=PIPE)
		log.debug(".. Done")
		time.sleep(5) # to fully initiliaze
		
		#start the service
		log.debug("> Starting `%s` service " % IPFS_SERVICE_NAME)
		cmd_start = "%s start" %ipfs_service
		cmd_tokens_start = cmd_start.split(" ")
		pid = Popen(cmd_tokens_start,cwd=self.ipfs_dest, env=env_vars, startupinfo=si, stdin=PIPE, stdout=PIPE, stderr=PIPE)
		log.debug(".. Done")
		log.debug("You can access now via http://localhost:%s/webui ." % IPFS_API_PORT)
		
	def is_64_bit(self):
		return platform.machine().endswith('64')
	
	def setup(self):
		log.debug("-- Setup IPFS")
		self.uninstall_ipfs_existing_service()
		self.ipfs_server_setup()
		self.ipfs_service_setup()
			
	def ipfs_server_setup(self):
		
		#download ipfs and extract
		self.get_ipfs_and_extract()
		
		env_vars = os.environ.copy()
		env_vars["IPFS_PATH"] = self.target_dir
		si = subprocess.STARTUPINFO()
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		
		# init the repo
		config_file = os.path.join(self.target_dir,IPFS_CONFIG_FILE)
		
		if not os.path.exists(config_file):
			
			log.debug("INITIALIZING IPFS REPO: %s" % self.target_dir)			
			ipfs = os.path.join(self.ipfs_dest,"ipfs.exe") #c:\programfiles\scl\sclexpress\ipfs\ipfs.exe
			cmd = "%s init" %ipfs
			cmd_tokens = cmd.split(" ")
			shell = Popen(cmd_tokens, cwd=self.target_dir, env=env_vars, stdin=PIPE, stdout=PIPE,stderr=PIPE)
			shell.communicate()
			
		# reconfigure the configuration
		
		config_data = {}
		
		with open(config_file) as f:
			config_data = json.loads(f.read())
			
		swarm_addresses = config_data["Addresses"]["Swarm"]
		api_address = config_data["Addresses"]["API"]
		gateway_address = config_data["Addresses"]["Gateway"]
		
		
		# modify swarm_addresses
		swarm_port = swarm_addresses[0].split("/")[-1]
		modified_swarm_addresses = []
		for sa in swarm_addresses:
			temp_sa = sa.replace(swarm_port,str(self.swarm_port))
			modified_swarm_addresses.append(temp_sa)
		
		config_data["Addresses"]["Swarm"] = modified_swarm_addresses

		# modify api_address		
		api_port = api_address.split("/")[-1]
		api_address = api_address.replace(api_port,str(self.api_port))
		
		config_data["Addresses"]["API"] = api_address
		
		# modify api_address		
		gateway_port = gateway_address.split("/")[-1]
		gateway_address = gateway_address.replace(gateway_port,str(self.gateway_port))
		
		config_data["Addresses"]["Gateway"] = gateway_address
		
		
		config_data["API"]["HTTPHeaders"]["Access-Control-Allow-Credentials"] = ["true"]
		config_data["API"]["HTTPHeaders"]["Access-Control-Allow-Methods"] = ["PUT", "GET", "POST"]
		config_data["API"]["HTTPHeaders"]["Access-Control-Allow-Origin"] = []
		config_data["API"]["HTTPHeaders"]["Access-Control-Allow-Origin"].append("http://127.0.0.1:%s" % self.api_port)
		config_data["API"]["HTTPHeaders"]["Access-Control-Allow-Origin"].append("https://webui.ipfs.io")
		
		with open(config_file,"w") as f:
			config_str = json.dumps(config_data)
			f.write(config_str)

	def ipfs_service_setup(self):
		
		#download winsw and create service xml
		self.get_winsw_exe()
		
		ipfs_xml = '''
		<configuration>
		<id>%s</id>
		<name>IFPS SERVICE</name>
			<env name="IPFS_PATH" value="%s" />
		<description>IPFS daemon run as a service</description>
		<executable>%s\ipfs.exe</executable>
		<arguments>daemon</arguments>
		</configuration>''' %(IPFS_SERVICE_NAME, self.target_dir, self.ipfs_dest)
		
		if os.path.exists(os.path.join(self.ipfs_dest, IPFS_SERVICE_XML)):
			os.remove(os.path.join(self.ipfs_dest, IPFS_SERVICE_XML))
			
		with open(os.path.join(self.ipfs_dest, IPFS_SERVICE_XML),"w") as f:
			f.write(ipfs_xml)		
			
if __name__ == "__main__":
	
	ipfs_repo = os.path.join(os.environ['LOCALAPPDATA'],"ipfs") #ipfs repo
	ipfs_dest = os.path.join(os.getcwd(), "ipfs") # extracted directory

	if 	not os.path.exists(ipfs_repo):
		os.makedirs(ipfs_repo)
		
	if 	not os.path.exists(ipfs_dest):
		os.makedirs(ipfs_dest)
	
	i = IPFSServer(ipfs_repo, IPFS_SWARM_PORT, IPFS_API_PORT, IPFS_GATEWAY_PORT, ipfs_dest)
	
	i.setup()
	i.run_ipfs_service()
	
	#packaging
	# pyinstaller thisfile.py --onefile --noconsole
