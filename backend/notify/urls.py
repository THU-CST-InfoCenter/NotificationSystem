"""scholarship URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import path
from dbapp import views

urlpatterns = [
    path('userLogin', views.userLogin),
    path('adminLogin', views.adminLogin),
    path('createStudentAccounts', views.createStudentAccounts)
    ## for debug purpose
    path('debugCheckers', views.debugCheckers),
    ## DB settings
    path('getDBList', views.getDBList),
    path('addDB', views.addDB),
    path('getDB', views.getDB),
    path('delDB', views.delDB),
    path('editDB', views.editDB),
    ## put/get variables (for admin only)
    path('putVariable', views.putVariable),
    path('getVariable', views.getVariable),
    ## Group settings
    path('getGroupList', views.getGroupList),
    path('addGroup', views.addGroup),
    path('delGroup', views.delGroup),
    path('editGroup', views.editGroup),
    path('getCurrentDBId', views.getCurrentDBId),
    path('getCurrentSystemTitle', views.getCurrentSystemTitle)
]
