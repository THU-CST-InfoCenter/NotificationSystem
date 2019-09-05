from functools import wraps
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.core import serializers
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from django.core.paginator import Paginator
from dbapp import models
import requests
import xlrd
import urllib
from django.utils.timezone import utc
import urllib.parse
import json
from config import *
import uuid
import sys
import datetime
import hashlib
import os
sys.path.append('../')


def createToken(user):
    # update token if already exists
    token = str(uuid.uuid4())
    models.SessionToken.objects.update_or_create(user=user,
                                                 defaults={'user': user, 'token': token, 'set_time': datetime.datetime.utcnow().replace(tzinfo=utc)})
    return token


def updateToken(user):
    try:
        obj = models.SessionToken.objects.get(user=user)
        obj.set_time = datetime.datetime.utcnow().replace(tzinfo=utc)
        obj.save(force_update=True)
    except Exception as e:
        print(e)


def getToken(user, expire_time):
    try:
        obj = models.SessionToken.objects.get(user=user)
        if(datetime.datetime.utcnow().replace(tzinfo=utc) - obj.set_time >= datetime.timedelta(seconds=expire_time)):
            return ''
        else:
            return obj.token
    except Exception as e:
        print(e)
        return ''


def getIpAddr(req):
    if 'HTTP_X_FORWARDED_FOR' in req.META.keys():
        return req.META['HTTP_X_FORWARDED_FOR']
    else:
        return req.META['REMOTE_ADDR']

### put/get variables by names
def getVariableImpl(name, default):
    try:
        res = models.Variables.objects.get(varname=name)
        return res.value
    except Exception as e:
        print(e)
        return default

def putVariableImpl(name, value):
    try:
        models.Variables.objects.update_or_create(varname=name, defaults={'varname':name, 'value':value})
        return True
    except Exception as e:
        print(e)
        return False

def getCurrentDB():
    id = getVariableImpl("curr_db_id", "")
    if(id == ""):
        return None
    else:
        id = int(id)
        try:
            db_settings = models.DBSettings.objects.get(id=id)
            return db_settings
        except:
            return None

def check_login(f):
    @wraps(f)
    def inner(req, *arg, **kwargs):
        try:
            if('HTTP_X_ACCESS_TOKEN' in req.META.keys() and 'HTTP_X_ACCESS_USERNAME' in req.META.keys()):
                pass
            else:
                raise Exception()
        except:
            return JsonResponse({'status': -1, 'message': '非法请求'})
        try:
            header_username = req.META['HTTP_X_ACCESS_USERNAME']
            header_token = req.META['HTTP_X_ACCESS_TOKEN']
            user = models.User.objects.get(username=header_username)
            token = getToken(user, token_exp_time)
            if(token == header_token):
                updateToken(user)
                kwargs['__user'] = user
                return f(req, *arg, **kwargs)
            else:
                return JsonResponse({'status': -1, 'message': '用户未登录'})
        except:
            return JsonResponse({'status': -1, 'message': '非法请求'})
    return inner


def check_admin(f):
    @wraps(f)
    def inner(req, *arg, **kwargs):
        try:
            if('HTTP_X_ACCESS_TOKEN' in req.META.keys() and 'HTTP_X_ACCESS_USERNAME' in req.META.keys()):
                pass
            else:
                print('Invalid Headers')
                raise Exception()
        except:
            return JsonResponse({'status': -1, 'message': '非法请求'})
        try:
            header_username = req.META['HTTP_X_ACCESS_USERNAME']
            header_token = req.META['HTTP_X_ACCESS_TOKEN']
            user = models.AdminUser.objects.get(username=header_username)
            if(user.token == header_token
                    and datetime.datetime.utcnow().replace(tzinfo=utc) - user.token_set_time < datetime.timedelta(seconds=token_exp_time)):
                user.token_set_time = datetime.datetime.utcnow().replace(tzinfo=utc)
                user.save(force_update=True)
                kwargs['__admin_user'] = user
                return f(req, *arg, **kwargs)
            else:
                return JsonResponse({'status': -1, 'message': '用户未登录'})
        except Exception as e:
            print(e)
            return JsonResponse({'status': -1, 'message': '非法请求'})
    return inner

def check_post(f):
    @wraps(f)
    def inner(req, *arg, **kwargs):
        if(req.method == 'POST'):
            return f(req, *arg, **kwargs)
        else:
            return HttpResponseForbidden()
    return inner

@csrf_exempt
@check_post
@check_login
def debugCheckers(req, *arg, **kwargs):
    result = {'status': 1}
    if('__user' in kwargs.keys()):
        result = {'status': 0, 'message': kwargs['__user'].username }
    else:
        result['message'] = 'Failed'
    return JsonResponse(result)

@csrf_exempt
@check_post
def userLogin(req):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        user = models.User.objects.get(username=data['username'])
        if(user.password != data['password']):
            result['message'] = '用户名或密码错误'
            models.LogAction('login_failure', user,
                                getIpAddr(req), 'Wrong password')
            return JsonResponse(result)
        else:
            models.LogAction('login', user, getIpAddr(req))
            result['token'] = createToken(user)
            result['status'] = 0
            result['name'] = user.name
            result['username'] = user.username
            return JsonResponse(result)
    except Exception as e:
        print(e)
        result['message'] = '登录失败'
        return JsonResponse(result)


@csrf_exempt
@check_post
def adminLogin(req):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        user = models.AdminUser.objects.get(username=data['username'])
        if(user.password != data['password']):
            result['message'] = '用户名或密码错误'
            models.LogAdminAction('login_failure', user,
                                getIpAddr(req), 'Wrong password')
            return JsonResponse(result)
        else:
            models.LogAdminAction('login', user, getIpAddr(req))
            token = str(uuid.uuid4())
            user.token = token
            user.token_set_time = datetime.datetime.utcnow().replace(tzinfo=utc)
            user.save(force_update=True)
            result['token'] = token
            result['status'] = 0
            result['name'] = user.name
            result['username'] = user.username
            return JsonResponse(result)
    except Exception as e:
        print(e)
        result['message'] = '登录失败'
        return JsonResponse(result)


@csrf_exempt
@check_post
@check_admin
def createStudentAccounts(req, **kwargs):
    try:
        result = {'status': 1}
        username_col = int(req.POST.get('username_col'))
        name_col = int(req.POST.get('name_col'))
        pwd_col = int(req.POST.get('pwd_col'))
        db_settings_id = req.POST.get('db_settings_id')
        f = req.FILES.get('file')
        f.seek(0)
        #print("Load Files",name_col,pwd_col)
        # tempFilePath = f.temporary_file_path()
        stuinfo = xlrd.open_workbook(filename=None, file_contents=f.read())
        sheet0 = stuinfo.sheet_by_index(0)
        rownum = sheet0.nrows
        #print(sheet0.cell_value(0,0),rownum)
        for i in range(1,rownum):
            stu_name = str(sheet0.cell_value(i,name_col))
            stu_username = str(sheet0.cell_value(i,username_col))
            stu_pwd = str(sheet0.cell_value(i,pwd_col))
            stu_pwd = hashlib.md5(stu_pwd.encode(encoding='UTF-8')).hexdigest()
            stu_info = {'username': stu_username,
                'name': stu_name,
                'password': stu_pwd,
                'email': 'null',
                'db_settings_id': db_settings_id}
            models.User.objects.update_or_create(username=stu_username, defaults=stu_info)
        result['status'] = 0
        result['newusers'] = rownum-1
    except Exception as e:
        print(e)
        result['message'] = '服务器内部错误'

### Handlers for DBSettings
@csrf_exempt
@check_post
@check_admin
def getDBList(req, **kwargs):
    result = {'status': 1 }
    try:
        result['data'] = serializers.serialize(
            'json', models.DBSettings.objects.all().order_by("-set_time"), fields=('id', 'system_title', 'alias', 'set_time'))
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def changeUsersGroupByExcel(req, **kwargs):
    try:
        result = {'status': 1}
        username_col = int(req.POST.get('username_col'))
        db_settings_id = int(req.POST.get('db_settings_id'))
        group_id = int(req.POST.get('group_id'))
        f = req.FILES.get('file')
        f.seek(0)
        stuinfo = xlrd.open_workbook(filename=None, file_contents=f.read())
        sheet0 = stuinfo.sheet_by_index(0)
        rownum = sheet0.nrows
        #print(sheet0.cell_value(0,0),rownum)
        for i in range(1,rownum):
            stu_username = str(sheet0.cell_value(i,username_col))
            models.User.objects.filter(username=stu_username,db_settings = db_settings_id).update(group=group_id)
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '服务器内部错误'

def getDB(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        result['data'] = models.DBSettings.objects.get(id=data['data']).other_settings
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def getNotifications(req, **kwargs):
    try:
        result = {'status': 1}
        group_id = int(req.POST.get('group_id'))
        db_settings_id = int(req.POST.get('db_settings_id'))
        result['data'] = serializers.serialize(
            'json', models.Notification.objects.filter(group = group_id, db_settings = db_settings_id))
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '服务器内部错误'
    finally:
        return JsonResponse(result)
        

@csrf_exempt
@check_post
@check_admin        
def addDB(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        data = data['data']
        ms = models.DBSettings(
            alias=data['alias'],
            system_title=data['system_title'],
            other_settings=data['other_settings']
        )
        ms.save()
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def delDB(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        models.DBSettings.objects.filter(
            id=data['data']).delete()
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def getNotificationStatus(req, **kwargs):
    try:
        result = {'status': 1}
        notification_id = int(req.POST.get('notification_id'))
        result['data'] = serializers.serialize(
            'json', models.NotificationStatus.objects.filter(notification_id = notification_id))
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '服务器内部错误'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def editDB(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        data = data['data']
        model = models.DBSettings.objects.get(id=data['pk'])
        model.alias = data['alias']
        model.system_title = data['system_title']
        model.other_settings = data['other_settings']
        model.save(force_update=True)
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

### Handlers for GET/PUT variables

@csrf_exempt
@check_post
@check_admin
def getVariable(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        res = getVariableImpl(data['varname'], "")
        result['status'] = 0
        result['data'] = res
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def putVariable(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        ok = putVariableImpl(data['varname'], data['value'])
        if ok:
            result['status'] = 0
        else:
            result['message'] = '无法写入设置'
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def getCurrentDBId(req, **kwargs):
    result = {'status': 1}
    try:
        res = getCurrentDB()
        result['status'] = 0
        result['data'] = "" if res is None else res.id
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

def getCurrentSystemTitle(req):
    result = {}
    try:
        res = getCurrentDB()
        if(res is None):
            result['system_title'] = "通知系统"
        else:
            result['system_title'] = res.system_title
    except Exception as e:
        print(e)
        result['system_title'] = "通知系统"
    finally:
        return JsonResponse(result)

## Handlers for user groups
@csrf_exempt
@check_post
@check_admin
def getGroupList(req, **kwargs):
    result = {'status': 1 }
    try:
        db = getCurrentDB()
        if(db is None):
            result['data'] = json.dumps({'json':[]})
        else:
            result['data'] = serializers.serialize(
            'json', models.Group.objects.filter(db_settings=db))
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def addGroup(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        data = data['data']
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            ms = models.Group(
            groupname=data['groupname'],
            db_settings=db
            )
            ms.save()
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def delGroup(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            models.Group.objects.filter(id=data['data']).delete()
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def editGroup(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        data = data['data']
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            model = models.Group.objects.get(id=data['pk'])
            model.groupname = data['groupname']
            model.save(force_update=True)
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def sendNotificationUpload(req, **kwargs):
    try:
        result = {'status': 1}
        f = req.FILES.get('file')
        title = req.POST.get('title')
        content = req.POST.get('content')
        db_settings_id = int(req.POST.get('db_settings_id'))
        visible_group_id = int(req.POST.get('visible_group_id'))
        f.seek(0)
        fdir = os.path.join(data_dir,f.name)
        with open(fdir, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        notification = models.Notification.objects.create(
            title=title, content=ontent, attachment_arr=fdir, db_settings_id=db_settings_id, visible_group_id=visible_group_id)
        if visible_group_id == -1:
            users = list(models.User.objects.filter(db_settings_id = db_settings_id))
        else:
            users = models.User.objects.filter(db_settings_id = db_settings_id,group_id = visible_group_id)
        for user in users:
            models.NotificationStatus.objects.create(
                status=0, notification_id=notification.id, user_id = user.id)
        result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '请求无效'
    finally:
        return JsonResponse(result)
