#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json
import operator
import pprint
import csv
import datetime
import time

from types import *

from collections import OrderedDict

X_USERNAME = 'username'
X_PASSWORD = 'pass'
X_ACCOUNT_CODE = 'accountcode'
ONGAGE_URL_API = 'https://api.ongage.net/api/reports/query'


def get_ongage_data(start_date, end_date):

    headers = {'X_USERNAME': X_USERNAME, 'X_PASSWORD': X_PASSWORD,
               'X_ACCOUNT_CODE': X_ACCOUNT_CODE}

    payload = {
        'list_ids': ['45633', '46064', '46065', '46066', '47655'],
        'select': [
            ['MAX(`stats_date`)', 'stats_date'],
            'isp_name',
            'type',
            'mailing_name',
            'event_name',
            'sum(`sent`)',
            'sum(`success`)',
            'sum(`failed`)',
            'sum(`opens`)',
            'sum(`unique_opens`)',
            'sum(`clicks`)',
            'sum(`unique_clicks`)',
            ],
        'from': 'mailing',
        'group': ['mailing_id', ['stats_date', 'day'], 'isp_id',
                  'event_id', 'list_id'],
        'order': [['delivery_timestamp', 'desc']],
        'filter': [['is_test_campaign', '=', 0], ['stats_date', '>=',
                   start_date], ['stats_date', '<=', end_date]],
        'calculate_rates': True,
        }

    r = requests.post(ONGAGE_URL_API, data=json.dumps(payload), headers=headers)

    raw_data = r.json()

    return raw_data['payload']


def process_ongage_data(start_date, end_date):

    temp_results = []

    for data in get_ongage_data(start_date, end_date):

        temp = OrderedDict()

        mailing_name = data['mailing_name']  # get transactional campaign result
        transactional = 'default transactional'

        if transactional in mailing_name:

            # print "-----------------------------------------------"....
            # for k,v in data.items():
                # print("%s: %s") % (k,v)

            # get only gmail and yahoo
            email_client = ['yahoo.com', 'gmail.com']

            if data['isp_name'] in email_client:

                temp['isp_mailing_name'] = mailing_name.replace('default transactional', '').strip()
                temp['isp_name'] = data['isp_name']
                temp['send'] = data['sent']
                temp['success'] = data['success_percent'].replace("%","")
                temp['failed'] = data['failed_percent'].replace("%","")
                temp['opens'] = data['opens_percent'].replace("%","")
                temp['uniq_opens'] = data['unique_opens_percent'].replace("%","")
                temp['clicks'] = data['clicks_percent'].replace("%","")
                temp['uniq_clicks'] = data['unique_clicks_percent'].replace("%","")

                # convert epoch to gmt time

                format_date = time.strftime('%Y-%m-%d',
                        time.gmtime(float(data['stats_date'])))

                # subtract 1 day to reflect the ongage server time/depend in your timezone. PH is ahead 1 day 

                format_date = datetime.datetime.strptime(format_date,
                        '%Y-%m-%d') - datetime.timedelta(days=1)
                temp['date'] = format_date.strftime('%Y-%m-%d')

                temp_results.append(temp)

    """sort according to isp_mailing_name"""
    temp_results.sort(key=operator.itemgetter('date','isp_mailing_name',
                      'isp_name'))             


     """rewrite and regroup the json based on date as key"""
    results = {}

    for result in temp_results:

        # key = result['isp_mailing_name']
        # key = key.strip()
        # regroup by isp_mailing_name as key
        # if key not in results.keys():
        # ....results[date] = []

        date = result['date']
        
        # regroup by `date` as key    
        if date not in results.keys():
            results[date] = []
           
            
            
        # delete the key we provide............
        # del result["isp_mailing_name"]........
        
	#remove the date duplication
        del result['date']
        
        sorted(results[date])
        
        results[date].append(result)

    return results


if __name__ == '__main__':

    # subtract 1 day to get the correct results, because today the ongage reporting is ongoing 
    date_today = datetime.datetime.now() - datetime.timedelta(1)
    date_today = date_today.strftime('%Y-%m-%d')
    start_date = '2018-01-01'
    
    raw_json = process_ongage_data(start_date, date_today)
    json_string = json.dumps(raw_json, indent=4)
    json_data = json_string.replace("%","")
    
    print "--JSON RESULT with pretty format----"
	
    print json_data


    """transform json to csv"""
        
    #data =  json.loads(json_data)

    csv_file = open('temp.csv', 'w')

    csvwriter = csv.writer(csv_file)

    count = 0
  
    raw_data = raw_json.items()
    
    for (key, val) in raw_data:

        new_date_val = {}  
        #key as the first column values 
        for item in val:
            
            new_date_val["date"] = key
            
            
            
            if count == 0:
               
                headers = item.keys()
                
                headers.insert(0, "date")
                
                headers = [x.upper() for x in headers]

                csvwriter.writerow(headers)
               
                count +=1
            
            joined_list = new_date_val.values() + item.values()
            
            
            csvwriter.writerow(joined_list)
        
        #add space/new line to looks good    
        csvwriter.writerow([])
        

    csv_file.close()

    fields = []
    
    """manipulate the csv data """
    
    #sort the csv file by date for cleanup
    
    with open('temp.csv') as temp:
        
        csv_reader = csv.reader(temp)
        #reserved the header fields
        fields = csv_reader.next()
        
        sortedlist = sorted(csv_reader)
        
        with open("sorted.csv", "wb") as f:
            
            headers = [field for field in fields]
            file_writer = csv.writer(f, delimiter=',')
            file_writer.writerow(headers)
           
            for row in sortedlist:
                
                if any(row): #delete the empty cell from current csv file


                    file_writer.writerow(row)
