from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from datetime import timedelta
from celery.schedules import crontab
from shutil import copyfile
import pyrebase,csv,json,re,glob,sys,datetime
import os, os.path
import smtplib,time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# initialize our running app
config_running_app = {
    "apiKey": "AIzaSyApHVzGEc9TYksZZV8dnKSOiIucxiEnQUU",
    "authDomain": "runningmate-7c3f2.firebaseapp.com",
    "databaseURL": "https://runningmate-7c3f2.firebaseio.com",
    "projectId": "runningmate-7c3f2",
    "storageBucket": "runningmate-7c3f2.appspot.com",
    "messagingSenderId": "867235253757"
}
running_app_firebase = pyrebase.initialize_app(config_running_app)
running_app_db = running_app_firebase.database()

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'running_mate.settings')

app = Celery(
    'running_mate',
    broker='amqp://localhost',
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
# app.config_from_object('django.conf:settings', namespace='CELERY')

app.config_from_object('django.conf:settings')

# Load task modules from all registered Django app configs.
# app.autodiscover_tasks()
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True
)

app.conf.CELERYBEAT_SCHEDULE = {
    'add-every-20-seconds': {
        'task': 'cluster',
        'schedule': timedelta(seconds=20),
        'args': (),
        'options': {'queue' : 'celery_periodic'}
    },
    'add-every-three-hours': {
        'task': 'sending_notification',
        'schedule': crontab(minute=0, hour='*/3'),#timedelta(seconds=60),#
        'args': (),
        'options': {'queue' : 'sending_notification'}
    }# ,
    # 'add-every-day': {
    #     'task': 'sending_email',
    #     'schedule': crontab(minute=0, hour=0),
    #     'args': (),
    #     'options': {'queue' : 'sending_email'}
    # },
}

# define Running Mate's E-mail
running_email = "maxwell111023@gmail.com"

# get friebase access and db
config_running_app = {
    "apiKey": "AIzaSyCjQCwrJHZKAOiNG04ycZnhtIQpGTw5yh4",
    "authDomain": "running-mate-7bb1b.firebaseapp.com",
    "databaseURL": "https://running-mate-7bb1b.firebaseio.com",
    "projectId": "running-mate-7bb1b",
    "storageBucket": "running-mate-7bb1b.appspot.com",
    "messagingSenderId": "610614312598"
}
running_app_firebase = pyrebase.initialize_app(config_running_app)
running_app_db = running_app_firebase.database()

# Create message container - the correct MIME type is multipart/alternative.
# set up test information for sending email
# in future, these info will store in csv file or somewhere
# when time to send, call that file to retrieve info 
# then enter to our email regular format, then send to each player
# At that time, not just only one email, but will use for loop
# to send every single needed email.
msg = MIMEMultipart('alternative')
msg['Subject'] = "2018-06-11 台北政大系內馬拉松競賽"
msg['From'] = running_email

# email file path
send_notification_path = Path("/Users/wangboren/running_mate/running_mate/running_mate/system_email.csv")
sending_email_origin = "/Users/wangboren/running_mate/running_mate/running_mate/system_email.csv"

# Create the body of the message (a plain-text and an HTML version).
html = """\
<html>

  <head>
    <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  </head>
  <style>
    .body{{
        width : 750px;
        font-family: 'Noto Sans', sans-serif !important;
    }}
    .title{{
        color : #E9A11A;
    }}
    .subtitle{{
        color : #EA7484;
    }}
    .content{{
        font-size: 18px;
        color : black;
        font-weight: 400;
    }}
    .star-content{{
        font-size: 18px;
        color : black;
        text-align : center;
    }}
    .last{{
        text-align : right;
    }}
  </style>
  <body style = "font-family: 'Noto Sans', sans-serif !important;width : 750px;">
    <h2 class = "title" style = "color : #E9A11A;">資管「 Running Mate 」首度公開啦 ！！在 6 月 11 號 ， Running Mate 歡迎大家來共襄盛舉哦～～</h2>
    <p class = "content" style = "font-size: 18px;color : black;font-weight: 400;">Hi {name} 您好, 最近忙著期末的你，事否有持續在運動呢？</p>
    <p class = "content" style = "font-size: 18px;color : black;font-weight: 400;">在 6 月 11 號 活動當天，Running Mate 將會在
    「 玉山國際會議廳 」發表最新的 「 跑步交友 」軟體，首度亮相！</p>
    <br>
    <br>
    <p class = "content" style = "font-size: 18px;color : black;font-weight: 400;display: flex;line-height: 30px;">
        <img src = "https://imgur.com/rAZwsfY.png" style = "width: 30px;height: 30px;margin-right: 15px;"/>Running Mate 結合了：    
    </p>
    <ul class = "content" style = "font-size: 18px;color : black;font-weight: 400;">
        <li style = "list-style: none;display: flex;line-height: 30px;margin-bottom: 10px;"><img src = "https://imgur.com/9cXny8v.png" style = "width: 30px;height: 30px;margin-right: 15px;"/>遊戲</li>
        <li style = "list-style: none;display: flex;line-height: 30px;margin-bottom: 10px;"><img src = "https://imgur.com/CvAcZNJ.png" style = "width: 30px;height: 30px;margin-right: 15px;"/>交友</li>
        <li style = "list-style: none;display: flex;line-height: 31px;margin-bottom: 10px;"><img src = "https://imgur.com/tRzkSxx.png" style = "width: 30px;height: 30px;margin-right: 15px;"/>運動</li>
    </ul>

    <br>
    <p class = "content" style = "font-size: 18px;color : black;font-weight: 400;">「 Running Mate 」相信能一定成為時下瘋狂的新穎 APP!!</p>
    
    <br>
    <p class = "content" style = "font-size: 18px;color : black;font-weight: 400;">想當然的，也會有許多驚喜等著各位呢！Running Mate 屆時將會與您共享歡樂！</p>

    <p class = "star-content" style = "font-size: 18px;color : black;text-align : center;">各位朋友們，我們不見不散哦！！</p>
    <h2 class = "subtitle last" style = "color : #E9A11A;text-align : right;">Running Mate,  sincerely</h2>
    <img style = "width: 100%;" src = "https://imgur.com/uxE4QDv.png"/>
  </body>
  
</html>
"""

# for starting
@app.task
def test(arg):
    print(arg)

# send email to each person (system send)
@app.task(name = "sending_notification")
def sending_notification():
    
    global send_notification_path
    global sending_email_origin
    recent_members = list()
    email_to_send = dict()

    #將『 key 』設成『 第 X 筆 』

    if send_notification_path.is_file():
        # file exists
        with open(sending_email_origin,"r") as email :
            email_data = csv.DictReader(email)

            members = running_app_db.child("members").get()
            recent_members =  list(members.val().keys())

            # 將原始檔案中的每行資料讀進每個 key 成為 value 值
            for i in range(len(recent_members)) :
                
                if recent_members[i] != "Running_Mate" :
                    # define some variables
                    email_to_send = dict()
                    email_person = running_app_db.child("email").child(recent_members[i]).get()
                    
                    # check each person's count
                    if email_person.each() == None :
                        current_count = 1
                    else :
                        current_count = len(email_person.val()) + 1

                    # read each line in csv file
                    for line in email_data :
                        if line["收件者"] == "All" or line["收件者"] == recent_members[i] :
                            email_to_send["第"+str(current_count)+"封"] = dict()
                            email_to_send["第"+str(current_count)+"封"]["標題"] = line["標題"]
                            email_to_send["第"+str(current_count)+"封"]["寄件者"] = "Running Mate"
                            email_to_send["第"+str(current_count)+"封"]["收件時間"] = datetime.datetime.now().strftime("%Y-%m-%d")
                            email_to_send["第"+str(current_count)+"封"]["內容"] = line["內容"]
                            email_to_send["第"+str(current_count)+"封"]["狀態"] = 0
                        current_count = current_count + 1 

                    #update info for each person
                    if email_person.each() == None :
                        running_app_db.child("email").child(recent_members[i]).set(email_to_send)
                    else :
                        running_app_db.child("email").child(recent_members[i]).update(email_to_send)
                    
                    # up tp begin and get first row
                    email.seek(0)
                    next(email)
                else :
                    pass

            # print(email_to_send)

            # restart variable and close file
            email_to_send = dict()
            email.close()

            # create directory if not exsist
            if not os.path.exists("email_history"): 
                os.mkdir("email_history")

            # get file count
            history_count = (len([name for name in os.listdir("/Users/wangboren/running_mate/running_mate/email_history") if name.endswith('.' + "csv")]))

            # copy file to history
            copyfile(sending_email_origin, "email_history/system_email_history_"+ str(history_count+1) +".csv")

            # remove that file
            os.remove(sending_email_origin)

    else :
        pass

@app.task(name = "sending_email")
def sending_email():
    
    global running_app_db, msg, html, running_email

    members = running_app_db.child("members").get()

    for all_member in members.each() :
        
        target = all_member.val()["email"]
        name = all_member.val()["name"]

        # set email
        msg["to"] = target

        # put name in html
        html = html.format(name=name)

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)

        # Send the message via local SMTP server.
        s = smtplib.SMTP('localhost')

        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
        s.sendmail(running_email, target, msg.as_string())
        s.quit()

        # sleep for few seconds
        time.sleep(3)
