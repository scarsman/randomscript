import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from email.header import Header

SMTP_HOST = "mail2.cba.pl"
SMTP_PORT = 587
SMTP_USER = "pol@polperpo.cba.pl"
SMTP_USER_PASSWORD = "abcd512ddf34E"
LOCAL_USER="pol@mail.hosstingcloud.party"

msg = MIMEMultipart('alternative')
msg['From'] = formataddr((str(Header('Pol', 'utf-8')), SMTP_USER))
msg['To'] = LOCAL_USER

msg['Subject'] = "Hello Pol"
server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
server.starttls()
server.login(SMTP_USER, SMTP_USER_PASSWORD)
message = "I'm running a test to check dovecot mailbox. Please let me know."
msg.attach(MIMEText(message, 'plain'))
server.sendmail(msg['From'], msg['To'], msg.as_string())
server.quit()
