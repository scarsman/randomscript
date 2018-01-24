import requests
import json

import operator
import itertools
import pprint
import csv
import datetime
import time


from collections import OrderedDict


X_USERNAME = "username"
X_PASSWORD = "pass"
X_ACCOUNT_CODE = "accountcode"
ONGAGE_URL_API = "https://api.ongage.net/api/reports/query"


def get_ongage_data(start_date,end_date):
	
	headers = {
				'X_USERNAME': X_USERNAME, 
				'X_PASSWORD': X_PASSWORD,
				'X_ACCOUNT_CODE': X_ACCOUNT_CODE
			}
		
	payload = {"list_ids":["45633","46064","46065","46066","47655"],
				"select":[
					["MAX(`stats_date`)","stats_date"],
					"isp_name",
					"type",
					"mailing_name",
					"event_name",
					"sum(`sent`)",
					"sum(`success`)",
					"sum(`failed`)",
					"sum(`opens`)",
					"sum(`unique_opens`)",
					"sum(`clicks`)",
					"sum(`unique_clicks`)",
				],
				"from":"mailing",
				"group":[
					"mailing_id",["stats_date","day"],
					"isp_id",
					"event_id",
					"list_id"
				],
				"order":[["delivery_timestamp","desc"]],
				"filter":[
					["is_test_campaign","=",0],
					["stats_date",">=", start_date],
					["stats_date","<=", end_date]
				],"calculate_rates": True
			}

	r = requests.post(ONGAGE_URL_API, data=json.dumps(payload), headers=headers)

	raw_data = r.json()

	return raw_data['payload']


def process_ongage_data(start_date, end_date):
	
	
	temp_results = []
	
	for data in get_ongage_data(start_date, end_date):

		temp = OrderedDict()
		
		
		mailing_name = data["mailing_name"] #get transactional campaign result
		transactional = 'default transactional'
		
		
		if transactional in mailing_name:
			
		
			#print "-----------------------------------------------"	
			#for k,v in data.items():
				#print("%s: %s") % (k,v)
			
			#print only gmail and yahoo
			email_client = ["yahoo.com", "gmail.com"]
			
			if data['isp_name'] in email_client:
				
				mailing_name = mailing_name.replace("default transactional", "").strip()	
				temp['isp_mailing_name'] = mailing_name
				temp['isp_name'] = data['isp_name']
				temp['send'] = data["sent"]
				temp['success'] = data["success_percent"]
				temp['failed'] = data["failed_percent"]
				temp['opens'] = data["opens_percent"]
				temp['uniq_opens'] = data["unique_opens_percent"]
				temp['clicks'] = data["clicks_percent"]
				temp['uniq_clicks'] = data["unique_clicks_percent"]
				
				#convert epoch to gmt time
				format_date = time.strftime("%Y-%m-%d", time.gmtime(float(data['stats_date'])))
				#subtract 1 day to reflect the ongage server time
				format_date = datetime.datetime.strptime(format_date, "%Y-%m-%d") - datetime.timedelta(days=1)
				temp['date'] = format_date.strftime("%Y-%m-%d")
			
				temp_results.append(temp)
	
	#sort according to domain				
	temp_results.sort(key=operator.itemgetter('isp_mailing_name','isp_name'))			
	
	#rewrite to regroup based on date
	results = {}

	for result in temp_results:
		
		
		#key = result['isp_mailing_name']
		#key = key.strip()
		
		# regroup by domain as key
		#if key not in results.keys():
		#	results[date] = []
		
		date = result['date']
		
		if date not in results.keys():
			results[date] = []
		
		#delete the key we provide			
		#del result["isp_mailing_name"]		
		del result["date"]
		results[date].append(result)
		
		
	return  results

	


if __name__ == '__main__':
	
	#subtract 1 day because ongage is in different timezone
	date_today = datetime.datetime.now()	- datetime.timedelta(1)
	date_today = date_today.strftime("%Y-%m-%d")
	
	start_date = "2018-01-19"
	
	json_string = json.dumps( process_ongage_data(start_date, date_today),indent=4)
	
	print (json_string.replace("%",""))
	
	
