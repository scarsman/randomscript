#!/bin/bash
BACKUPDIR=/backupdir
DBNAME=dbname
DBUSER=dbuser
DBPASSWORD=dbpass

logfile=$BACKUPDIR/backup.log
cur_datetime=$(date)
time_start=$(date +%s.%N)

echo "[$cur_datetime] [INFO] Start the backup $DBNAME database ... " >> $logfile

/usr/bin/mysqldump -u $DBUSER --password=$DBPASSWORD --single-transaction $DBNAME > $BACKUPDIR/`date +\%Y\%m\%d`.$DBNAME-backup.sql
#/usr/bin/mysqldump -u $DBUSER --password=$DBPASSWORD  $DBNAME > $BACKUPDIR/$TODAY.$DBNAME-backup.sql

time_end=$(date +%s.%N)
runtime=$(python -c "print(${time_end} - ${time_start})")

echo "[$cur_datetime] [INFO] Done the backup, it took around $runtime seconds to complete the backup.." >> $logfile

#deleting seven days sql backup

sevendays_ago=`date -d '7 days ago' +\%Y\%m\%d`

for file in `ls $BACKUPDIR/ | grep -E "[0-9]"`
do
        filename=`basename "$file" | sed 's/[^0-9]*//g'`
        if (( `expr $filename` <= `expr $sevendays_ago` )); then
           echo "[$cur_datetime] [INFO] Deleting $file, more than 7 days due" >> $logfile
           rm -rf $BACKUPDIR/$file
           echo "[$cur_datetime] [INFO] Done .." >> $logfile
        fi
done
