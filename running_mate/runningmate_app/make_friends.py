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
import re

# import other file
from  runningmate_app import end_game as end_game

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

# get friends data
def get_final_friends(current_player_member_id) :
     
    # set up some variables
    global running_app_db
    friends_data = list()

    player_data = running_app_db.child("running_player").child(current_player_member_id).child("跑友").get().each()

    if player_data != None :
        for data in player_data :
            friends_data.append(data.key())
    else :
        pass

    return friends_data

# get ranking data and update
def ranking_data(friends) :
    
    # set up some variables
    global running_app_db
    distance_dict = dict()
    time_dict = dict()
    count_dict = dict()

    for i in range(len(friends)) :
        
        if friends[i] != "Running_Mate" :
        
            distance_get = running_app_db.child("members").child(friends[i]).child("total_distance(km)").get()
            count_get = running_app_db.child("members").child(friends[i]).child("total_count").get()
            time_get = running_app_db.child("members").child(friends[i]).child("average_time").get()
            distance_dict[friends[i]] = float(distance_get.val())
            time_dict[friends[i]] = float(time_get.val())
            count_dict[friends[i]] = float(count_get.val())

    print(distance_dict)
    print(time_dict)
    print(count_dict)
    
    return distance_dict,time_dict,count_dict

# get other friend list to update ranking
def other_get_friend_list(current_player,friends):
    
    # set up some variables
    global running_app_db
    firend_list = list()
    other_friend = list()

    all_friend = running_app_db.child("friends_list").child(current_player).child("好友").get()

    if all_friend.each() != None :
        
        favor_data = running_app_db.child("friends_list").child(current_player).child("好友").child("摯友").get().each()
        normal_data = running_app_db.child("friends_list").child(current_player).child("好友").child("一般好友").get().each()

        if favor_data != None :
            for friend in favor_data :
                
                if friend.key() != "Running_Mate" :
                    firend_list.append(friend.key())

        if normal_data != None :
            for friend in normal_data :
                firend_list.append(friend.key())

        for i in range(len(firend_list)) :
            if firend_list[i] in friends :
                pass
            else :
                other_friend.append(firend_list[i])
    else :
        pass

    return other_friend

# return all ranking data
def return_ranking_data_for_all(all_distance_ranking,all_time_ranking,all_count_ranking):

    # set variables
    global running_app_db
    ranking_all = dict()
    ranking_all["distance"] = dict()
    ranking_all["time"] = dict()
    ranking_all["count"] = dict()
    for i in range(len(all_distance_ranking)) :
        ranking_all["distance"]["第"+str(i+1)+"名"] = dict()
        ranking_all["distance"]["第"+str(i+1)+"名"]["id"] = str(all_distance_ranking[i][0])
        ranking_all["distance"]["第"+str(i+1)+"名"]["value"] = float(all_distance_ranking[i][1])
        ranking_all["distance"]["第"+str(i+1)+"名"]["url"] = running_app_db.child("members").child(all_distance_ranking[i][0]).child("profileImageURL").get().val()[0]
        ranking_all["distance"]["第"+str(i+1)+"名"]["name"] = running_app_db.child("members").child(all_distance_ranking[i][0]).get().val()["name"]

    for i in range(len(all_time_ranking)) :
        ranking_all["time"]["第"+str(i+1)+"名"] = dict()
        ranking_all["time"]["第"+str(i+1)+"名"]["id"] = str(all_time_ranking[i][0])
        ranking_all["time"]["第"+str(i+1)+"名"]["value"] = float(all_time_ranking[i][1])
        ranking_all["time"]["第"+str(i+1)+"名"]["url"] = running_app_db.child("members").child(all_time_ranking[i][0]).child("profileImageURL").get().val()[0]
        ranking_all["time"]["第"+str(i+1)+"名"]["name"] = running_app_db.child("members").child(all_time_ranking[i][0]).get().val()["name"]

    for i in range(len(all_count_ranking)) :
        ranking_all["count"]["第"+str(i+1)+"名"] = dict()
        ranking_all["count"]["第"+str(i+1)+"名"]["id"] = str(all_count_ranking[i][0])
        ranking_all["count"]["第"+str(i+1)+"名"]["value"] = float(all_count_ranking[i][1])
        ranking_all["count"]["第"+str(i+1)+"名"]["url"] = running_app_db.child("members").child(all_count_ranking[i][0]).child("profileImageURL").get().val()[0]
        ranking_all["count"]["第"+str(i+1)+"名"]["name"] = running_app_db.child("members").child(all_count_ranking[i][0]).get().val()["name"]

    return ranking_all

# check friend
def check_friend(friend,current_player_member_id) :
    
    # set variables
    global running_app_db
    favorite_friend = running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("摯友").child(friend).get()
    normal_friend = running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("一般好友").child(friend).get()

    # return status 1 when friend exisit in normal friend before 
    # And get count data
    if favorite_friend.each() == None and normal_friend.each() != None :
        
        check_count = normal_friend.val()["遇到次數"]
        status = 1

    # return status 2 when friend exisit in favorite friend before 
    # And get count data
    elif favorite_friend.each() != None and normal_friend.each() == None :
        
        check_count = favorite_friend.val()["遇到次數"]
        status = 2

    # return status 3 when friend exisit in favorite friend before and also in normal friend 
    # And get count data
    # But this is abnormal situation 
    # hardly happened
    elif favorite_friend.each() != None and normal_friend.each() != None :
        
        check_count = max([int(favorite_friend.val()["遇到次數"]),int(normal_friend.val()["遇到次數"])])
        status = 3

    # There is no data in friend
    elif favorite_friend.each() == None and normal_friend.each() == None :
        
        check_count = 0
        status = 4
        
    return check_count , status

# remove current firend data
def check_type_remove_current(check_status,current_player_member_id,friend,type_no):   

    # set variables
    global running_app_db

    if type_no == 1 :
        
        if check_status == 1 :
            running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("一般好友").child(friend).remove()
        
        elif check_status == 3 :
            running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("一般好友").child(friend).remove()
            running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("摯友").child(friend).remove()

        elif check_status == 2  and check_status == 4 :
            pass

    else :
        
        if check_status == 2 :
            running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("摯友").child(friend).remove()
        
        elif check_status == 3 :
            running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("一般好友").child(friend).remove()
            running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("摯友").child(friend).remove()

        elif check_status == 1  and check_status == 4 :
            pass
      
# retrieve personal data
def retrieve_personal(friend) :
    
    global running_app_db
    personal = dict()

    if running_app_db.child("members").child(friend).get().each() == None :
        
        pass
    
    else :
        
        for data in running_app_db.child("members").child(friend).get().each() :
            
            if data.key() == "password" or data.key() == "email":
                pass
            
            else :
                personal[data.key()] = data.val()

    return personal

# add friend
@app.task(queue="add_friend")
def add_friend(member_id_finish_game):

    # set up some variables
    global running_app_db
    friends_dict = dict()
    friends_dict["摯友"] = dict()
    friends_dict["一般好友"] = dict()

    current_player_member_id = str(member_id_finish_game["member_id"])
    favorite = str(member_id_finish_game["favorite"])
    favorite_convert = re.findall(r"[\w']+", favorite)

    # check if in friend list
    friends = get_final_friends(current_player_member_id)
    
    for i in range(len(friends)) :
        
        check_count, check_status = check_friend(friends[i],current_player_member_id)
        personal_data = retrieve_personal(friends[i])
        
        # do this when sended data in "摯友"
        if friends[i] in favorite_convert : 
            friends_dict["摯友"][friends[i]] = dict()
            check_type_remove_current(check_status,current_player_member_id,friends[i],1)
            friends_dict["摯友"][friends[i]]["個人資料"] = personal_data
            friends_dict["摯友"][friends[i]]["遇到次數"] = check_count + 1
        
        # do this when sended data in "一般好友"
        else :
            friends_dict["一般好友"][friends[i]] = dict()
            check_type_remove_current(check_status,current_player_member_id,friends[i],2)
            friends_dict["一般好友"][friends[i]]["個人資料"] = personal_data
            friends_dict["一般好友"][friends[i]]["遇到次數"] = check_count + 1

    # current friend ranking
    get_ranking_data_distance_current , get_ranking_data_time_current , get_ranking_data_count_current = ranking_data(friends)
        
    # check and return other friends
    other_friend = other_get_friend_list(current_player_member_id,friends)

    # add myself
    other_friend.append(current_player_member_id)

    # return ranking data for other friends
    get_ranking_data_distance_past , get_ranking_data_time_past , get_ranking_data_count_past  = ranking_data(other_friend)

    # update current ranking data
    get_ranking_data_distance_current.update(get_ranking_data_distance_past)
    get_ranking_data_count_current.update(get_ranking_data_count_past)
    get_ranking_data_time_current.update(get_ranking_data_time_past)

    # ranking sort from big to small
    all_distance_ranking = sorted(get_ranking_data_distance_current.items(), key=lambda d:d[1], reverse = True)
    all_time_ranking = sorted(get_ranking_data_time_current.items(), key=lambda d:d[1], reverse = True)
    all_count_ranking = sorted(get_ranking_data_count_current.items(), key=lambda d:d[1], reverse = True)  

    # return finished ranking data
    ranking_data_all = return_ranking_data_for_all(all_distance_ranking,all_time_ranking,all_count_ranking)

    # upload to firebase
    if running_app_db.child("friends_list").child(current_player_member_id).child("排行榜").get().val() == None :
        running_app_db.child("friends_list").child(current_player_member_id).child("排行榜").set(ranking_data_all)
    else :
        running_app_db.child("friends_list").child(current_player_member_id).child("排行榜").update(ranking_data_all)

    if running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("摯友").get().val() == None :
        running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("摯友").set(friends_dict["摯友"])
    else :
        running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("摯友").update(friends_dict["摯友"])
    
    if running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("一般好友").get().val() == None :
        running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("一般好友").set(friends_dict["一般好友"])
    else :
        running_app_db.child("friends_list").child(current_player_member_id).child("好友").child("一般好友").update(friends_dict["一般好友"])
    

    # get all friends 
    # other_friend.extend(friends)

    # for i in range(len(other_friend)) :
        
    #     if other_friend[i] != "Running_Mate" :
    #         if running_app_db.child("friends_list").child(other_friend[i]).child("排行榜").get().val() == None :
    #             running_app_db.child("friends_list").child(other_friend[i]).child("排行榜").set(ranking_data_all)
    #         else :
    #             running_app_db.child("friends_list").child(other_friend[i]).child("排行榜").update(ranking_data_all)

    # return status
    status_db = end_game.cancel_players(current_player_member_id,1)

    return "fininsh adding friends per person And status of" + str(current_player_member_id) + "'s room info is" + str(status_db)


    