from functools import wraps
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.core import serializers
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from django.core.paginator import Paginator
from dbapp import models
import requests
import urllib
from django.utils.timezone import utc
import urllib.parse
import json
from config import *
import uuid
import sys
import datetime
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
                raise Exception()
        except:
            return JsonResponse({'status': -1, 'message': '非法请求'})
        try:
            header_username = req.META['HTTP_X_ACCESS_USERNAME']
            header_token = req.META['HTTP_X_ACCESS_TOKEN']
            user = models.AdminUser.objects.get(username=header_username)
            if(user.token == header_token
                    and datetime.datetime.utcnow().replace(tzinfo=utc) - user.token_set_time >= datetime.timedelta(seconds=expire_time)):
                user.token_set_time = datetime.datetime.utcnow().replace(tzinfo=utc)
                user.save(force_update=True)
                kwargs['__admin_user'] = user
                return f(req, *arg, **kwargs)
            else:
                return JsonResponse({'status': -1, 'message': '用户未登录'})
        except:
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
