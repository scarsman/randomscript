#!/bin/bash
#set -x

LOGFILE=/var/log/mail.log
EMAILRECIPIENT="pol@localhost"
MAILER=/usr/bin/mail
STATUS="sent"

#send an email to test postfix sendmail
echo "test mail from postfix" | ${MAILER} -s "postfix - test mail(time)" ${EMAILRECIPIENT}

#read the logfile from bottom to top and search email recipient if it was delivered
status=$(awk '/to=<'${EMAILRECIPIENT}'>/{k=$0}END{print k}' ${LOGFILE} | grep -q "status=${STATUS}" && echo "ok" || echo "not ok")
echo "${status}"
