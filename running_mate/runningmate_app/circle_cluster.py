import pandas as pd, numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from geopy.distance import geodesic
from shapely.geometry import MultiPoint 
import random, uuid, types, math
from celery import shared_task
from celery import Celery
from celery import task
from datetime import timedelta
from running_mate.celery import app
import pyrebase,json
import googlemaps
import urllib.request 
import qrcode
from urllib.request import Request, urlopen
from time import sleep

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
storage = running_app_firebase.storage()

# define some data set
df = pd.read_csv('summer-travel-gps-full.csv')
coords = df.as_matrix(columns=['lat', 'lon'])
main_pool = {
    "b698893899fd416d2edfa68d20031a584f213089e7dec47340991f102d5db7b9" : {
        "x" : 121.576692619234,
        "y" : 24.9864641918703
    },
    # "eedf72e088d4753d1ab4dbe974d95a4c1ae0072fa037c192cd4007771c459948" : {
    #     "x" : 121.576692619234,
    #     "y" : 24.9864641918703
    # },
    "21060d5cb18c11bb4808683194fa4948883cc1abc558db02ff345d03c6181023" : {
        "x" : 51.4801463,
        "y" : -0.4411027
    }
}
# main_pool = {

# }
gift = ["舒跑買一送一","乳清系列95折","PowerBar買一送一","健身課程送一堂","皮拉提斯課程"]

# define left pool and main pool for dictionary and list data type respectively
left_pool = dict()
main_pool_list = list()

# define for room data, each player data and pool status
room = dict()
players = dict()
main_pool_status = 0

# define for clustering parameters
kms_per_radian = 6371.0088
epsilon = 3 / kms_per_radian
far_person_add_km = 2.95

# some parameters about math
average_earth_radius = 6378.1
d_center1 = 1.5
d_center2 = 0.75
d_center3 = 0.7

# google map api
api_key = "AIzaSyCSYMBNKYYrsaww53kOF0PuwKxRRxGq1rs"
# for evalation 
api_key_evalation_c1 = "AIzaSyAyIMaNpGjadSM2Y6nzj_eoH8hfw-quMw4"
api_key_evalation_c2 = "AIzaSyBCqYh_MT8Rq7xLK_Fd7HlbKltDAkishfw"
api_key_evalation_c3 = "AIzaSyCqyEldy-NXQpsyOih5uTX6bwYGGGim8Oo"
api_key_evalation_c4 = "AIzaSyA9xG0hj9wNkhThQcxuteGnjXAZU01EMmE"
api_key_evalation_a1 = "AIzaSyBK0y56i-73FWQwZwY3zbemPMi2cdM8NAc"
api_key_evalation_a2 = "AIzaSyAMksbgaSpzHy3vVZdQqhd_Ju1xmuvKebA"
api_key_evalation_a3 = "AIzaSyCruy-qmmb4BcOvEDC_1JmU4y0ActNOiG0"

# for geocoding
api_key_geocoding_c1 = "AIzaSyAy3BBdz9xEUr2RRowvhIvaVO80BIKOlkI"
api_key_geocoding_c2 = "AIzaSyAHdxk7COSuHx3FbVlUuqdMy8FkP2Yyr6Q"
api_key_geocoding_c3 = "AIzaSyDeUo-QAmUKze0rvURLczLC1wYSIDZj2a0"
api_key_geocoding_c4 = "AIzaSyD4Kl8a9OeFbT4_ZbEAT7pELthLO8wWE-k"
api_key_geocoding_a1 = "AIzaSyDJGg8dyRIjlz6A28-yN8qK-dj81IhDWHM"
api_key_geocoding_a2 = "AIzaSyBNDoNTjtRPS6Q9JtQSAPDbmpSxzWBt0iE"
api_key_geocoding_a3 = "AIzaSyCYqmtpYc8zAAW-UZsp1dQ976A_DJXVbhM"

gmaps = googlemaps.Client(key=api_key)

# set evalation high
evalation_high = 100
evalation_url = "https://maps.googleapis.com/maps/api/elevation/json?locations={},{}&key={}"
geocoding_url_ROOFTOP = "https://maps.googleapis.com/maps/api/geocode/json?latlng={},{}&location_type=ROOFTOP&key={}"
geocoding_url_GEOMETRIC_CENTER = "https://maps.googleapis.com/maps/api/geocode/json?latlng={},{}&location_type=GEOMETRIC_CENTER&key={}"

# detect for robot
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

# ========================================================

# find specific person
def find_person(x,y):

    global main_pool

    for key,value in main_pool.items():
        if str(value["x"]) == str(x) and str(value["y"]) == str(y):
            return key
        else :
            pass

# ========================================================

# add person to exsisted room
def add_people(room_key,current_person_key,straight_distance):
    
    # define some variables
    global main_pool
    surprise,circle1,circle2,circle3,circle4 = str(),dict(),dict(),dict(),dict()
    other_people_list = list()
    player_data = dict()

    other_people = running_app_db.child("running_room").child(room_key).child("經緯度").get().each()
    for others in other_people :
        other_people_list.append(others.key())

    running_app_db.child("running_room").child(room_key).child("經緯度").update({current_person_key : 
                                                                                    {
                                                                                        "x" : main_pool[current_person_key]["x"],
                                                                                        "y" : main_pool[current_person_key]["y"]
                                                                                    }
                                                                                })

    room_data = running_app_db.child("running_room").child(room_key).get().each()

    for data in room_data:
        if data.key() == "空投":
            surprise = data.val()
        elif  data.key() == "第一圈圓心":
            circle1 = data.val()
        elif  data.key() == "第二圈圓心":
            circle2 = data.val()
        elif  data.key() == "第三圈圓心":
            circle3 = data.val()
        elif  data.key() == "第四圈圓心":
            circle4 = data.val()

    players_data_get = running_app_db.child("members").get().each()

    for data in players_data_get :
        if data.key() in other_people_list :
            player_data[data.key()] = dict()
            for key,value in data.val().items():
                if key == "email" or key == "password" or key == "average_time" or key == "total_count" or key == "total_distance(km)" or key == "total_time":
                    pass
                else :
                    player_data[data.key()][key] = value

    update_personal_data = {
        current_person_key : { 
            "average_time" : 0,
            "total_distance(km)" : 0,
            "total_time" : 0,
            "房間" : room_key,
            "房間狀態" : "不正常狀況",
            "最遠直線距離" : straight_distance,
            "空投" : surprise,
            "第一圈圓心" : circle1,
            "第二圈圓心" : circle2,
            "第三圈圓心" : circle3,
            "第四圈圓心" : circle4,
            "跑友" : player_data
        }
    }

    running_app_db.child("running_player").update(update_personal_data)

    return other_people_list

# ========================================================

# update other players' info
def update_all_players(other_people,current_person_key):
    
    # define some variables
    current_player_upload = dict()

    current_person_data = running_app_db.child("members").get().each()

    for data in current_person_data :
        if data.key() == current_person_key :
            current_player_upload[data.key()] = dict()
            for key,value in data.val().items():
                if key == "email" or key == "password" or key == "average_time" or key == "total_count" or key == "total_distance(km)" or key == "total_time":
                    pass
                else :
                    current_player_upload[data.key()][key] = value
    
    for i in range(len(other_people)) :
        running_app_db.child("running_player").child(other_people[i]).child("跑友").update(current_player_upload)
        
# ========================================================

# check distance for each player for each room
def check_distance_whenadd(room_key,main_pool_list,last_circle,available_player):

    # define some varibles
    global far_person_add_km
    global main_pool
    main_pool_list_rep = main_pool_list
    for i in range(len(main_pool_list_rep)):
        if available_player <= 0 :
            break
        else :
            straight_distance = geodesic((float(main_pool_list_rep[i][1]),float(main_pool_list_rep[i][0])), (float(last_circle["y"]),float(last_circle["x"]))).km
            if straight_distance <= far_person_add_km and available_player >= 0:
                current_person_key = find_person(main_pool_list_rep[i][0],main_pool_list_rep[i][1])
                other_people = add_people(room_key,current_person_key,straight_distance)
                update_all_players(other_people,current_person_key)
                available_player = available_player - 1
                main_pool_list.remove([main_pool_list_rep[i][0],main_pool_list_rep[i][1]])
                del main_pool[current_person_key]
            else :
                pass

    return available_player , main_pool_list

# ========================================================

# update abnormal to normal
def update_to_normal(room_key):
    
    # define variable
    all_player_list = list() 
    all_player = running_app_db.child("running_room").child(room_key).child("經緯度").get().each()
    for player in all_player:
        all_player_list.append(player.key())

    for i in range(len(all_player_list)):
        running_app_db.child("running_player").child(all_player_list[i]).update({"房間狀態" :"正常狀況"})

# ========================================================

# check each room's situation and insert possible player
def check_room_and_insert(main_pool_list) :
    
    # define global 
    global running_app_db
    available_player = int()
    abnormal_room = running_app_db.child("running_room").get().each()
    
    if abnormal_room != None:
        for abnormal_room_status in abnormal_room :
            remain_data = abnormal_room_status.val()
            print("=== Current room's status is {}".format(remain_data["狀態"]))
            if remain_data["狀態"] == "不正常狀況":
                current_player = len(remain_data["經緯度"])
                available_player = 6 - int(current_player)
                available_player , main_pool_list = check_distance_whenadd(abnormal_room_status.key(),main_pool_list,remain_data["第四圈圓心"],available_player)
                print("=== check before cluster !!!!!!!!!!!!!!! ===")
                current_room_player_count = len(running_app_db.child("running_room").child(abnormal_room_status.key()).get().val())
                if available_player == 6-current_player or current_room_player_count < 3:
                    print("=== 不正常狀況 ===")
                    pass
                else :
                    print("=== 正常狀況 ===")
                    running_app_db.child("running_room").child(abnormal_room_status.key()).update({"狀態":"正常狀況"})
                    update_to_normal(abnormal_room_status.key())
            else :
                pass
    else :
        pass

    return main_pool_list

# ========================================================

# store in db
def store_in_db_and_clean():
    
    currernt_room = list()
    global room
    global players

    print("=== cluster start ===")
    print("printing room...")
    print(room)
    print("printing players...")
    print(players)
    print("=== cluster end ===")

    all_rooms = running_app_db.child("running_room").get()
    all_player = running_app_db.child("running_player").get()

    if all_rooms.each() == None:
        running_app_db.child("running_room").set(room)
        running_app_db.child("running_player").set(players)
    else :
        running_app_db.child("running_room").update(room)
        running_app_db.child("running_player").update(players)

    # back to empty
    room = dict()
    players = dict()

# ========================================================

# clustering main 
def circle_clustering(pool_list):
    # define clustering parameters
    
    global kms_per_radian
    global epsilon
    global main_pool_status

    db = DBSCAN(eps=epsilon, min_samples=3, algorithm='ball_tree', metric='haversine').fit(np.radians(np.array(pool_list)))
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels))
    clusters = pd.Series([np.array(main_pool_list)[cluster_labels == n] for n in range(num_clusters)])

    seperate_room(cluster_labels,num_clusters,clusters)

# ========================================================    

# check points whether in river or some other place
def check_point_place(y,x,api_key):
    
    # set up variable
    global gmaps,geocoding_url_ROOFTOP,geocoding_url_GEOMETRIC_CENTER,headers

    # get location from google
    # reverse_geocode_result_first = gmaps.reverse_geocode(latlng=(y, x),location_type="ROOFTOP")
    # reverse_geocode_result_second = gmaps.reverse_geocode(latlng=(y, x),location_type="GEOMETRIC_CENTER")

    with urllib.request.urlopen(Request(geocoding_url_ROOFTOP.format(y,x,api_key), headers=headers)) as f:
        reverse_geocode_result_first = json.loads(f.read().decode())["results"]

    with urllib.request.urlopen(Request(geocoding_url_GEOMETRIC_CENTER.format(y,x,api_key), headers=headers)) as f:
        reverse_geocode_result_second = json.loads(f.read().decode())["results"]

    # return status and x , y
    if reverse_geocode_result_first == [] and reverse_geocode_result_second == [] :
        return 0,y,x
    elif reverse_geocode_result_first != [] and reverse_geocode_result_second == [] :
        y = float(reverse_geocode_result_first[0]["geometry"]["location"]["lat"])
        x = float(reverse_geocode_result_first[0]["geometry"]["location"]["lng"])
        return 1,x,y
    elif reverse_geocode_result_first == [] and reverse_geocode_result_second != [] :
        y = float(reverse_geocode_result_second[0]["geometry"]["location"]["lat"])
        x = float(reverse_geocode_result_second[0]["geometry"]["location"]["lng"])
        return 1,x,y
    elif reverse_geocode_result_first != [] and reverse_geocode_result_second != [] :
        y = float(reverse_geocode_result_first[0]["geometry"]["location"]["lat"])
        x = float(reverse_geocode_result_first[0]["geometry"]["location"]["lng"])
        return 1,x,y

# check distance finally when clustering
def check_distance_during_cluster(before_y,before_x,after_y,after_x,distance) :
    
    straight_distance = geodesic((float(before_y),float(before_x)), (float(after_y),float(after_x))).km
    if straight_distance <= distance :
        return 0
    else :
        return 1

# check hight
def check_evalation(each_cluster,y,x,api_key):
    
    # set variable
    global gmaps,evalation_high,status,evalation_url,headers
    status = 0

    # print(y)
    # print(x)
    # elevation_point_result = gmaps.elevation(locations=(y, x))
    # print(elevation_point_result)

    with urllib.request.urlopen(Request(evalation_url.format(y,x,api_key), headers=headers)) as f:
        elevation_point_result = json.loads(f.read().decode())["results"]

    for i in range(len(each_cluster)):
        
        # print(each_cluster[i][1])

        # print(each_cluster[i][0])

        # elevation_each_result = gmaps.elevation(locations=(each_cluster[i][1], each_cluster[i][0]))

        with urllib.request.urlopen(Request(evalation_url.format(each_cluster[i][1],each_cluster[i][0],api_key), headers=headers)) as f:
            elevation_each_result = json.loads(f.read().decode())["results"]

        if ( abs( (elevation_point_result[0]["elevation"] - elevation_each_result[0]["elevation"]) < evalation_high ) ):
            status = 1
        else :
            status = 0
            break
        
    return status

# circle center
def center_circle(each_cluster) :
    
    global average_earth_radius, d_center1, d_center2, d_center3
    global status_check_c1, status_check_c2, status_check_c3, status_check_c4
    global status_high_c1, status_high_c2, status_high_c3, status_high_c4
    global status_check_a1, status_check_a2, status_check_a3, status_check_a4
    global status_high_a1, status_high_a2, status_high_a3, status_high_a4
    status_check_c1, status_check_c2, status_check_c3, status_check_c4 = 0,0,0,0
    status_high_c1, status_high_c2, status_high_c3, status_high_c4 = 0,0,0,0
    status_check_a1, status_check_a2, status_check_a3, status_check_a4 = 0,0,0,0
    status_high_a1, status_high_a2, status_high_a3, status_high_a4 = 0,0,0,0
    
    # get c1 center and random different angle
    # while(status_check_c1 == 0 and status_high_c1 == 0):
    #     random_angle_c1 = math.radians(random.uniform(0,360))
    #     random_angle_c2 = math.radians(random.uniform(0,360))
    #     random_angle_c3 = math.radians(random.uniform(0,360))
    #     c1_center = each_cluster.mean(axis=0)

    #     # check status
    #     status_check_c1,c1_center[0],c1_center[1] = check_point_place(c1_center[1],c1_center[0],api_key_geocoding_c1)

    #     # check high
    #     status_high_c1 = check_evalation(each_cluster,c1_center[1],c1_center[0],api_key_evalation_c1)

    random_angle_c1 = math.radians(random.uniform(0,360))
    random_angle_c2 = math.radians(random.uniform(0,360))
    random_angle_c3 = math.radians(random.uniform(0,360))
    c1_center = each_cluster.mean(axis=0)

    
    # # create c1 center lat/long
    # while(status_check_c2 == 0 and status_high_c2 == 0):
    #     L1 = random.uniform(0,d_center1) 
    #     c2y = math.asin( math.sin( math.radians(c1_center[1]) ) * math.cos( L1/average_earth_radius ) + math.cos( math.radians(c1_center[1]) ) * math.sin( L1/average_earth_radius ) * math.cos(random_angle_c1) )
    #     c2x = math.radians( c1_center[0] ) + math.atan2( math.sin( random_angle_c1 ) * math.sin( L1/average_earth_radius ) * math.cos( math.radians( c1_center[1]) ), math.cos( L1/average_earth_radius ) - math.sin( math.radians( c1_center[1]) ) * math.sin(c2y) )
    #     c2x = math.degrees(c2x)
    #     c2y = math.degrees(c2y)

    #     # check status
    #     status_check_c2,c2x,c2y = check_point_place(c2y,c2x,api_key_geocoding_c2)

    #     # check high
    #     status_high_c2 = check_evalation(each_cluster,c2y,c2x,api_key_evalation_c2)

    #     if status_high_c2 == 0 or status_check_c2 == 0:
    #         pass
    #     else :
    #         final_status = check_distance_during_cluster(c1_center[1],c1_center[0],c2y,c2x,d_center1)
    #         if final_status == 1 :
    #             status_check_c2 = 0
    #             status_high_c2 = 0
    #         else :
    #             pass
    
    L1 = random.uniform(0,d_center1) 
    c2y = math.asin( math.sin( math.radians(c1_center[1]) ) * math.cos( L1/average_earth_radius ) + math.cos( math.radians(c1_center[1]) ) * math.sin( L1/average_earth_radius ) * math.cos(random_angle_c1) )
    c2x = math.radians( c1_center[0] ) + math.atan2( math.sin( random_angle_c1 ) * math.sin( L1/average_earth_radius ) * math.cos( math.radians( c1_center[1]) ), math.cos( L1/average_earth_radius ) - math.sin( math.radians( c1_center[1]) ) * math.sin(c2y) )
    c2x = math.degrees(c2x)
    c2y = math.degrees(c2y)

    # # create c2 center lat/long
    # while(status_check_c3 == 0 and status_high_c3 == 0):
    #     L2 = random.uniform(0,d_center2)
    #     c3y = math.asin( math.sin( math.radians(c2y) ) * math.cos( L2/average_earth_radius ) + math.cos( math.radians(c2y) ) * math.sin( L2/average_earth_radius ) * math.cos( random_angle_c2 ) )
    #     c3x = math.radians( c2x ) + math.atan2( math.sin( random_angle_c2 ) * math.sin( L2/average_earth_radius ) * math.cos( math.radians( c2y ) ), math.cos( L2/average_earth_radius ) - math.sin( math.radians( c2y ) ) * math.sin( c3y ) )
    #     c3x = math.degrees(c3x)
    #     c3y = math.degrees(c3y)

    #     # check status
    #     status_check_c3,c3x,c3y = check_point_place(c3y,c3x,api_key_geocoding_c3)

    #     # check high
    #     status_high_c3 = check_evalation(each_cluster,c3y,c3x,api_key_evalation_c3)

    #     if status_high_c3 == 0 or status_check_c3 == 0:
    #         pass
    #     else :
    #         final_status = check_distance_during_cluster(c2y,c2x,c3y,c3x,d_center2)
    #         if final_status == 1 :
    #             status_check_c3 = 0
    #             status_high_c3 = 0
    #         else :
    #             pass

    L2 = random.uniform(0,d_center2)
    c3y = math.asin( math.sin( math.radians(c2y) ) * math.cos( L2/average_earth_radius ) + math.cos( math.radians(c2y) ) * math.sin( L2/average_earth_radius ) * math.cos( random_angle_c2 ) )
    c3x = math.radians( c2x ) + math.atan2( math.sin( random_angle_c2 ) * math.sin( L2/average_earth_radius ) * math.cos( math.radians( c2y ) ), math.cos( L2/average_earth_radius ) - math.sin( math.radians( c2y ) ) * math.sin( c3y ) )
    c3x = math.degrees(c3x)
    c3y = math.degrees(c3y)

    # # create c3 center lat/long
    # while(status_check_c4 == 0 and status_high_c4 == 0):
    #     L3 = random.uniform(0,d_center3)
    #     c4y = math.asin( math.sin( math.radians(c3y) ) * math.cos( L3/average_earth_radius ) + math.cos(math.radians( c3y ) ) * math.sin( L3/average_earth_radius ) * math.cos( random_angle_c3 ) )
    #     c4x = math.radians( c3x ) + math.atan2( math.sin( random_angle_c3 ) * math.sin( L3/average_earth_radius ) * math.cos( math.radians( c3y ) ), math.cos( L3/average_earth_radius ) - math.sin( math.radians( c3y ) ) * math.sin(c4y) )
    #     c4x = math.degrees(c4x)
    #     c4y = math.degrees(c4y)

    #     # check status
    #     status_check_c4,c4x,c4y = check_point_place(c4y,c4x,api_key_geocoding_c4)

    #     # check high
    #     status_high_c4 = check_evalation(each_cluster,c4y,c4x,api_key_evalation_c4)

    #     if status_high_c4 == 0 or status_check_c4 == 0:
    #         pass
    #     else :
    #         final_status = check_distance_during_cluster(c3y,c3x,c4y,c4x,d_center3)
    #         if final_status == 1 :
    #             status_check_c4 = 0
    #             status_high_c4 = 0
    #         else :
    #             pass
    
    L3 = random.uniform(0,d_center3)
    c4y = math.asin( math.sin( math.radians(c3y) ) * math.cos( L3/average_earth_radius ) + math.cos(math.radians( c3y ) ) * math.sin( L3/average_earth_radius ) * math.cos( random_angle_c3 ) )
    c4x = math.radians( c3x ) + math.atan2( math.sin( random_angle_c3 ) * math.sin( L3/average_earth_radius ) * math.cos( math.radians( c3y ) ), math.cos( L3/average_earth_radius ) - math.sin( math.radians( c3y ) ) * math.sin(c4y) )
    c4x = math.degrees(c4x)
    c4y = math.degrees(c4y)

    # # 空頭 a1
    # while(status_check_a1 == 0 and status_high_a1 == 0):
    #     random_angle_a1 = math.radians( random.uniform(0,360) ) #角度 0~360
    #     a1y = math.asin( math.sin( math.radians( c1_center[1]) ) * math.cos( L1/average_earth_radius ) + math.cos( math.radians(c1_center[1]) ) * math.sin( L1/average_earth_radius ) * math.cos(random_angle_a1))
    #     a1x = math.radians(c1_center[0]) + math.atan2(math.sin( random_angle_a1 ) * math.sin( L1/average_earth_radius)  * math.cos( math.radians(c1_center[1]) ), math.cos( L1/average_earth_radius ) - math.sin( math.radians(c1_center[1]) ) * math.sin(a1y))
    #     a1x = math.degrees(a1x)
    #     a1y = math.degrees(a1y)

    #     # check status
    #     status_check_a1,a1x,a1y = check_point_place(a1y,a1x,api_key_geocoding_a1)

    #     # check high
    #     status_high_a1 = check_evalation(each_cluster,a1y,a1x,api_key_evalation_a1)

    #     if status_high_a1 == 0 or status_check_a1 == 0:
    #         pass
    #     else :
    #         final_status = check_distance_during_cluster(c1_center[1],c1_center[0],a1y,a1x,d_center1)
    #         if final_status == 1 :
    #             status_check_a1 = 0
    #             status_high_a1 = 0 
    #         else :
    #             pass

    random_angle_a1 = math.radians( random.uniform(0,360) ) #角度 0~360
    a1y = math.asin( math.sin( math.radians( c1_center[1]) ) * math.cos( L1/average_earth_radius ) + math.cos( math.radians(c1_center[1]) ) * math.sin( L1/average_earth_radius ) * math.cos(random_angle_a1))
    a1x = math.radians(c1_center[0]) + math.atan2(math.sin( random_angle_a1 ) * math.sin( L1/average_earth_radius)  * math.cos( math.radians(c1_center[1]) ), math.cos( L1/average_earth_radius ) - math.sin( math.radians(c1_center[1]) ) * math.sin(a1y))
    a1x = math.degrees(a1x)
    a1y = math.degrees(a1y)
            
         
    # # 空頭 a2
    # while(status_check_a2 == 0 and status_high_a2 == 0):
    #     random_angle_a2 = math.radians(random.uniform(0,360)) #角度 0~360
    #     a2y = math.asin( math.sin( math.radians(c2y) ) * math.cos( L2/average_earth_radius) + math.cos( math.radians(c2y) ) * math.sin( L2/average_earth_radius ) * math.cos( random_angle_a2 ))
    #     a2x = math.radians(c2x) + math.atan2(math.sin( random_angle_a2 ) * math.sin( L2/average_earth_radius ) * math.cos( math.radians(c2y) ), math.cos( L2/average_earth_radius ) - math.sin( math.radians(c2y) ) * math.sin(c3y) )
    #     a2x = math.degrees(a2x)
    #     a2y = math.degrees(a2y)

    #     # check status
    #     status_check_a2,a2x,a2y = check_point_place(a2y,a2x,api_key_geocoding_a2)

    #     # check high
    #     status_high_a2 = check_evalation(each_cluster,a2y,a2x,api_key_evalation_a2)

    #     if status_high_a2 == 0 or status_check_a2 == 0:
    #         pass
    #     else :
    #         final_status = check_distance_during_cluster(c2y,c2x,a2y,a2x,d_center2)
    #         if final_status == 1 :
    #             status_check_a2 = 0
    #             status_high_a2 = 0
    #         else :
    #             pass
            
    random_angle_a2 = math.radians(random.uniform(0,360)) #角度 0~360
    a2y = math.asin( math.sin( math.radians(c2y) ) * math.cos( L2/average_earth_radius) + math.cos( math.radians(c2y) ) * math.sin( L2/average_earth_radius ) * math.cos( random_angle_a2 ))
    a2x = math.radians(c2x) + math.atan2(math.sin( random_angle_a2 ) * math.sin( L2/average_earth_radius ) * math.cos( math.radians(c2y) ), math.cos( L2/average_earth_radius ) - math.sin( math.radians(c2y) ) * math.sin(c3y) )
    a2x = math.degrees(a2x)
    a2y = math.degrees(a2y)

    # # 空頭 a3
    # while(status_check_a3 == 0 and status_high_a3 == 0):
    #     random_angle_a3 = math.radians(random.uniform(0,360)) #角度 0~360
    #     a3y = math.asin( math.sin( math.radians(c3y) ) * math.cos( L2/average_earth_radius ) + math.cos( math.radians(c3y) ) * math.sin( L2/average_earth_radius ) * math.cos(random_angle_a3))
    #     a3x = math.radians(c3x) + math.atan2( math.sin(random_angle_a3) * math.sin( L3/average_earth_radius ) * math.cos( math.radians(c3y) ), math.cos( L3/average_earth_radius ) - math.sin( math.radians(c3y) ) * math.sin(c4y) )
    #     a3x = math.degrees(a3x)
    #     a3y = math.degrees(a3y)

    #     # check status
    #     status_check_a3,a3x,a3y = check_point_place(a3y,a3x,api_key_geocoding_a3)

    #     # check high
    #     status_high_a3 = check_evalation(each_cluster,a3y,a3x,api_key_evalation_a3)

    #     if status_high_a3 == 0 or status_check_a3 == 0:
    #         pass
    #     else :
    #         final_status = check_distance_during_cluster(c3y,c3x,a3y,a3x,d_center3)
    #         if final_status == 1 :
    #             status_check_a3 = 0
    #             status_high_a3 = 0  
    #         else :
    #             pass

    random_angle_a3 = math.radians(random.uniform(0,360)) #角度 0~360
    a3y = math.asin( math.sin( math.radians(c3y) ) * math.cos( L2/average_earth_radius ) + math.cos( math.radians(c3y) ) * math.sin( L2/average_earth_radius ) * math.cos(random_angle_a3))
    a3x = math.radians(c3x) + math.atan2( math.sin(random_angle_a3) * math.sin( L3/average_earth_radius ) * math.cos( math.radians(c3y) ), math.cos( L3/average_earth_radius ) - math.sin( math.radians(c3y) ) * math.sin(c4y) )
    a3x = math.degrees(a3x)
    a3y = math.degrees(a3y)

    return c1_center , np.array([c2x,c2y]) , np.array([c3x,c3y]) , np.array([c4x,c4y]) , np.array([a1x,a1y]) , np.array([a2x,a2y]) , np.array([a3x,a3y])

# ========================================================

# find and return members
def find_members(room_data) :
    
    global main_pool
    players_key_each_room = list()

    for i in range(len(room_data)) :
        for key,value in main_pool.items() :
            if int(room_data[i][0]) == int(value["x"]) and int(room_data[i][1]) == int(value["y"]) and key not in players_key_each_room:
                players_key_each_room.append(key)
                break
            else :
                pass

    # print(players_key_each_room)
    return players_key_each_room

# ========================================================

# insert for each players
def insert_players(room_id,players_key_each_room,c1_center,c2_center,c3_center,c4_center,gift_data):
    
    global players
    global main_pool

    members_data = running_app_db.child("members").get()

    for i in range(len(players_key_each_room)) :
        players[players_key_each_room[i]] = dict()
        players[players_key_each_room[i]]["房間"] = room_id
        players[players_key_each_room[i]]["第一圈圓心"] = {
            "x" : c1_center[0],
            "y" : c1_center[1]
        }
        players[players_key_each_room[i]]["第二圈圓心"] = {
            "x" : c2_center[0],
            "y" : c2_center[1]
        }
        players[players_key_each_room[i]]["第三圈圓心"] = {
            "x" : c3_center[0],
            "y" : c3_center[1]
        }
        players[players_key_each_room[i]]["第四圈圓心"] = {
            "x" : c4_center[0],
            "y" : c4_center[1]
        }
        players[players_key_each_room[i]]["空投"] = gift_data

        # some running data for each run
        players[players_key_each_room[i]]["total_distance(km)"] = 0
        players[players_key_each_room[i]]["average_time"] = 0
        players[players_key_each_room[i]]["total_time"] = 0
        players[players_key_each_room[i]]["房間狀態"] = "正常狀況"

        # compute distance between first place and last place
        firstplace = (float(main_pool[players_key_each_room[i]]["y"]),float(main_pool[players_key_each_room[i]]["x"]))
        lastplace = (float(c4_center[1]),float(c4_center[0]))
        straight_distance = geodesic(firstplace, lastplace).km
        players[players_key_each_room[i]]["最遠直線距離"] = straight_distance

        players[players_key_each_room[i]]["跑友"] = dict()
        for x in range(len(players_key_each_room)) :
            if players_key_each_room[i] == players_key_each_room[x] :
                pass
            else :
                players[players_key_each_room[i]]["跑友"][players_key_each_room[x]] = dict()
                for data in members_data.each() :
                    if data.key() == players_key_each_room[x] :
                        for data_key,data_value in data.val().items() :
                            if data_key == "email" or data_key == "password" or data_key == "average_time" or data_key == "total_count" or data_key == "total_distance(km)" or data_key == "total_time":
                                pass
                            else :
                                players[players_key_each_room[i]]["跑友"][players_key_each_room[x]][data_key] = data_value

        # players[players_key_each_room[i]]["跑友"]
    for y in range(len(players_key_each_room)) :
        del main_pool[players_key_each_room[y]]

# ========================================================

# convert room data : ndarrary to json
def room_data_convert(room_data , players_key_each_room) :
    
    room_dict = dict()
    print(players_key_each_room)
    for i in range(len(room_data)) :
        print(room_data)
        room_dict[players_key_each_room[i]] = {
            "x" : room_data[i][0],
            "y" : room_data[i][1]
        }

    return room_dict

# ========================================================

# create dict for gift each room
def create_gift(gift_1,gift_2,gift_3,gift,room_id):
    
    global storage
    gift_data = dict()
    gift_list = list()
    gift_url = list()
    random_choice_1 = random.randint(0,4)
    random_choice_2 = random.randint(0,4)
    random_choice_3 = random.randint(0,4)
    gift_1_detail = gift[random_choice_1]
    gift_2_detail = gift[random_choice_2]
    gift_3_detail = gift[random_choice_3]
    gift_list = [gift_1_detail,gift_2_detail,gift_3_detail]

    for i in range(len(gift_list)) :
        # set up qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.make(fit=True)
        qr.add_data({
            "gift" : gift_list[i]
        })
        img = qr.make_image()
        img.save("airdrops.png")
        url = storage.child("airdrops/"+str(room_id)+"/airdrops_"+ str(i+1)).put("airdrops.png")
        gift_url.append("https://firebasestorage.googleapis.com/v0/b/running-mate-7bb1b.appspot.com/o/airdrops%2F"+str(room_id)+"%2Fairdrops_" + str(i+1) +"?alt=media&token=" + str(url['downloadTokens']))
        sleep(1)
        
    gift_data = {
        "first" : {
            "x" : gift_1[0],
            "y" : gift_1[1],
            "gift" : gift_1_detail,
            "status" : 0,
            "airdrops_url" : gift_url[0]
        },
        "second" : {
            "x" : gift_2[0],
            "y" : gift_2[1],
            "gift" : gift_2_detail,
            "status" :  0,
            "airdrops_url" : gift_url[1]
        },
        "third" : {
            "x" : gift_3[0],
            "y" : gift_3[1],
            "gift" : gift_3_detail,
            "status" : 0,
            "airdrops_url" : gift_url[2]
        }
    }

    return gift_data

# ========================================================

# insert room data
def insert_room_data(room_data) :
    
    global room
    global main_pool
    global gift

    room_id = str(uuid.uuid1())
    room[room_id] = dict()
    c1_center , c2_center , c3_center ,c4_center , gift_1 , gift_2 , gift_3 = center_circle(room_data)
    players_key_each_room = find_members(room_data)
    room_data_dict = room_data_convert(room_data , players_key_each_room)
    room[room_id]["經緯度"] = room_data_dict
    room[room_id]["狀態"] = "正常"
    room[room_id]["第一圈圓心"] = {
            "x" : c1_center[0],
            "y" : c1_center[1]
        }
    room[room_id]["第二圈圓心"] = {
            "x" : c2_center[0],
            "y" : c2_center[1]
        }
    room[room_id]["第三圈圓心"] = {
            "x" : c3_center[0],
            "y" : c3_center[1]
        }
    room[room_id]["第四圈圓心"] = {
            "x" : c4_center[0],
            "y" : c4_center[1]
        }
    gift_data = create_gift(gift_1,gift_2,gift_3,gift,room_id)
    room[room_id]["空投"] = gift_data
    insert_players(room_id,players_key_each_room,c1_center,c2_center,c3_center,c4_center,gift_data)

# ========================================================

# cluster_data is a list
def room_create(cluster_data) :
    if isinstance(cluster_data, list):
        for i in range(len(cluster_data)):
            insert_room_data(cluster_data[i])
    else :
        insert_room_data(cluster_data)

# ========================================================

# seperate data to each room
def seperate_room(cluster_labels,num_clusters,clusters) :
    
    for i in range(num_clusters) : 
        clusters[i] = sorted(clusters[i] , key=lambda k: [k[1], k[0]])
        clusters[i] = np.asarray(clusters[i])
        if clusters[i].shape[0] == 0 :
            pass
        elif clusters[i].shape[0] > 6 :
            for x in range(6,3,-1):
                room_len_least = (np.array_split(clusters[i], clusters[i].shape[0]/x, 0)[-1]).shape[0]
                if room_len_least >= 3:
                    room_create(np.array_split(clusters[i], clusters[i].shape[0]/x, 0))
                    break
                else :
                    pass
        else:
            room_create((clusters[i]))

# check member in mainpool
def check_member_in_mainpool(id_key) :
    
    global main_pool
    if id_key in main_pool.keys() :
        return 1

    else :
        return 0

# ========================================================

# delete from left pool
@app.task(queue="delete_person")
def delete_person(id_key,status):
    
    global running_app_db
    global main_pool
    global left_pool
    global main_pool_status
    if id_key not in left_pool.keys() and id_key not in main_pool.keys():
        pass
    elif id_key not in left_pool.keys() and id_key in main_pool.keys():
        del main_pool[id_key]
        pass
    elif id_key in left_pool.keys() and id_key not in main_pool.keys():
        del left_pool[id_key]
        pass
    elif id_key in left_pool.keys() and id_key in main_pool.keys():
        del main_pool[id_key]
        del left_pool[id_key]
        pass
    else :
        pass

    if status == 2:
        players = running_app_db.child("running_player").get().each()
        
        if players == None :
            pass
        else :
            current_player = running_app_db.child("running_player").child(id_key).get()
            
            if current_player.each() != None :
                
                player_room = current_player.val()["房間"]
                running_app_db.child("running_room").child(player_room).child("經緯度").child(id_key).remove()
                running_app_db.child("running_player").child(id_key).remove()

            else :
                pass

# ========================================================

# put data in pool
@app.task(queue="put_data")
def put_data(x,y,id_key):
    global main_pool
    global left_pool
    global main_pool_status
    status = check_member_in_mainpool(id_key)
    if status == 0 :
        if main_pool_status == 0 :
            print("putting in main pool ...")
            if len(left_pool) > 0:
                main_pool.update(left_pool)
                left_pool = dict()

            main_pool.update(left_pool)
            main_pool[id_key] = dict()
            main_pool[id_key]["x"] = x
            main_pool[id_key]["y"] = y
        else :
            print("putting in left pool ...")
            left_pool[id_key] = dict()
            left_pool[id_key]["x"] = x
            left_pool[id_key]["y"] = y
    else :
        pass

    return "success enter put_data"

# ========================================================

# retrieve data (x,y) from each user
@app.task(name = "cluster")
def retrieve_user_data() :
    # define some variables
    global main_pool_list
    global main_pool_status
    global main_pool
    global left_pool
    global room
    global players
    
    if len(main_pool) != 0 :

        # make main pool status to 1
        main_pool_status = 1

        # put some each players' x , y to main pool
        for key, value in main_pool.items() :
            main_pool_list.append([value["x"],value["y"]])

        print("=== begin main pool data : ===")
        print(main_pool)
        print("=== === === === === === ===")
        
        # check each room's status and put new members into those rooms
        main_pool_list = check_room_and_insert(main_pool_list)

        # start to cluster after checking (which data is randomly seperate)

        # ==============  not  =========  done  =============  yet  ======================================#

        # cluster for other diemension data (not done yet)
        # special_cluster = kmeans(main_pool_list)

        # cluster special data for distance
        # circle_clustering(special_cluster)

        # store special data in firebase
        # store_in_db_and_clean(room,players)

        # check for other players without special cluster
        # main_pool_list = check_after_special_cluster(special_room,main_pool_list)

        # ==============  not  =========  done  =============  yet  ======================================#

        # cluster normal data for distance
        circle_clustering(main_pool_list)

        print("=== over main pool data : ===")
        print(main_pool)
        print("=== === === === === === ===")

        # clean main pool list
        main_pool_list = list()

        # store normal data in firebase
        store_in_db_and_clean()

        # change the main pool status to 0
        main_pool_status = 0

        return "success cluserting to each room !!"

    else :
        return "no players !!"
    
    