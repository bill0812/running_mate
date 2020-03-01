# import some django library
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import QueryDict
from django.template.context_processors import csrf
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

# from dwebsocket import require_websocket
# import some other py file from this app
import runningmate_app.circle_cluster as circle
import runningmate_app.identification as id  
import runningmate_app.end_game as end_game
import runningmate_app.make_friends as make_friends

#import some specific library that we need
from geopy.distance import geodesic
import pyrebase,json,re
import datetime

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

# construct some functions 
# logout 
def logout(request):
    if request.method == "POST" :
        print(request.META)
        seeesion_check = request.session.get(request.META["REMOTE_ADDR"],default=None)
        if seeesion_check == None :
            JsonResponse({"result":"logout already ! or long time to login"})
        else :
            del request.session[request.META["REMOTE_ADDR"]]
        return JsonResponse({"result":"logout"})
    else :
        return JsonResponse({"result":"failed"})

# check if session exsist
def check_session(request):
    
    global running_app_db

    if request.method == "POST" :
        # del request.session[request.META["REMOTE_ADDR"]]
        seeesion_check = request.session.get(request.META["REMOTE_ADDR"],default=None)
        print(seeesion_check)
        if seeesion_check == None :
            return JsonResponse({"result":"Not Login Before",
                                 "member_id" : "no id"
                                })
        else :
            request.session[request.META["REMOTE_ADDR"]]["cluster"] =  "no"
            request.session[request.META["REMOTE_ADDR"]]["cluster_count"] =  0
            return JsonResponse({"result":"login already",
                                 "member_id" : request.session[request.META["REMOTE_ADDR"]]["members"]
                                })
                
    else :
        return JsonResponse({"result":"something went wrong",
                              "member_id" : "no id"
                            })

# update data
def update_member(request):
    if request.method == "POST" :
        update_member_dict = QueryDict((request.body).decode('utf-8')).dict()
        status = id.update_member(update_member_dict,running_app_db)
        return JsonResponse({"result":"success",
                             "update_status" : status
                            })
    else :
        return JsonResponse({"result":"failed"})

# regiser function
def register_member(request):
    if request.method == "POST" :
        member_dict = QueryDict((request.body).decode('utf-8')).dict()
        email = str(member_dict["email"])
        password = str(member_dict["password"])
        birth_day = str(member_dict["birth_day"])
        birth_month = str(member_dict["birth_month"])
        birth_year = str(member_dict["birth_year"])
        name = str(member_dict["name"])
        sex = str(member_dict["sex"])
        sex_prefer = str(member_dict["sex_prefer"])
        member_status , member_key = id.register_member(email,password,birth_day,birth_month,birth_year,name,sex,sex_prefer,running_app_db)
        return JsonResponse({"result":"success",
                             "register_status" : member_key,
                             "member_id" : member_status
                            })
    else :
        return JsonResponse({"result":"failed"})

# login function
def login_member(request):
    if request.method == "POST" :
        member_dict = QueryDict((request.body).decode('utf-8')).dict()
        email = str(member_dict["email"])
        password = str(member_dict["password"])
        member_id = id.login_member(email,password,running_app_db)
        if member_id == "login failed":
            return JsonResponse({"result":"failed",
                                "member_id" : "login failed"
                               })
        else:
            request.session[request.META["REMOTE_ADDR"]] = dict()
            request.session[request.META["REMOTE_ADDR"]]["members"] =  member_id
            request.session[request.META["REMOTE_ADDR"]]["cluster"] =  "no"
            request.session[request.META["REMOTE_ADDR"]]["cluster_count"] =  0
            return JsonResponse({"result":"success",
                                "member_id" : member_id
                               })
    else :
        return JsonResponse({"result":"failed"})

# circle cluster for each players
def circle_cluster(request):
    if request.method == "POST" and request.session[request.META["REMOTE_ADDR"]]["cluster"] == "no" and request.session[request.META["REMOTE_ADDR"]]["cluster_count"] ==  0 :
        request.session[request.META["REMOTE_ADDR"]]["cluster"] =  "yes"
        request.session[request.META["REMOTE_ADDR"]]["cluster_count"] =  1
        place_dict = QueryDict((request.body).decode('utf-8')).dict()
        x = float(place_dict["x"])
        y = float(place_dict["y"])
        print("=== current player : ===")
        print("(" + str(x) + "," + str(y) + ")")
        id_key = str(place_dict["member_id"])
        circle.put_data.delay(x,y,id_key) 
        return JsonResponse({"result":"success cluster"})
    elif request.method == "POST" and request.session[request.META["REMOTE_ADDR"]]["cluster"] == "yes" and request.session[request.META["REMOTE_ADDR"]]["cluster_count"] ==  1:
        return JsonResponse({"result":"failed to cluster"})
    else :
        return JsonResponse({"result":"failed to connect"})

# add data and update them after game end normally
def add_to_history(request) :
    if request.method == "POST" :
        end_game_data = QueryDict((request.body).decode('utf-8')).dict()
        member_id = str(end_game_data["member_id"])
        total_distance = float(end_game_data["total_distance(km)"])
        airdrops = str(end_game_data["airdrops"])
        airdrops_URL = str(end_game_data["airdrops_URL"])
        tokens_URL = str(end_game_data["tokens_URL"])
        total_time = float(end_game_data["total_time"])
        airdrops_convert = re.findall(r"[\w']+", airdrops)
        airdrops_URL_convert = re.split(', | ', airdrops_URL[1:-1])
        tokens_URL_convert = re.split(',', tokens_URL[1:-1])
        print(airdrops_URL_convert)
        if float(total_distance) == 0 :
            average_time = 0
        else :
            average_time = float(total_time)/float(total_distance)
        request.session[request.META["REMOTE_ADDR"]]["cluster"] =  "no"
        request.session[request.META["REMOTE_ADDR"]]["cluster_count"] =  0

        end_game.end_game_update.delay(member_id,total_distance,total_time,average_time,airdrops_convert,airdrops_URL_convert,tokens_URL_convert) 
        return JsonResponse({"result":"dealing with data..."})
    else :
        return JsonResponse({"result":"failed"})

# check if member cancel when starting game
def start_game_cancel(request):
    if request.method == "POST" :
        seeesion_check = request.session.get(request.META["REMOTE_ADDR"],default=None)
        
        if seeesion_check == None :
            pass
        else :
            end_game_abnormally = QueryDict((request.body).decode('utf-8')).dict()
            member_id = str(end_game_abnormally["member_id"])
            request.session[request.META["REMOTE_ADDR"]]["cluster"] =  "no"
            request.session[request.META["REMOTE_ADDR"]]["cluster_count"] =  0
            end_game.start_game_cancel.delay(member_id) 
        
        return JsonResponse({"result":"success"})
    else :
        return JsonResponse({"result":"failed"})

# cnacel during game
def durring_game_cancel(request) :
    if request.method == "POST" :
        end_game_abnormally = QueryDict((request.body).decode('utf-8')).dict()
        member_id = str(end_game_abnormally["member_id"])
        total_distance = float(end_game_abnormally["total_distance(km)"])
        total_time = float(end_game_abnormally["total_time"])
        if float(total_distance) == 0 :
            average_time = 0
        else :
            average_time = float(total_time)/float(total_distance)

        request.session[request.META["REMOTE_ADDR"]]["cluster"] =  "no"
        request.session[request.META["REMOTE_ADDR"]]["cluster_count"] =  0
        end_game.durring_game_cancel.delay(member_id,total_distance,total_time,average_time) 
        return JsonResponse({"result":"success"})
    else :
        return JsonResponse({"result":"failed"})

# delete from main pool
def delete_from_main_pool(request) :
    if request.method == "POST" :
        place_dict = QueryDict((request.body).decode('utf-8')).dict()
        id_key = str(place_dict["member_id"])
        request.session[request.META["REMOTE_ADDR"]]["cluster"] =  "no"
        request.session[request.META["REMOTE_ADDR"]]["cluster_count"] =  0
        circle.delete_person.delay(id_key,1)
        return JsonResponse({"result":"dealing with data..."})
    else :
        return JsonResponse({"result":"failed"})

# add to friend
def add_to_friend(request) :
    if request.method == "POST" :
        member_id_finish_game = QueryDict((request.body).decode('utf-8')).dict()
        make_friends.add_friend.delay(member_id_finish_game)
        return JsonResponse({"result":"dealing with data..."})
    else :
        return JsonResponse({"result":"failed"})

# app terminate abnormally
def app_terminate(request):
    
    global running_app_db

    if request.method == "POST" :
        seeesion_check = request.session.get(request.META["REMOTE_ADDR"],default=None)
        
        if seeesion_check == None :
            pass
        else :
            member_id_app_terminate = QueryDict((request.body).decode('utf-8')).dict()
            id_key = str(member_id_app_terminate["member_id"])

            circle.delete_person.delay(id_key,2)
            request.session[request.META["REMOTE_ADDR"]]["cluster"] =  "no"
            request.session[request.META["REMOTE_ADDR"]]["cluster_count"] =  0
            
        return JsonResponse({"result":"terminate done"
                            })
           
    else :
        return JsonResponse({"result":"something went wrong"
                            })

# return some problems
def return_problems(request):
    
    global running_app_db
    problems_kind = list()
    update_each_person_problem = dict()
    update_each_person_problem["正常選項"] = dict()
    update_each_person_problem["其他選項"] = dict()

    if request.method == "POST" :
        problems = QueryDict((request.body).decode('utf-8')).dict()

        # get member id
        member_id = str(problems["member_id"])

        # receive all problems
        problems_convert = re.findall(r"[\w']+", str(problems["problems"]))
        
        # retrieve kinds of problems
        retrieve_database = running_app_db.child("回報問題選項").get().each()

        for kinds in retrieve_database :
            problems_kind.append(kinds.val())

        for i in range(len(problems_convert)) :
            if problems_convert[i] in problems_kind :
                update_each_person_problem["正常選項"][i] = problems_convert[i]
            else :
                update_each_person_problem["其他選項"][i] = problems_convert[i]
        
        now_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")     

        # retrieve historical problem each person
        each_person_retrieve = running_app_db.child("回報問題待處理").child(member_id).get()

        if each_person_retrieve.each() == None :
            running_app_db.child("回報問題待處理").child(member_id).set({
                now_time : update_each_person_problem
            })
        else :
            running_app_db.child("回報問題待處理").child(member_id).update({
                now_time : update_each_person_problem
            })

        return JsonResponse({"result":"receive some problems and update !!"
                            })
           
    else :
        return JsonResponse({"result":"something went wrong"
                            })

# use airdrops  
def use_airdrops(request):

    global running_app_db
    original_airdrops = list()
    update_to_used = dict()
    update_to_not_used = dict()

    if request.method == "POST" :

        member_use_airdrops = QueryDict((request.body).decode('utf-8')).dict()

        # get member id
        member_id = str(member_use_airdrops["member_id"])

        # used airdrops
        used_airdrops = re.findall(r"[\w']+", str(member_use_airdrops["used_airdrops"]))

        # retrieve member's original data
        get_all_airdrops = running_app_db.child("members").child(member_id).child("airdrops").get().each()

        if get_all_airdrops == None :
            
            pass

        else :
            for data in get_all_airdrops :
                original_airdrops.append(data.val())

            for i in range(len(used_airdrops)) :
                if used_airdrops[i] in original_airdrops :
                    original_airdrops.remove(used_airdrops[i])
                    update_to_used[str(i)] = used_airdrops[i]

            for i in range(len(original_airdrops)) :
                update_to_not_used[str(i)] = original_airdrops[i]

            running_app_db.child("members").child(member_id).update({
                "airdrops" : update_to_not_used
            })

            now_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")     

            if running_app_db.child("使用過的空投").child(member_id).get().each() == None :
                running_app_db.child("使用過的空投").child(member_id).set({
                    now_time : update_to_used
                })
            else :
                running_app_db.child("使用過的空投").child(member_id).update({
                    now_time : update_to_used
                })

        return JsonResponse({"result":" Use Airdrops !!"
                            })
           
    else :
        return JsonResponse({"result":"something went wrong"
                            })

# update friend status
def update_friend_status(request) :

    global running_app_db

    if request.method == "POST" :

        member_friend_update = QueryDict((request.body).decode('utf-8')).dict()

        # get member id
        member_id = str(member_friend_update["member_id"])

        # get friend data
        friend = str(member_friend_update["friend_id"])

        # determine status
        # status = 1 : normal to  favorite
        # status = 2 : favorite to normal 
        status_change = str(member_friend_update["type"])

        
        # get friend status currently
        count , status_current = make_friends.check_friend(friend,member_id)

        if status_current == 1 :
            if status_change == 1 :
                current_data = running_app_db.child("friend_list").child(member_id).child("好友").child("一般好友").child(friend).get().each()
                if current_data != None :
                    running_app_db.child("friend_list").child(member_id).child("好友").child("摯友").set({
                        member_id : current_data
                    })
                    running_app_db.child("friend_list").child(member_id).child("好友").child("一般好友").child(friend).remove()

            else :
                pass
        
        elif status_current == 2 :
            if status_change == 2 :
                current_data = running_app_db.child("friend_list").child(member_id).child("好友").child("").child(friend).get().each()
                if current_data != None :
                    running_app_db.child("friend_list").child(member_id).child("好友").child("一般好友").set({
                        member_id : current_data
                    })
                    running_app_db.child("friend_list").child(member_id).child("好友").child("摯友").child(friend).remove()

            else :
                pass

        else :
            pass
        
        return JsonResponse({"result":"successful data"
                            })

    else :
        return JsonResponse({"result":"something went wrong"
                            })

# change airdrops status each room
def change_airdrops(request) :

    if request.method == "POST" :
        update_member_airdrops = QueryDict((request.body).decode('utf-8')).dict()
        member_id = str(update_member_airdrops["member_id"])
        which = str(update_member_airdrops["which"])
        room_id = running_app_db.child("running_player").child(member_id).get().val()["房間"]
        
        # change no. to string
        if which == "0" :
            which = "first"
        elif which == "1" :
            which = "second"
        elif which == "2" :
            which = "third"

        # change status of each room's airdrops status
        end_game.change_status.delay(member_id,which,room_id)
        return JsonResponse({"result":"success"})
    else :
        return JsonResponse({"result":"failed"})
