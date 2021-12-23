# Nii Golightly
import robin_stocks.robinhood as r 
import os 
from pathlib import Path
import toml
import subprocess


class bcolor:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
robinhood_config = toml.load(Path().absolute()/'robinhood_config.toml')

class load_config:
	def __init__(self, broker_file = robinhood_config):
		self.broker_file = broker_file
		self.prefered_config = broker_file['disable_multiStonk']
		self.robinhood_account = self.broker_file['robinhood_login']
		self._broker_config = self.broker_file['use_broker']
		self.limit_order = self.broker_file['order_limit']
		# self.news_source = self.broker_file['news_sources']
		# self.buy_list = self.broker_file['file_locations']['buyList']
		# self.news_file = self.broker_file['file_locations']['news_file']
		# self.mongodb_url = self.broker_file['database_settings']['mongodb_url']
		


class robinhoodConfig(load_config):
	def robinhood_credentials(self):
		try:				
			user_account = self.robinhood_account
			return user_account
		except Exception as e:  
			print("file: issues from function robinhood_credentials",e)
			return None
	
		
