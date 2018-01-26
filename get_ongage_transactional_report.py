#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import json
import operator
import pprint
import csv
import datetime
import time


from collections import OrderedDict


X_USERNAME = ''
X_PASSWORD = ''
X_ACCOUNT_CODE = ''
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
            email_client = ['yahoo.com', 'gmail.com',"others"]

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

                # subtract 1 day to reflect the ongage server time

                format_date = datetime.datetime.strptime(format_date,
                        '%Y-%m-%d') - datetime.timedelta(days=1)
                temp['date'] = format_date.strftime('%Y-%m-%d')

                temp_results.append(temp)

    # sort according to domain................
    temp_results.sort(key=operator.itemgetter('date','isp_mailing_name',
                      'isp_name'))             


    # rewrite to regroup based on date

    results = {}

    for result in temp_results:

        # key = result['isp_mailing_name']
        # key = key.strip()
        # regroup by domain as key
        # if key not in results.keys():
        # ....results[date] = []

        date = result['date']
        
        # regroup by `date` as key    
        if date not in results.keys():
            results[date] = []
           
            
            
        # delete the key we provide............
        # del result["isp_mailing_name"]........
        
        del result['date']
        
        sorted(results[date])
        
        results[date].append(result)

    return results


if __name__ == '__main__':

    # subtract 1 day to get the correct results, because today the ongage reporting is ongoing 
    date_today = datetime.datetime.now() - datetime.timedelta(1)
    date_today = date_today.strftime('%Y-%m-%d')
    start_date = '2018-01-22'
    raw_json = process_ongage_data(start_date, date_today)
    json_string = json.dumps(raw_json, indent=4)
    json_data = json_string.replace("%","")
    
    raw_data = raw_json.items()
    
    print "--JSON RESULT----"
    print json_data
    
    
    
    """
        * Proof of concept json to csv manipulation
        * transform json to csv
    """

    csv_file = open('temp.csv', 'w')
    csvwriter = csv.writer(csv_file)

    count = 0

    i = 0
    
    for (key, val) in raw_data:
        new_date = {}
        #key as the first column values 
        for item in val:
            new_date['date'] = key
            if count == 0:
               
                headers = item.keys()
                
                headers.insert(0, "date")
                
                headers = [x.upper() for x in headers]

                csvwriter.writerow(headers)
                
                count +=1
                
            joined_list =  new_date.values() + item.values()
            
            i += 1    
            
            csvwriter.writerow(joined_list)
        
        #add space/new line to looks good    
        #csvwriter.writerow([])
        
    csv_file.close()

    "cleaning the csv above"

    fields = []

    duplicate_date = []

    index = 0

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
                if any(row): #remove empty row
                    if row[0] not in duplicate_date:
                        duplicate_date.append(row[0])
                    else:
                        duplicate_date.append("")
                    

                    row[0] = duplicate_date[index]

                    if row[2] != "gmail.com":
                        row[1] = ""
                    print "-----------------------------"    
                    print "Adding row %s data to csv file" % index    
                    print "-----------------------------"
                    print row
                    print "\n"
                    
                    file_writer.writerow(row) 
                    
                    index += 1                    
        
