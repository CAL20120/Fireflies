import os 
import sys
import re

from functools import cache

import shutil
from datetime import datetime

import pathlib

import gazu


# NAS_DB_PATH = "Z:\\PRODS\\fireflies_tracker\\tracker_db.xml"


CT_HOU = False
CT_MAYA = False
CT_NUKE = False

try:
    import hou #type:ignore
    CT_HOU = True
    print("HOU CONTEXT")

except:
    pass


try:
    import maya.cmds as cmds #type: ignore
    import maya.OpenMayaUI as omui #type: ignore
    CT_MAYA = True
    print("MAYA CONTEXT")

except:
    pass


try:
    import nuke #type: ignore
    import nukescripts #type: ignore
    CT_NUKE = True
    print("NUKE CONTEXT")

except:
    pass



ASSET_TASKS = [
    "model",
    "assembly",
    "lookdev",
    "rig",
    "groom",
    "anim",
    "validate", #Only under Alice's supervision
    "to_validate", 
    "retopo", 
    "setup"

]

SHOT_TASKS = [
    "layout", 
    "light",
    "comp", 
    "env", 
    "fx", 
    "previz", 
    'anim'
]

TARGET_TASKS = ASSET_TASKS + SHOT_TASKS


@cache
def read_login_prefs():
    uesr_prefs_path = "C:\\Fireflies\\Common\\fmk_user_prefs\\login_prefs.txt"

    if not os.path.exists(uesr_prefs_path):
        print("### Please enter you informations in the fireflies framework ###")
        return


    with open(uesr_prefs_path, "r") as f:
        result = f.readlines()
    
    global username
    global password
    global user_mail

    username = result[0].strip()
    password = result[1].strip()
    user_mail = result[2].strip()


read_login_prefs()

def check_path_type(path:str) -> bool:
    path_check = False

    check = re.search(r'(\d{3}/\d{2})', path)

    if check:
        path_check = True

    print("### Path check result: {} ###".format(path_check))

    return path_check


class manage_paths():
    def __init__(self, path:str, is_asset:bool=None, path_check:bool=False) -> object:
        super(manage_paths, self).__init__()

        target_ext = ['.hip', '.hipnc', '.hiplc', '.mb', '.ma', '.nk']
        target_asset_ext = ['.usd', '.usda', '.usdc']

        if is_asset:
            target_ext = target_ext + target_asset_ext

        if any(ext for ext in target_ext if path.endswith(ext)):
            path = os.path.dirname(path)

        obj_path = pathlib.Path(path)
        path_parts = list(obj_path.parts)


        self.ct_scene = obj_path.stem
        self.ct_task = path_parts[-1]
        self.ct_shot = path_parts[-2]
        self.ct_seq = path_parts[-3]
        self.ct_prod = path_parts[-4]

        if is_asset: 
            kt_tasks_dict = gazu.task.all_task_types()
            kt_tasks = []
            for val in kt_tasks_dict:
                task = val['name']
                kt_tasks.append(task)

            path = path.replace('/', os.sep)

            obj_path = pathlib.Path(path)

            path_parts = list(obj_path.parts)

            self.ct_version = obj_path.stem
            self.ct_name = path_parts[-2]
            self.ct_task = next((task for task in kt_tasks if task in path), None)
            self.ct_prod = path_parts[-7]


            if path_check:
                self.ct_shot = path_parts[-5]
                self.ct_seq = path_parts[-6]



class manage_context():
    def __init__(self):
        try:
            gazu.set_host('http://192.168.1.176:4875/api')
        
            gazu.log_in(user_mail, password)

            self.kt_user = gazu.client.get_current_user()

        except:
            from PySide2 import QtWidgets
            print("### Please activate the vpn to use kitsu ###")

            QtWidgets.QMessageBox.warning(self, 'warning', 'Please activate the vpn to use kitsu')
            return



    def get_context_info(self, prod_name:str, seq_name:str=None, shot_name:str=None):
        current_path = None
        
        if CT_HOU:
            current_path = hou.hipFile.path()

        if CT_MAYA:
            pass

        self.kt_prod = gazu.project.get_project_by_name(prod_name)

        if not self.kt_prod: 
            print("### Couldn't find the targeted production ###")
            return

        if seq_name:
            self.kt_seq = gazu.shot.get_sequence_by_name(self.kt_prod, seq_name)

        if shot_name:
            self.kt_shot = gazu.shot.get_shot_by_name(self.kt_seq , shot_name)


    #used to create shots / tasks from the context window
    def add_seq(self, seq_name, prod_name):
        self.get_context_info(prod_name)

        new_seq = gazu.shot.new_sequence(
            self.kt_prod, 
            seq_name
        )
        
        print("### New sequence created: {} ###".format(seq_name))

        return new_seq


    def add_shot(self, prod_name, seq_name, shot_name):
        self.get_context_info(prod_name, seq_name)

        new_shot = gazu.shot.new_shot(
            self.kt_prod, 
            self.kt_seq, 
            shot_name
        )

        print("### New sequence created: {} ###".format(shot_name))

        return new_shot


    def add_task(self, prod_name, sequence_name, shot_name, task_name):
        self.get_context_info(prod_name, sequence_name, shot_name)

        kt_task_entity = gazu.task.get_task_type_by_name(task_name)
        kt_status = gazu.task.get_task_status_by_name('TODO')

        new_task = gazu.task.new_task(
            entity=self.kt_shot,
            task_type=kt_task_entity, 
            task_status=kt_status
        )
        
        print("### New task created created: {} ###".format(task_name))

        return new_task


    #all methods related to checks / publishing for assets        

    def publish_asset_task(self, asset_name, scene_path, preview_path=None, comment=None) -> dict:
        print("### Publishing asset on kitsu ###")

        CT_PATH = manage_paths(scene_path)

        self.get_context_info(prod_name=CT_PATH.ct_prod)

        kt_asset = gazu.asset.get_asset_by_name(self.kt_prod, asset_name)

        asset_exists = False
        if kt_asset:
            asset_exists = True

        kt_asset_type = gazu.asset.get_asset_type_by_name('Prop')

        if not asset_exists: 
            print("### Coudln't find the targeted asset, creating it... ###") 

            kt_asset = gazu.asset.new_asset(
                self.kt_prod, 
                kt_asset_type, 
                asset_name
            )

        kt_target_task = gazu.task.get_task_type_by_name(CT_PATH.ct_task)

        kt_asset_task = gazu.task.get_task_by_entity(kt_asset, kt_target_task)

        kt_status = gazu.task.get_task_status_by_name('Work In Progress')


        if not kt_asset_task:
            kt_asset_task = gazu.task.new_task(
                entity=kt_asset, 
                task_type=kt_target_task,
                task_status=kt_status
            )            

        if not comment:
            comment = "No comment"

        if not preview_path:
            preview_path = "Z:\\VFX_LIB\\06_USD_DEV\\debug_tex.png"
        
        preview_path = os.path.normpath(preview_path)

        gazu.task.publish_preview(
            task=kt_asset_task,
            task_status=kt_status, 
            person=self.kt_user, 
            comment=comment, 
            preview_file_path=preview_path
        )
        

    #mainly used in the asset resolver to set the correct
    #task status in kitsu

    def set_to_validate(self, prod_name:str, asset_path:str, valid_state:bool, task_removed:bool=False) -> list[dict]:
        """
        Method to set the validation status on kitsu
        
        Args:
            prod_name(str): The production name (that will be queried on kitsu)
            
            asset_path(str): The task path related to the targeted asset that will be changed on kitsu
            
            valid_state(bool): The validation status that will be displayed on kitsu (False= to_valid, True=Valid)
            
            task_removed(bool): If the task was removed from the validate usd stage

        Returns: 
            kt_infos, new_status: A list of the dict of the kitsu asset, and the new status
        """

        self.get_context_info(prod_name)

        CT_PATH = manage_paths(path=asset_path, is_asset=True)

        version = CT_PATH.ct_version[-3:]

        kt_infos = self.get_full_ct(asset_path, asset=True)

        if valid_state:
            kt_validate_status = gazu.task.get_task_status_by_name('Validate')
            comment = "Fireflies - approved task in validate for version: {}".format(version)

        else:
            if task_removed:
                kt_validate_status = gazu.task.get_task_status_by_name('Removed')
                comment = "Fireflies - task removed from the validate version: {}".format(version)


            else:
                kt_validate_status = gazu.task.get_task_status_by_name('Waiting For Validation')
                comment = "Fireflies - Task is waiting for validation for version: {}".format(version)
            

        current_task = kt_infos['task_entity']
        current_entity = kt_infos['current_entity']

        new_status = gazu.task.add_comment(current_task, kt_validate_status, comment)

        return kt_infos, new_status


    def get_kt_to_valid_tasks(self, prod_name:str, asset_name:str) -> dict:
        self.get_context_info(prod_name)

        kt_asset = gazu.asset.get_asset_by_name(self.kt_prod, asset_name)

        asset_data = kt_asset['data']
        # print(asset_data)

        return asset_data


    
    def check_current_prod(self, path:str) -> list[str, list]:
        """
        Checks if the current production is right (if manage_paths() fails)
        and returns the right production name 

        Args:
            path(str): A given path that will be checked via a kitsu query

        Returns: 
            out_prod(list): 
            A list of the current production name as a string, and the list of all the
            current productions as a list

        """

        prods = gazu.project.all_projects()

        current = []

        for val in prods: 
            current.append(val['name'])

        print(current)

        current_prod = next((prod for prod in current if prod in path), None)
        print(current_prod)

        if not current_prod:
            print("### Couldn't find a production in the given path ###")
            return
        
        out_prod = [current_prod, current]

        return out_prod




    ### all methods related to gather / publish shot info ###

    #we try to get all the possible data from a given shot / task path
    def get_full_ct(self, path:str, asset:bool=False) -> dict:
        check = check_path_type(path)

        task_exclude_list = ['to_validate', 'validate', 'assembly']

        current_prods = []
        target_entity = None

        match asset:
            case True if asset and check:
                CT_PATH = manage_paths(path, is_asset=True, path_check=True)

                print("### ASSET WITHIN SHOT ###")
                print(CT_PATH.ct_prod)
                print(CT_PATH.ct_seq)
                print(CT_PATH.ct_shot)
                print(CT_PATH.ct_task)

                self.get_context_info(CT_PATH.ct_prod, CT_PATH.ct_seq, CT_PATH.ct_shot)
                target_entity = self.kt_shot
                target_prod = CT_PATH.ct_prod

            case True if asset and not check:
                CT_PATH = manage_paths(path=path, is_asset=True)

                current_prod, kt_prods = self.check_current_prod(path)

                target_prod = current_prod if current_prod != CT_PATH.ct_prod else CT_PATH.ct_prod

                #temporary
                if any(task for task in task_exclude_list if task == CT_PATH.ct_task):
                    info_dict = {
                        'status': 'Not tracked',
                        'start_date': 'Not tracked',
                        'end_date': 'Not tracked', 
                        'assigned_users': ['Not tracked'], 
                        'task_entity': 'Not tracked', 
                        'current_entity': 'Not tracked'
                    }

                    return info_dict

                print(target_prod)
                self.get_context_info(target_prod)

                asset_name = CT_PATH.ct_name

                if not '_asset' in asset_name.lower():
                    asset_name = asset_name + '_ASSET'

                kt_asset = gazu.asset.get_asset_by_name(self.kt_prod, asset_name)
                target_entity = kt_asset


        if not asset:
            print("### Looking for shot ###")
            path = path.replace(os.sep, '\\')
            CT_PATH = manage_paths(path)

            self.get_context_info(CT_PATH.ct_prod, CT_PATH.ct_seq, CT_PATH.ct_shot)
            target_entity = self.kt_shot


        if not target_entity:
            print("### Couldn't find the targeted entity ###")
            return


        if CT_PATH.ct_task == 'validate':
            print("### Not checking for validates ###")
            return None

        target_task_type = gazu.task.get_task_type_by_name(CT_PATH.ct_task)
        
        kt_task_entity = gazu.task.get_task_by_entity(target_entity, target_task_type)


        start_date = 'Undefined'
        end_date = 'Undefined'

        try:
            kt_start = kt_task_entity['start_date']
            kt_end = kt_task_entity['due_date']
            
            out_date = lambda date: str(datetime.fromisoformat(date))
            
            if kt_start and kt_end:
                start_date = out_date(kt_start)
                end_date = out_date(kt_end)

        except:
            pass


        task_status = gazu.task.get_task_status(kt_task_entity['task_status_id'])
        current_status = task_status['short_name']

        kt_task = gazu.task.get_task(kt_task_entity['id'])

        assigned_users_id = kt_task['assignees']
            
        out_user_name = []
        for user_id in assigned_users_id:
            kt_user = gazu.person.get_person(user_id)
            user_name = kt_user['full_name']

            out_user_name.append(user_name)

        if not asset:
            kt_shot_data = self.kt_shot['data']

            kt_fstart = kt_shot_data['frame_in']
            kt_fend = kt_shot_data['frame_out'] 

            kt_frame_range = [kt_fstart, kt_fend]

            kt_fps = kt_shot_data['fps']

            info_dict = {
                'status': current_status,
                'start_date': start_date,
                'end_date': end_date, 
                'assigned_users': out_user_name, 
                'frame_range': kt_frame_range,
                'fps': kt_fps,
                'task_entity': kt_task_entity,
                'current_entity': target_entity

            }


        else:
            info_dict = {
                'status': current_status,
                'start_date': start_date,
                'end_date': end_date, 
                'assigned_users': out_user_name, 
                'task_entity': kt_task_entity, 
                'current_entity': target_entity
            }

        return info_dict


    def publish_shot_task(self, comment, preview_path, scene_path):
        if not os.path.exists(preview_path):
            preview_path = "Z:\\VFX_LIB\\06_USD_DEV\\debug_tex.png"

        preview_path = os.path.normpath(preview_path)

        if not os.path.exists(preview_path):
            print("### Couldn't find the preview path ###")
            return

        CT_PATH = manage_paths(scene_path)
        
        ct_task = CT_PATH.ct_task

        self.get_context_info(CT_PATH.ct_prod, CT_PATH.ct_seq, CT_PATH.ct_shot)
        target_task_type = gazu.task.get_task_type_by_name(ct_task)

        kt_task_entity = gazu.task.get_task_by_entity(self.kt_shot, target_task_type)
        kt_current_status = gazu.task.get_task_status(kt_task_entity['task_status_id'])

        gazu.task.publish_preview(
            task=kt_task_entity, comment=comment, preview_file_path=preview_path, 
            person=self.kt_user, task_status=kt_current_status
        )

        print("### Version published to kitsu - {} ###".format(ct_task))


    def set_scene_range(self, scene_path):
        # CT_CONTEXT = manage_paths(scene_path)
        
        kt_infos = self.get_full_ct(scene_path)

        f_start, f_end = kt_infos['frame_range']

        if not f_start:
            print("### First or Last frame is not set on kitsu ###")
            return

        if CT_HOU:
            hou.playbar.setFrameRange(f_start, f_end)

        if CT_MAYA:
            cmds.playbackOptions(minTime=f_start, maxTime=f_end,
                                 animationStartTime=f_start, animationEndTime=f_end)


        print("### Frame range set to the server data")

    #all methods related to assets

if __name__ == "__main__":
    path = "R:/Christopher_LUCAS/PRODS/test_dev_02/001/01/light/usd_published/rig_test_ASSET/rig_test_ASSET_003/rig_test_ASSET.usd"
    x = manage_paths(path=path, is_asset=True)

    print(x.ct_name)
