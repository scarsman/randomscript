#!/bin/bash

#send email alert when mysql goes down and 5 attempts of restart
#run this via cron job
#sendemail package in ubuntu https://tecadmin.net/send-email-from-gmail-smtp-via-linux-command/#
#sendEmail in centos http://blog.ahughes.org/?p=751

timeToday=$(date)
today=`date +%Y-%m-%d`
service="mariadb"
service_status=`systemctl status $service.service |  grep -q -w 'inactive\|failed' && echo 'inactive' || echo 'active'`


if [ $service_status == 'inactive' ]; then

		if [ ! -e /tmp/attempt-$today ]; then
			echo "0" > /tmp/attempt-$today
		fi

		getTotal="$(cat /tmp/attempt-$today)"
		sum="$((getTotal + 1))"
		echo "Total failed attempt: " $sum
		echo $sum > /tmp/attempt-$today
		
    total="$(cat /tmp/attempt-$today)"

		if [  $total -gt 5 ]; then
			#send email
                        echo "Send last 30 lines of logs from file"
                        tail -n 30 /tmp/$service-$today.log > /tmp/sentToEmail.log
                        echo -e "$service status: $service_status\nMore than 5 attempts to restart the $service service.\n\nAdditional info: \n\n $(cat /tmp/sentToEmail.log)" > /tmp/sentToEmail.log
                        /usr/local/bin/sendEmail -f "sender@gmail.com" -u "Alert: Mysql-Error from [$HOSTNAME] needs attention" -t "receiver@doamin.com" -cc="anotherreceiver@domain.com" -s "smtp.gmail.com:587" -o tls=yes -xu "sender@gmail.com" -xp "password" -o message-file="/tmp/sentToEmail.log" > /dev/null
                        
                        exit 1

		fi 

        echo "" >> /tmp/$service-$today.log
        echo "-----------------------------------------------------" >> /tmp/$service-$today.log
        echo "Date: $timeToday" >> /tmp/$service-$today.log
        echo "-----------------------------------------------------" >> /tmp/$service-$today.log
        echo " Mariadb was stop. Restarting the mariadb." >>/tmp/$service-$today.log
        echo "Last 30 lines of logs return from mariadb" >> /tmp/$service-$today.log
        echo "" >> /tmp/$service-$today.log
        echo "" >> /tmp/$service-$today.log
        journalctl -u $service | tail -n 30 >> /tmp/$service-$today.log
        systemctl start $service.service
        service_status_now=`systemctl status $service.service |  grep -q -w 'inactive\|failed' && echo 'inactive' || echo 'active'` 
        echo "" >> /tmp/$service-$today.log
        echo "Mariadb status now: $service_status_now" >> /tmp/$service-$today.log

fi
