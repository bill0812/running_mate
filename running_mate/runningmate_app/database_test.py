# create and construct "member" database
import hashlib
def member(running_app_db):
    # email password birth 性取向 姓名 性別
    member_data = {
        "email" : "maxwell111023@gmail.com",
        "password" : "Maxwell111023",
        "birth_day" : "12",
        "birth_month" : "August",
        "birth_year" : "1997",
        "name" : "王柏仁",
        "sex" : "Male",
        "sex_prefer" : "Female"
    }
    member_datakey_hash = hashlib.sha256("maxwell111023@gmail.com".encode()+"Maxwell111023".encode())
    running_app_db.child("members").child(member_datakey_hash.hexdigest()).set(member_data)

