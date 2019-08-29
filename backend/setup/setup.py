### Initial setup script for the scholarship system
import argparse
import sys
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scholarship.settings")
sys.path.append('../')
import django
import getpass
import hashlib
import json
django.setup()
from scholarship import settings
from dbapp.models import User, ApplyMaterialSetting, ApplyScoreRuleSetting

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--add-admin", help="add an admin user", action="store_true")
    parser.add_argument("--add-teacher", help="add a teacher user", action="store_true")
    parser.add_argument("--del-admin", help="delete an admin user", action="store_true")
    parser.add_argument("--del-teacher", help="delete a teacher user", action="store_true")
    parser.add_argument("--import-default", help="import default material settings and scoring settings", action="store_true")
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(0)
    args = parser.parse_args()
    if((args.add_admin and args.del_admin) or (args.add_teacher and args.del_teacher)):
        print("Cannot add and delete user at the same time")
        exit(0)
    if((args.add_admin and args.add_teacher) or (args.del_admin and args.del_teacher)):
        print("Cannot add or delete two types of users at the same time")
        exit(0)
    if(args.add_admin or args.add_teacher):
        username = input("Input username: ")
        name = input("Input name: ")
        password = getpass.getpass("Input password: ")
        user_type = 2 if args.add_admin else 1
        info = {'username': username,
                        'name': name,
                        'user_type': user_type,
                        'password': hashlib.md5(password.encode()).hexdigest()}
        user, created = User.objects.update_or_create(
                    username=username, defaults=info)
        if(created):
            print("Created user %s successfully" % username)
        else:
            print("User %s already exists, updated its info instead" % username)
    if(args.del_admin or args.del_teacher):
        username = input("Input username: ")
        try:
            User.objects.get(username=username).delete()
            print("Successfully deleted user %s" % username)
        except:
            print("Delete failed. User does not exist")
    if(args.import_default):
        if(ApplyMaterialSetting.objects.all().count() > 0 or ApplyScoreRuleSetting.objects.all().count() > 0):
            print("Material/ScoreRule table is not empty, please truncate them before you do the initial import")
            exit(0)
        print("Import default settings")
        with open("default_template.json") as f:
            res = json.load(f)
            mSetting = ApplyMaterialSetting(alias=res['material_settings']['alias'], json=res['material_settings']['json'])
            mSetting.save()
            mScore = ApplyScoreRuleSetting(alias=res['score_rule_settings']['alias'], json=res['score_rule_settings']['json'],
            apply_material_id=mSetting)
            mScore.save()
        print("Successfully imported default template to database")

if(__name__ == "__main__"):
    main()
