from functools import wraps
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.core import serializers
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from django.core.paginator import Paginator
from django.db.models import Q
from dbapp import models
import pathlib
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
from io import BytesIO
sys.path.append('../')

MSG_STATUS_ARR = [{
    'label': '未读',
    'type': ''
},{
    'label': '已读',
    'type': 'info'
},{
    'label': '已接受',
    'type': 'success'
},{
    'label': '已拒绝',
    'type': 'danger'
}]

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
            db_settings = getCurrentDB()
            if(db_settings is None):
                raise Exception("System is not properly configured")
            user = models.User.objects.get(username=header_username, db_settings=db_settings)
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
@check_admin
def adminChangePassword(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        user = kwargs['__admin_user']
        if(data['old_pwd'] == user.password):
            user.password = data['new_pwd']
            user.save(force_update=True)
            result['status'] = 0
        else:
            raise Exception('Invalid password found when trying to modify pwd')
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    return JsonResponse(result)

@csrf_exempt
@check_post
@check_login
def userChangePassword(req, **kwargs):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        user = kwargs['__user']
        if(data['old_pwd'] == user.password):
            user.password = data['new_pwd']
            user.save(force_update=True)
            result['status'] = 0
        else:
            raise Exception('Invalid password found when trying to modify pwd')
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    return JsonResponse(result)


@csrf_exempt
@check_post
def userLogin(req):
    result = {'status': 1}
    try:
        data = json.loads(req.body)
        db_settings = getCurrentDB()
        if(db_settings is None):
            raise Exception("System is not properly configured")
        user = models.User.objects.get(username=data['username'], db_settings=db_settings)
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
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            username_col = int(req.POST.get('username_col'))
            name_col = int(req.POST.get('name_col'))
            pwd_col = int(req.POST.get('pwd_col'))
            start_row = int(req.POST.get('start_row'))
            end_row = int(req.POST.get('end_row'))
            f = req.FILES.get('file')
            f.seek(0)
            #print("Load Files",name_col,pwd_col,username_col)
            # tempFilePath = f.temporary_file_path()
            stuinfo = xlrd.open_workbook(filename=None, file_contents=f.read())
            sheet0 = stuinfo.sheet_by_index(0)
            rownum = sheet0.nrows
            #print(sheet0.cell_value(0,0),rownum)
            for i in range(start_row, min(rownum, end_row + 1)):
                stu_name = str(sheet0.cell_value(i,name_col))
                stu_username = str(sheet0.cell_value(i,username_col))
                stu_pwd = str(sheet0.cell_value(i,pwd_col))
                stu_pwd = hashlib.md5(stu_pwd.encode(encoding='UTF-8')).hexdigest()
                stu_info = {'username': stu_username,
                    'name': stu_name,
                    'password': stu_pwd,
                    'db_settings': db}
                user, created = models.User.objects.update_or_create(username=stu_username, db_settings=db, defaults=stu_info)
                if(created):
                    ## update notification settings
                    entries = models.Notification.objects.filter(visible_group=None, db_settings=db)
                    for notify in entries:
                        models.NotificationStatus.objects.create(user=user, notification=notify, status=0)
            result['status'] = 0
            result['newusers'] = min(rownum, end_row + 1) - start_row
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
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            username_col = int(req.POST.get('username_col'))
            start_row = int(req.POST.get('start_row'))
            end_row = int(req.POST.get('end_row'))
            groupname_col = int(req.POST.get('groupname_col'))
            f = req.FILES.get('file')
            f.seek(0)
            stuinfo = xlrd.open_workbook(filename=None, file_contents=f.read())
            sheet0 = stuinfo.sheet_by_index(0)
            rownum = sheet0.nrows
            #print(sheet0.cell_value(0,0),rownum)
            changed = 0
            unchanged = 0
            for i in range(start_row,min(rownum, end_row+1)):
                stu_username = str(sheet0.cell_value(i,username_col))
                groupname = str(sheet0.cell_value(i,groupname_col))
                try:
                    group = None if groupname is None or groupname == "" else models.Group.objects.get(groupname=groupname, db_settings=db)
                    user = models.User.objects.get(username=stu_username, db_settings = db)
                    if(user.group != group):
                        # del old info
                        if(user.group is not None):
                            for item in models.NotificationStatus.objects.filter(user=user):
                                if(item.notification.visible_group is not None):
                                    item.delete()
                        # push new information
                        if(group is not None):
                            for item in models.Notification.objects.filter(visible_group=group):
                                models.NotificationStatus.objects.get_or_create(user=user, notification=item, defaults={
                                    'user': user,
                                    'notification': item,
                                    'status': 0
                                })
                        user.group = group
                        user.save(force_update=True)
                        changed += 1
                    else:
                        unchanged += 1
                except:
                    unchanged += 1
            result['changed'] = changed
            result['unchanged'] = unchanged
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
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            data = json.loads(req.body)
            notification_id = int(data['id'])
            notification = models.Notification.objects.get(id=notification_id, db_settings=db)
            result['data'] = []
            pages = Paginator(models.NotificationStatus.objects.filter(notification=notification).order_by("-status", "user_id"), 15)
            page = pages.page(data['page'])
            result['data'] = { 'page_cnt': pages.num_pages, 'count': pages.count, 'curr_entries': [] }
            seq = (data['page'] - 1) * 15
            for item in page.object_list:
                result['data']['curr_entries'].append({'seq': seq, 'username': item.user.username, 'name': item.user.name, 'status': MSG_STATUS_ARR[item.status] })
                seq += 1
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
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            notify = []
            notifies = models.Notification.objects.filter(db_settings = db).order_by("-time")
            for entry in notifies:
                notify.append({
                    'title': entry.title,
                    'date': entry.time,
                    'link': entry.id,
                    'id': entry.id
                })
            result['data'] = notify
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def delNotification(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            data = json.loads(req.body)['data']
            try:
                model = models.Notification.objects.get(db_settings=db,id=data['id'], title=data['title'])
                model.delete()
            except:
                pass
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_login
def getPersonalNotifications(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            user = kwargs['__user']
            ## visible to the group the user is in / visible to all (Group is None)
            notify = []
            notifies = models.Notification.objects.filter(Q(visible_group=user.group)|Q(visible_group=None), db_settings=db).order_by("-time")
            for entry in notifies:
                stat, _ = models.NotificationStatus.objects.get_or_create(
                    user=user, notification=entry, defaults={'user': user, 'notification': entry, 'status': 0})
                notify.append({
                    'title': entry.title,
                    'date': entry.time,
                    'link': entry.id,
                    'status': MSG_STATUS_ARR[stat.status],
                    'id': entry.id
                })
            result['data'] = notify
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '请求无效'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def sendNotification(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            f = req.FILES.get('file')
            title = req.POST.get('title')
            content = req.POST.get('content')
            visible_group_id_str = req.POST.get('visible_group_id')
            visible_group = None
            if(visible_group_id_str != ''):
                visible_group = models.Group.objects.get(id=int(visible_group_id_str))
            attachments = []
            if f is not None:
                f.seek(0)
                attachments.append(f.name)
                pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True) 
                fdir = os.path.join(data_dir, f.name)
                with open(fdir, 'wb+') as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)
            notification = models.Notification.objects.create(
                title=title, content=content, attachment_arr=json.dumps(attachments), db_settings=db, visible_group=visible_group)
            if(visible_group is not None):
                users = models.User.objects.filter(group=visible_group, db_settings=db)
            else:
                users = models.User.objects.filter(db_settings=db)
            for user in users:
                models.NotificationStatus.objects.update_or_create(notification=notification, user=user, defaults={
                    'notification': notification,
                    'user': user,
                    'status': 0
                })
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '请求无效'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_login
def getNotificationDetail(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            user = kwargs['__user']
            data = json.loads(req.body)
            notification_id = int(data['id'])
            notification = models.Notification.objects.get(Q(visible_group=user.group)|Q(visible_group=None), id=notification_id, db_settings=db)
            result['data'] = {
                'title': notification.title,
                'content': notification.content,
                'attachment_arr': json.loads(notification.attachment_arr)
            }
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '请求无效'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def getNotificationDetailAdmin(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            data = json.loads(req.body)
            notification_id = int(data['id'])
            notification = models.Notification.objects.get(id=notification_id, db_settings=db)
            result['data'] = {
                'title': notification.title,
                'content': notification.content,
                'attachment_arr': json.loads(notification.attachment_arr)
            }
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '请求无效'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_login
def changeNotificationStatus(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            user = kwargs['__user']
            data = json.loads(req.body)
            notification_id = int(data['id'])
            status = int(data['status'])
            notification = models.Notification.objects.get(Q(visible_group=user.group)|Q(visible_group=None), id=notification_id, db_settings=db)
            models.NotificationStatus.objects.update_or_create(user=user, notification=notification, defaults={'user':user, 'notification': notification, 'status':status})
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '请求无效'
    finally:
        return JsonResponse(result)

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
            models.Group.objects.filter(id=data['data'], db_settings=db).delete()
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
            model = models.Group.objects.get(id=data['pk'], db_settings=db)
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
def getUserList(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            data = json.loads(req.body)
            result['data'] = []
            pages = Paginator(models.User.objects.filter(db_settings=db).order_by('id'), 15)
            page = pages.page(data['page'])
            result['data'] = { 'page_cnt': pages.num_pages, 'count': pages.count, 'curr_entries': [] }
            seq = (data['page'] - 1) * 15
            for item in page.object_list:
                result['data']['curr_entries'].append({'seq': seq, 'username': item.username, 'name': item.name, 'link': {'link': item.id, 'label': '编辑用户'} })
                seq += 1
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def getUserInfo(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            data = json.loads(req.body)
            user = models.User.objects.get(db_settings=db, id=data['id'])
            result['data'] = {
                'username': user.username,
                'name': user.name,
                'email': user.email,
                'create_time': user.create_time,
                'group': None if user.group is None else user.group.id,
                'id': user.id
            }
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def changeUserInfoAdmin(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            data = json.loads(req.body)
            print(data)
            user = models.User.objects.get(db_settings=db, id=data['id'])
            user.email = data['email']
            if(data['pwd'] is not None and data['pwd'] != ""):
                user.password = data['pwd']
            group = None
            if(data['group'] is not None and data['group'] != ""):
                group_id = int(data['group'])
                group = models.Group.objects.get(id=group_id)
            ## if user changes group, messages that are private in original group should be deleted
            if(group != user.group):
                # del old information
                if(user.group is not None):
                    for item in models.NotificationStatus.objects.filter(user=user):
                        if(item.notification.visible_group is not None):
                            item.delete()
                # push new information
                if(group is not None):
                    for item in models.Notification.objects.filter(visible_group=group):
                        models.NotificationStatus.objects.get_or_create(user=user, notification=item, defaults={
                            'user': user,
                            'notification': item,
                            'status': 0
                        })
            user.group = group
            user.save(force_update=True)
            result['status'] = 0
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
    finally:
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_admin
def downloadAttachmentAdmin(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            data = json.loads(req.body)
            nid = data['id']
            fname = data['filename']
            notification = models.Notification.objects.get(id=nid, db_settings=db)
            arr = json.loads(notification.attachment_arr)
            if(fname in arr):
                response = HttpResponse(content_type='application/octet-stream')
                response['Content-Disposition'] = 'attachment;filename="{}"'.format(fname)
                response['Access-Control-Expose-Headers'] = 'Content-Disposition'
                with open(os.path.join(data_dir, fname), 'rb') as fin:
                    data = BytesIO(fin.read())
                    data.seek(0)
                    response.write(data.getvalue())
                    return response
            else:
                raise Exception("Invalid filename when trying to download attachment")
    except Exception as e:
        print(e)
        result['message'] = '操作失败'
        return JsonResponse(result)

@csrf_exempt
@check_post
@check_login
def downloadAttachmentUser(req, **kwargs):
    try:
        result = {'status': 1}
        db = getCurrentDB()
        if(db is None):
            raise Exception("No db is selected now")
        else:
            data = json.loads(req.body)
            user = kwargs['__user']
            nid = data['id']
            fname = data['filename']
            notification = models.Notification.objects.get(id=nid, db_settings=db)
            arr = json.loads(notification.attachment_arr)
            if(notification.visible_group is not None and notification.visible_group != user.group):
                raise Exception("Unauthorized user found when trying to download attachment")
            if(fname in arr):
                response = HttpResponse(content_type='application/octet-stream')
                response['Content-Disposition'] = 'attachment;filename=' + fname
                with open(os.path.join(data_dir, fname), 'rb') as fin:
                    data = BytesIO(fin.read())
                    data.seek(0)
                    response.write(data.getvalue())
                    return response
            else:
                raise Exception("Invalid filename when trying to download attachment")
    except Exception as e:
        print(e)
        result['message'] = '操作失败'