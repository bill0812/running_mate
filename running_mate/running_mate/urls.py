"""running_mate URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from runningmate_app import views
from django.conf.urls import include

urlpatterns = [
    path('admin/', admin.site.urls),

    # get in app and check if session exsis  (ok
    path('check_session/',views.check_session),

    # logout  (ok 
    path('logout/',views.logout),

    # new account to register  (ok
    path('register_member/',views.register_member),

    # when exsisting member login  (ok
    path('login_member/',views.login_member),

    # update personal data  (ok
    path('update_member/',views.update_member),

    # when game cancel normally, add data to firebase
    path('add_to_history/',views.add_to_history),

    # get response, and check game started(yes or no)
    path('start_game_cancel/',views.start_game_cancel),

    # check and update data if players cnacel durring games
    path('during_game_cancel/',views.durring_game_cancel),

    # circle cluster for players  (ok
    path('circle/',views.circle_cluster, name = 'circle'),

    # the person really dont be in cluster
    path('delete_from_main_pool/',views.delete_from_main_pool),

    # search for each ranking
    path('add_to_friend/',views.add_to_friend),

    # app terminate
    path('app_terminate/',views.app_terminate),

    # change airdrops status each room
    path('change_airdrops/',views.change_airdrops)

    # return some problems
    # path('return_problems/',views.return_problems),

    # use airdrops
    # path('use_airdrops/',views.return_problems),

    # update friend status
    # path('update_friend_status/',view.update_friend_status)
]
