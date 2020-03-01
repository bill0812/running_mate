import pandas as pd, numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from shapely.geometry import MultiPoint 
import random, uuid, types, math
from celery import shared_task
from celery import Celery
from celery import task
import datetime
from running_mate.celery import app
import pyrebase,json,re
from datetime import timedelta
from time import sleep

# import other file
from runningmate_app import make_friends as make_friends

# initialize our running app
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

# find other players
def find_other_player(member_id_room_no,member_id) :
    
    # define variables
    other_player = list()
    global running_app_db

    room_data_player = running_app_db.child("running_room").child(member_id_room_no).child("經緯度").get()
    for each_player in room_data_player.each() :
        if each_player.key() != member_id :
            other_player.append(each_player.key())
        else :
            pass

    return other_player

# delete specific players and rooms
def delete_players_room(member_id,other_player,member_id_room_no) :

    global running_app_db

    # delete that person who click cancel game
    delete_players(member_id)

    running_app_db.child("running_room").child(member_id_room_no).child("經緯度").child(member_id).remove()

    status = check_all_player_exsist(other_player)

    if status == "still playing" :
        return "still playing"
    elif status == "not playing" :
        if running_app_db.child("running_room").child(member_id_room_no).get().each() == None :
            return "delete room already"
        else :
            running_app_db.child("running_room").child(member_id_room_no).remove()
            return "delete finished"
    else :
        return "Internet went wrong"

# check room's players status
def check_all_player_exsist(other_player) :
    
    # define some variables
    all_players = list()
    status = str()
    global running_app_db

    for players in running_app_db.child("running_player").get().each() :
        all_players.append(players.key())

    for i in range(len(other_player)) :

        if other_player[i] in all_players :
            status =  "still playing"
            break
        else :
            status =  "not playing"

    return status

# delete canceled person
def delete_players(member_id) :
    
    global running_app_db

    # delete that person who click cancel game
    running_app_db.child("running_player").child(member_id).remove()
     
# revise each player room data
def revise_players(other_player,member_id,status) :

    global running_app_db

    for i in range(len(other_player)) :
        running_app_db.child("running_player").child(other_player[i]).child("跑友").child(member_id).remove()
        if status == 0 :
            running_app_db.child("running_player").child(other_player[i]).update({"房間狀態":"不正常狀況"})
        else :
            pass

# revise exsisted players' data
def revise_room(member_id_room_no,member_id,status) :    

    global running_app_db
    count = 0

    running_app_db.child("running_room").child(member_id_room_no).child("經緯度").child(member_id).remove()
    all_current_players = running_app_db.child("running_room").child(member_id_room_no).child("經緯度").get().each()

    if status == 2 :
        for current_player in all_current_players :
            count = count + 1

        if count <=2 :
            running_app_db.child("running_room").child(member_id_room_no).update({"狀態":"不正常狀況"})
    elif status == 3 :
        pass

    return count

# common fuction of delete member while cancel
def cancel_players(member_id,status) :
    
    all_players = list()
    member_id_room_no = str()
    current_player = int()
    global running_app_db

    if running_app_db.child("running_player").get().each() == None :
        pass
    else :
        for players in running_app_db.child("running_player").get().each() :
            all_players.append(players.key())

    if member_id not in all_players :
        return "something went wrong !"
    else :
        member_id_room_no = running_app_db.child("running_player").child(member_id).child("房間").get().val()
        # print(member_id_room_no)
        other_player = find_other_player(member_id_room_no,member_id)
        if status == 1 :
            status_db = delete_players_room(member_id,other_player,member_id_room_no)
        elif status == 2 :
            current_player = revise_room(member_id_room_no,member_id,2)

            # revise player's 房間狀況
            if current_player <= 2 :
                revise_players(other_player,member_id,0)
            else :
                revise_players(other_player,member_id,1)

            delete_players(member_id)
            
            status_db = check_all_player_exsist(other_player)
        
        elif status == 3 :
            current_player = revise_room(member_id_room_no,member_id,3)
            delete_players(member_id)
            for i in range(len(other_player)) :
                running_app_db.child("running_player").child(other_player[i]).child("跑友").child(member_id).remove()

            status_db = check_all_player_exsist(other_player)

    return status_db

# return other friends
def get_rest_friend(member_id) :
    
    # local variables
    global running_app_db
    friends_list = list()
    friends_list.append(member_id)

    friend_get = running_app_db.child("friend_list").child("好友").get().each()

    if friend_get == None :
        pass
    else :
        favor_data = running_app_db.child("friends_list").child(member_id).child("好友").child("摯友").get().each()
        normal_data = running_app_db.child("friends_list").child(member_id).child("好友").child("摯友").get().each()

        if favor_data != None :
            for friend in favor_data :
                friends_list.append(friend.key())

        if normal_data != None :
            for friend in normal_data :
                friends_list.append(friend.key())

    return friends_list

# update members' personal data each run
def update_member_data(member_id,total_distance,total_time,average_time):
    
    # local variables
    global running_app_db
    current_distance , current_time , current_average_time , current_total_count = float() , float() , float() , int()
    
    member_data = running_app_db.child("members").child(member_id).get()
    for data in member_data.each():
        if data.key() == "total_distance(km)" :
            current_distance = float(data.val())
            current_distance = current_distance + total_distance
            # print(current_distance)
            running_app_db.child("members").child(member_id).update({"total_distance(km)" : current_distance})
        elif data.key() == "total_time" :
            current_time = float(data.val())
            current_time = current_time + total_time
            # print(current_time)
            running_app_db.child("members").child(member_id).update({"total_time" : current_time})
        elif data.key() == "average_time" :
            if current_time == 0 :
                current_average_time = 0
            else :
                current_average_time = float(current_distance / current_time)
            # print(current_average_time)
            running_app_db.child("members").child(member_id).update({"average_time" : current_average_time})
        elif data.key() == "total_count" :
            current_total_count = int(data.val())
            current_total_count = current_total_count + 1
            running_app_db.child("members").child(member_id).update({"total_count" : current_total_count})
        else :
            pass

# update history data
def update_history(member_id,total_distance,total_time,average_time):
    
    # local variables
    global running_app_db

    # get historical data
    historical = running_app_db.child("historical_data").child(member_id).get()
    now_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    # update to historical data
    if historical.each() == None :
        historical_data = {
            "第1筆" : {
                        "datetime" : now_time,
                        "total_distance(km)" : total_distance,
                        "total_time" : total_time,
                        "average_time" : average_time
                    }
            } 
        # print(historical_data)  
        running_app_db.child("historical_data").child(member_id).set(historical_data)
    else :
        historical_len = len(running_app_db.child("historical_data").child(member_id).get().val())
        historical_data = {
            "第"+str(historical_len+1)+"筆" : {
                        "datetime" : now_time,
                        "total_distance(km)" : total_distance,
                        "total_time" : total_time,
                        "average_time" : average_time
                    }
            }
        # print(historical_data)  
        running_app_db.child("historical_data").child(member_id).update(historical_data)

# airdrops
def airdrops(member_id,airdrops,airdrops_URL,tokens_URL) :

    # local variables
    global running_app_db
    airdrops_dict = dict()

    airdrops_db = running_app_db.child("members").child(member_id).child("airdrops").get()

    if len((airdrops)) != 0 :
        if airdrops_db.val() == None :
            for i in range(len(airdrops)) :
                airdrops_dict[str(i)] = dict()
                airdrops_dict[str(i)]["名稱"] = airdrops[i]
                # print(type(airdrops_URL[i]))
                # print(airdrops_URL[i])
                real_url = str(airdrops_URL[i][1:-1])
                front_url = real_url[:85]
                back_url = real_url[85:].replace("/", "%2F")
                # print(front_url + back_url + "&token=" + str(tokens_URL[i][1:-1]))
                airdrops_dict[str(i)]["url"] = front_url + back_url + "&token=" + str(tokens_URL[i][1:-1])
                # print(front)
                # print(back)

            running_app_db.child("members").child(member_id).child("airdrops").set(airdrops_dict)
        else :
            for i in range(len(airdrops)) :
                airdrops_dict[str(i + len(airdrops_db.val()))] = dict()
                airdrops_dict[str(i + len(airdrops_db.val()))]["名稱"] = airdrops[i]
                real_url = str(airdrops_URL[i][1:-1])
                front_url = real_url[:85]
                back_url = real_url[85:].replace("/", "%2F")
                # print(front_url + back_url + "&token=" + str(tokens_URL[i][1:-1]))
                airdrops_dict[str(i + len(airdrops_db.val()))]["url"] = front_url + back_url + "&token=" + str(tokens_URL[i][1:-1])
                # print(front)
                # print(back)

            running_app_db.child("members").child(member_id).child("airdrops").update(airdrops_dict)
    else :
        pass
            
# change room airdrops status
def change_room_airdrops_status(room_id,which):
    
    # set up variables
    global running_app_db

    running_app_db.child("running_room").child(room_id).child("空投").child(which).update({
        "status" : 1
    })

# end game normally and update
@app.task(queue="end_game_update")
def end_game_update(member_id,total_distance,total_time,average_time,airdrops_data,airdrops_URL,tokens_URL) :

    # local variables
    global running_app_db
    personal_data = dict()

    # update history data
    update_history(member_id,total_distance,total_time,average_time)

    # update data to personal 
    update_member_data(member_id,total_distance,total_time,average_time)

    # update to airdrops
    airdrops(member_id,airdrops_data,airdrops_URL,tokens_URL)

    # update ranking data and check
    friends = get_rest_friend(member_id)

    # rest for few seconds
    sleep(3)

    # retrieve data
    get_ranking_data_distance , get_ranking_data_time , get_ranking_data_count = make_friends.ranking_data(friends)

    # ranking sort from big to small
    all_distance_ranking = sorted(get_ranking_data_distance.items(), key=lambda d:d[1], reverse = True)
    all_time_ranking = sorted(get_ranking_data_time.items(), key=lambda d:d[1], reverse = True)
    all_count_ranking = sorted(get_ranking_data_count.items(), key=lambda d:d[1], reverse = True)  

    # return finished ranking data
    ranking_data_all = make_friends.return_ranking_data_for_all(all_distance_ranking,all_time_ranking,all_count_ranking)

    # upload to firebase
    running_app_db.child("friends_list").child(member_id).child("排行榜").set(ranking_data_all)

    # retrieve personal data
    retrieve_data = running_app_db.child("members").child(member_id).get().each()
    if retrieve_data == None :
        pass
    else :
        for data in retrieve_data :
            if data.key() == "password" or data.key() == "email" or data.key() == "airdrops":
                pass
            else :
                personal_data[data.key()] = data.val()

    for i in range(len(friends)) :

        if friends[i] != "Running_Mate" :
            if running_app_db.child("friends_list").child(friends[i]).child("排行榜").get().val() == None :
                running_app_db.child("friends_list").child(friends[i]).child("排行榜").set(ranking_data_all)
            else :
                running_app_db.child("friends_list").child(friends[i]).child("排行榜").update(ranking_data_all)
            
            if friends[i] != member_id :
                count ,status = make_friends.check_friend(member_id,friends[i])

                # update personal data when in other friends' normal area
                if status == 1 :
                    running_app_db.child("friends_list").child(friends[i]).child("好友").child("一般好友").child(member_id).update(personal_data)
                
                # update personal data when in other friends' favorite area
                elif status == 2 :
                    running_app_db.child("friends_list").child(friends[i]).child("好友").child("摯友").child(member_id).update(personal_data)

                # status wrong
                else :
                    pass

    # update_room_status(status_db,member_id)
    
    return "fininsh update game data per person"

# players cancel when game is operating
@app.task(queue="durring_game_cancel")
def durring_game_cancel(member_id,total_distance,total_time,average_time) :
    
    # local variables
    global running_app_db

    # update data to personal 
    update_member_data(member_id,total_distance,total_time,average_time)

    # update history data
    update_history(member_id,total_distance,total_time,average_time)

    # take data to cancel_players def
    status_db = cancel_players(member_id,3)

    # update ranking
    friend = make_friends.other_get_friend_list(member_id,[])    

    friend.append(member_id)

    get_ranking_data_distance_past , get_ranking_data_time_past , get_ranking_data_count_past  = make_friends.ranking_data(friend)

    # ranking sort from big to small
    all_distance_ranking = sorted(get_ranking_data_distance_past.items(), key=lambda d:d[1], reverse = True)
    all_time_ranking = sorted(get_ranking_data_time_past.items(), key=lambda d:d[1], reverse = True)
    all_count_ranking = sorted(get_ranking_data_count_past.items(), key=lambda d:d[1], reverse = True)  

    # return finished ranking data
    ranking_data_all = make_friends.return_ranking_data_for_all(all_distance_ranking,all_time_ranking,all_count_ranking)

    # upload to firebase
    if running_app_db.child("friends_list").child(member_id).child("排行榜").get().val() == None :
        running_app_db.child("friends_list").child(member_id).child("排行榜").set(ranking_data_all)
    else :
        running_app_db.child("friends_list").child(member_id).child("排行榜").update(ranking_data_all)

    # update_room_status(status_db,member_id)

    return "finish deleting players when during game ! And status of" + str(member_id) + "'s room info is" + str(status_db)

# when game start , players cnacel
@app.task(queue="start_game_cancel")
def start_game_cancel(member_id) :

    global running_app_db

    # take data to cancel_players def
    status_db = cancel_players(member_id,2)

    return "finish deleting players when starting ! And status of" + str(member_id) + "'s room info is" + str(status_db)

# change status
@app.task(queue="change_status")
def change_status(member_id,which,room_id) :
    
    # set up variables
    global running_app_db

    roon_player = running_app_db.child("running_room").child(room_id).child("經緯度").get().each()

    change_room_airdrops_status(room_id,which)

    for data in roon_player :
        
        running_app_db.child("running_player").child(data.key()).child("空投").child(which).update({
            "status" : 1
        })

    return "success update " + which + " airdrops for all members"

# ==================================================================== #
# all code below may use in the future
# update roome's info
# def update_room_status(status_db,member_id):
    
#     global running_app_db

#     member_id_room_no = running_app_db.child("running_player").child(member_id).child("房間").get()
#     if status_db == "still playing" :
#         pass
#     else :
#         running_app_db.child("running_room").child(member_id_room_no).update({"狀態": "不正常"})

# update_room_status(status_db,member_id)