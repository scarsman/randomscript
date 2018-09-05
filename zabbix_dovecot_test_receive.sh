#!/bin/bash
#set -x

LOGFILE=/var/log/mail.log
LOCALUSER=pol@mail.hostingcloud.party
SENDERUSER=pol@polperpo.cba.pl
STATUS="sent"
PYTHONBIN=/usr/bin/python2.7
PYTHONFILE=/home/pol/scripts/sendemail.py


#send an email to test postfix sendmail
${PYTHONBIN} ${PYTHONFILE}
DATE=`date '+%b %e %H:%M:%S'`
sleep 3
#read the logfile from bottom to top and search email recipient if it was delivered
status=$(awk '/to=<'${LOCALUSER}'>/{k=$0}END{print k}' ${LOGFILE} | grep -q "status=${STATUS}" && echo "ok" || echo "not ok")
sender=$(awk '/from=<'${SENDERUSER}'>/{k=$0}END{print k}' ${LOGFILE} | grep "postfix/qmgr" | awk '{print $1 " " $2 " " $3}')
receiver=$(awk '/to=<'${LOCALUSER}'>/{k=$0}END{print k}' ${LOGFILE} | grep "postfix/local" | awk '{print $1 " " $2 " " $3}')

epoch_date=$(date -d "${DATE}" +"%s")
epoch_date_sender=$(date -d "${sender}" +"%s")
epoch_date_receiver=$(date -d "${receiver}" +"%s")

if [[ $epoch_date_sender -eq $epoch_date_receiver && $status == "ok" ]];then
	time_difference=$epoch_date_sender-$epoch_date
	if [[ $time_difference -lt 10 ]];then
		echo "ok"
	else
		echo "not ok"
	fi	
else
	echo "not ok"	
fi

