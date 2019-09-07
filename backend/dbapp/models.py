from django.db import models
from django.db.models.signals import pre_delete
import os
import json
import sys
sys.path.append('../')
from config import *
# used to store global configurations


class Variables(models.Model):
    varname = models.CharField(max_length=255, db_index=True, unique=True)
    value = models.TextField()


class DBSettings(models.Model):
    alias = models.CharField(max_length=255, db_index=True, unique=True)
    system_title = models.CharField(max_length=255)
    set_time = models.DateTimeField(auto_now_add=True)
    other_settings = models.TextField()  # JSON format

# users that are not subject to the change of DBsettings


class AdminUser(models.Model):
    username = models.CharField(max_length=100, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=50)
    email = models.EmailField(null=True, default=None)
    create_time = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=64, db_index=True)
    token_set_time = models.DateTimeField(auto_now_add=True)


class Group(models.Model):
    class Meta:
        unique_together = ("groupname", "db_settings")
    groupname = models.CharField(max_length=100)
    db_settings = models.ForeignKey(DBSettings, on_delete=models.CASCADE)


class User(models.Model):
    class Meta:
        unique_together = ("username", "db_settings")
    username = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=50)
    email = models.EmailField()
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, default=None)
    create_time = models.DateTimeField(auto_now_add=True)
    db_settings = models.ForeignKey(DBSettings, on_delete=models.CASCADE)


class Log(models.Model):
    action = models.CharField(max_length=100)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, default=None)
    admin_user = models.ForeignKey(
        AdminUser, on_delete=models.CASCADE, null=True, default=None)
    details = models.TextField(max_length=1000)
    ip = models.CharField(max_length=100)
    time = models.DateTimeField(auto_now_add=True)


class SessionToken(models.Model):
    user = models.OneToOneField(User, models.CASCADE)
    token = models.CharField(max_length=64, db_index=True)
    set_time = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    content = models.TextField()  # notification content, encoded in JSON
    attachment_arr = models.TextField()  # attachment array, encoded in JSON
    # if NULL, all users can see the message
    visible_group = models.ForeignKey(
        Group, on_delete=models.CASCADE, null=True, default=None)
    time = models.DateTimeField(auto_now_add=True, db_index=True)
    db_settings = models.ForeignKey(DBSettings, on_delete=models.CASCADE)


class NotificationStatus(models.Model):
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    status = models.PositiveSmallIntegerField(default=0)
    # if this entry does not exist / status == 0  => unread
    # status == 1 => read
    # status == 2 => accept
    # status == 3 => reject

def file_cleanup(sender, instance, *args, **kwargs):
    '''
        Deletes the file(s) associated with a model instance. The model
        is not saved after deletion of the file(s) since this is meant
        to be used with the pre_delete signal.
    '''
    try:
        attachments = json.loads(instance.attachment_arr)
        for f in attachments:
            try:
                os.remove(os.path.join(data_dir, f))
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    

pre_delete.connect(file_cleanup, sender=Notification)

def LogAction(action, username, ip, details=''):
    Log.objects.create(action=action, user=username, details=details, ip=ip)


def LogAdminAction(action, admin, ip, details=''):
    Log.objects.create(action=action, admin_user=admin, details=details, ip=ip)
