# email password birth 性取向 姓名 性別
import hashlib
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

running_email = "104306093@nccu.edu.tw"

msg = MIMEMultipart('alternative')
msg['Subject'] = "2018-06-11 台北政大系內馬拉松競賽!!!"
msg['From'] = running_email

# Create the body of the message (a plain-text and an HTML version).
html = '''
<html>

  <head></head>
  <style>
    .body{{
        width : 750px;
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
  <body style = "width : 750px;">
    <h2 class = "title" style = "color : #E9A11A;">資管馬拉松首度舉辦！！在 6 月 11 號 ， Running Mate 歡迎大家來共襄盛舉哦～～</h>
    <p class = "content" style = "font-size: 18px;color : black;font-weight: 400;">Hi {name} , 最近還好嗎 !?</p>
    <p class = "content" style = "font-size: 18px;color : black;font-weight: 400;">親愛的{name}跑友，相信您對於跑步開始產生極大樂趣了吧！當天的馬拉松活動不只要為了成績而戰，中途也設置了許多關卡、空頭等著大家哦！
    想當然的，也會有許多驚喜等著各位呢！Running Mate 屆時將會與您共享歡樂！</p>
    <p class = "star-content" style = "font-size: 18px;color : black;text-align : center;">各位跑友，來賺積分跟禮物吧！！</p>
    <h2 class = "subtitle last" style = "color : #E9A11A;text-align : right;">Running Mate,  sincerely</p>
  </body>
  
</html>
'''

# register member
def register_member(email,password,birth_day,birth_month,birth_year,name,sex,sex_prefer,running_app_db):
    # email password birth 性取向 姓名 性別
    global msg,html
    email_list = list()
    print(name)

    all_member = running_app_db.child("members").get()
    if all_member.each() == None :
        member_data = {
            "email" : email,
            "password" : password,
            "birth_day" : birth_day,
            "birth_month" : birth_month,
            "birth_year" : birth_year,
            "name" : name,
            "sex" : sex,
            "sex_prefer" : sex_prefer,
            "total_distance(km)" : 0,
            "average_time" : 0,
            "total_count" : 0,
            "total_time" : 0,
            "嘗試" : " ",
            "困擾" : " ",
            "興趣" : " ",
            "居住地" : " ",
            "school" : " "
        }

        member_datakey_hash = hashlib.sha256(email.encode()+password.encode())

        # set running mate favorite friend
        if running_app_db.child("friends_list").child(member_datakey_hash.hexdigest()).child("好友").child("摯友").child("Running_Mate").get().val() != None :
            
            pass
        
        else :
            running_app_db.child("friends_list").child(member_datakey_hash.hexdigest()).child("好友").child("摯友").child("Running_Mate").update({
                "個人資料" : {
                    "average_time" : " - ",
                    "birth_day" : " - ",
                    "birth_month" : " - ",
                    "birth_year" : " - ",
                    "name" : "Running_Mate",
                    "profileImageURL" : {
                        "0" : "https://firebasestorage.googleapis.com/v0/b/running-mate-7bb1b.appspot.com/o/Running_Mate%2FR_logo.jpg?alt=media&token=bcc045a2-de37-471b-9bcc-007ea5c4dd94"
                    },
                    "sex" : " - ",
                    "sex_prefer" : " - ",
                    "total_count" : " - ",
                    "total_distance(km)" : " - ",
                    "total_time" : " - "
                },
                "遇到次數" : 0,
            })

        running_app_db.child("members").child(member_datakey_hash.hexdigest()).set(member_data)

        # send notification
        email_to_send = dict()
        email_to_send["第"+str(1)+"封"] = dict()
        email_to_send["第"+str(1)+"封"]["標題"] = "2018-06-11 資管 Running Mate 首度公開!!!"
        email_to_send["第"+str(1)+"封"]["寄件者"] = "Running Mate"
        email_to_send["第"+str(1)+"封"]["收件時間"] = datetime.datetime.now().strftime("%Y-%m-%d")
        email_to_send["第"+str(1)+"封"]["內容"] = "歡迎使用 Running Mate 跑步交友軟體！！很高興您加入跑步的大家庭！願未來{}跑友能在 Running  Mate 上遇到各種驚喜！！".format(name)
        email_to_send["第"+str(1)+"封"]["狀態"] = 0

        email_person = running_app_db.child("email").child(member_datakey_hash.hexdigest()).get()

        #update info for each person
        if email_person.each() == None :
            running_app_db.child("email").child(member_datakey_hash.hexdigest()).set(email_to_send)
        else :
            running_app_db.child("email").child(member_datakey_hash.hexdigest()).update(email_to_send)
            
        # sending first email
        msg["to"] = email
        html_rep = html
        html_rep = html_rep.format(name=name)

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(html_rep, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)

        # Send the message via local SMTP server.
        s = smtplib.SMTP('localhost')

        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
        s.sendmail(running_email, email, msg.as_string())
        s.quit()

        return member_datakey_hash.hexdigest() , "註冊成功"
    else :
        for member in all_member.each():
            if member.key() == "Running_Mate" :
                pass
            else:
                email_list.append(member.val()["email"])
            # print(member.val()["email"])
        if email not in email_list :
            member_data = {
                "email" : email,
                "password" : password,
                "birth_day" : birth_day,
                "birth_month" : birth_month,
                "birth_year" : birth_year,
                "name" : name,
                "sex" : sex,
                "sex_prefer" : sex_prefer,
                "total_distance(km)" : 0,
                "average_time" : 0,
                "total_count" : 0,
                "total_time" : 0,
                "嘗試" : " ",
                "困擾" : " ",
                "興趣" : " ",
                "居住地" : " ",
                "school" : " "
            }

            member_datakey_hash = hashlib.sha256(email.encode()+password.encode())

            # set running mate favorite friend
            if running_app_db.child("friends_list").child(member_datakey_hash.hexdigest()).child("好友").child("摯友").child("Running_Mate").get().val() != None :
                
                pass
            
            else :
                running_app_db.child("friends_list").child(member_datakey_hash.hexdigest()).child("好友").child("摯友").child("Running_Mate").update({
                    "個人資料" : {
                        "average_time" : " - ",
                        "birth_day" : " - ",
                        "birth_month" : " - ",
                        "birth_year" : " - ",
                        "name" : "Running_Mate",
                        "profileImageURL" : {
                            "0" : "https://firebasestorage.googleapis.com/v0/b/running-mate-7bb1b.appspot.com/o/Running_Mate%2FR_logo.jpg?alt=media&token=bcc045a2-de37-471b-9bcc-007ea5c4dd94"
                        },
                        "sex" : " - ",
                        "sex_prefer" : " - ",
                        "total_count" : " - ",
                        "total_distance(km)" : " - ",
                        "total_time" : " - "
                    },
                    "遇到次數" : 0,
                })

            running_app_db.child("members").child(member_datakey_hash.hexdigest()).set(member_data)

            # send notification
            email_to_send = dict()
            email_to_send["第"+str(1)+"封"] = dict()
            email_to_send["第"+str(1)+"封"]["標題"] = "2018-06-11 資管 Running Mate 首度公開!!!"
            email_to_send["第"+str(1)+"封"]["寄件者"] = "Running Mate"
            email_to_send["第"+str(1)+"封"]["收件時間"] = datetime.datetime.now().strftime("%Y-%m-%d")
            email_to_send["第"+str(1)+"封"]["內容"] = "歡迎使用 Running Mate 跑步交友軟體！！很高興您加入跑步的大家庭！願未來{}跑友能在 Running  Mate 上遇到各種驚喜！！".format(name)
            email_to_send["第"+str(1)+"封"]["狀態"] = 0

            email_person = running_app_db.child("email").child(member_datakey_hash.hexdigest()).get()

            #update info for each person
            if email_person.each() == None :
                running_app_db.child("email").child(member_datakey_hash.hexdigest()).set(email_to_send)
            else :
                running_app_db.child("email").child(member_datakey_hash.hexdigest()).update(email_to_send)

            # sending first email
            msg["to"] = email
            html_rep = html
            html_rep = html_rep.format(name=name)

            # Record the MIME types of both parts - text/plain and text/html.
            part1 = MIMEText(html_rep, 'html')

            # Attach parts into message container.
            # According to RFC 2046, the last part of a multipart message, in this case
            # the HTML message, is best and preferred.
            msg.attach(part1)
            # Send the message via local SMTP server.
            s = smtplib.SMTP('localhost')
            # sendmail function takes 3 arguments: sender's address, recipient's address
            # and message to send - here it is sent as one string.
            s.sendmail(running_email, email, msg.as_string())
            s.quit()

            return member_datakey_hash.hexdigest() , "註冊成功"
        else :
            return "no key" , "註冊失敗"

# login member
def login_member(email,password,running_app_db):
    # get email and password hash key
    member_status = "login failed"

    member_datakey_hash = hashlib.sha256(email.encode()+password.encode())

    all_member = running_app_db.child("members").get()
    for member in all_member.each():
        if member_datakey_hash.hexdigest() == member.key():
            member_status = member_datakey_hash.hexdigest()
            break
   
    return member_status

# update personal info
def update_member(update_member_dict,running_app_db) :
    all_member = running_app_db.child("members").get()
    all_member_key = list()
    if all_member.each() == None :
        return "更新失敗"
    else :
        for member in all_member.each():
            all_member_key.append(member.key())
            
        if str(update_member_dict["member_id"]) not in  all_member_key :
            return "更新失敗"
        else :
            for update_key,update_value in update_member_dict.items() :
                if update_key == "member_id" :
                    pass
                else :
                    running_app_db.child("members").child(update_member_dict["member_id"]).update({str(update_key): str(update_value)})
            return "更新成功"

