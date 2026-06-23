import os 
import sys
import re

from functools import cache

import concurrent


import shutil
from datetime import datetime

import pathlib

from dataclasses import dataclass

import gazu

try:
    from pxr import Usd
except:
    pass

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
    "validate", #Only under Alice's supervision
    "to_validate", 
    "retopo", 
    "setup"

]

SHOT_TASKS = [
    "layout", 
    "light",
    "comp", 
    # "env", 
    "fx", 
    "cfx",
    "previz", 
    "anim", 
    "validate", 
    "delivery"
]


TARGET_TASKS = ASSET_TASKS + SHOT_TASKS


task_icon_dir = "C:\\Fireflies\\Fireflies\\softs_logo\\resolver\\tasks"
get_icon_path = lambda name: os.path.join(task_icon_dir, name)

SHOT_TASKS_ICONS = {
    'light': get_icon_path("light_task.png"),
    'fx': get_icon_path("fx_task.png"), 
    'cfx': get_icon_path('groom_task.png'), 
    'layout': get_icon_path("layout_task.png"), 
    'comp': get_icon_path("comp_task.png"), 
    'anim': get_icon_path("anim_task.png"),
    'to_validate': get_icon_path("validate_task.png"), 
    'validate': get_icon_path("delivery_task.png"), 
}

ASSET_TASKS_ICONS = {
    'model': get_icon_path('model_task.png'), 
    'groom': get_icon_path('groom_task.png'), 
    'lookdev': get_icon_path('lookdev_task.png')
}


shot_layers_order = ['cfx', 'fx', 'anim', 'light', 'layout']
asset_layers_order = ['model', 'groom', 'lookdev']



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



def get_local_prod_path():
    target_file = r"C:\\Fireflies\\Common\\fmk_user_prefs\\user_prefs_dir.txt"

    if not os.path.exists(target_file):
        print("### Please fill the production path in the framework ###")
        return

    with open(target_file, 'r') as f:
        path = os.path.normpath(f.read())

    return path
        


def check_path_type(path:str) -> bool:
    path_check = False

    check = re.search(r'(\d{3}/\d{2})', path)

    if check:
        path_check = True

    print("### Path check result: {} ###".format(path_check))

    return path_check


def get_scene_path():
    out_path = None

    if CT_HOU:
        out_path = hou.hipFile.path()
    
    if CT_MAYA:
        out_path = cmds.file(q=True, sn=True)

    if out_path is None:
        print("### Error while trying to get the scene path ###")
        return
    
    return out_path




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
            print("### Please activate the vpn to use kitsu ###")
            return


        self.kt_shot = None


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

    def set_to_validate(self, prod_name:str, asset_path:str,
                        valid_state:bool, kt_task_entity:dict, 
                        version:str=None) -> list[dict]:
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

        if not version:
            CT_PATH = manage_paths(path=asset_path, is_asset=True)
            version = CT_PATH.ct_version[-3:]


        if valid_state:
            kt_validate_status = gazu.task.get_task_status_by_name('Validate')
            comment = "Fireflies - approved task in validate for version: {}".format(version)

        else:
            kt_validate_status = gazu.task.get_task_status_by_name('Waiting For Validation')
            comment = "Fireflies - Task is waiting for validation for version: {}".format(version)
            

        # current_task = kt_infos['task_entity']
        # current_entity = kt_infos['current_entity']

        new_status = gazu.task.add_comment(kt_task_entity, kt_validate_status, comment)

        return kt_task_entity, new_status


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

        target_entity = None

        if not asset:
            if 'props' in path.lower():
                print("### ASSET CONTEXT ###")
                asset = True


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

            if self.kt_shot is None:
                return

            target_entity = self.kt_shot


        if not target_entity:
            print("### Couldn't find the targeted entity ###")
            return


        if CT_PATH.ct_task == 'validate':
            print("### Not checking for validates ###")
            return None

        target_task_type = gazu.task.get_task_type_by_name(CT_PATH.ct_task)
        
        try:
            kt_task_entity = gazu.task.get_task_by_entity(target_entity, target_task_type)
        
        except:
            print("### Couldn't find the targeted task ###")
            return


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
                'current_entity': target_entity, 
                'is_asset': asset

            }


        else:
            info_dict = {
                'status': current_status,
                'start_date': start_date,
                'end_date': end_date, 
                'assigned_users': out_user_name, 
                'task_entity': kt_task_entity, 
                'current_entity': target_entity, 
                'is_asset': asset
            }

        return info_dict


    def get_shots_hierarchy(self, prod_name:str):
        """
        Used to get a dict of the sequences and shot names
        """

        current_production = gazu.project.get_project_by_name(prod_name)

        seqs = gazu.shot.all_sequences_for_project(current_production)
        # print(shots)

        out_dict = {}

        for val in seqs:
            seq_name = val['name']
            shots = gazu.shot.all_shots_for_sequence(val)

            shot_list = [shot['name'] for shot in shots]

            for x in range(len(shot_list)):
                current_shot_name = shot_list[x]
                tasks = gazu.task.all_tasks_for_shot(shots[x])

                out_dict.setdefault(seq_name, {})[current_shot_name] = tasks

            # for x in range(len(shot_list)):
            #     current_shot_name = shot_list[x]

            #     tasks = gazu.task.all_tasks_for_shot(shots[x])

            #     out_dict.setdefault(
            #         seq_name, {current_shot_name: tasks}
            #     )



        return out_dict



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



@dataclass
class Shot_Builder_Context: 
    scene_path:str = None
    kt_context:dict = None

    prod_name:str = None
    shot_name:str = None
    task_name:str = None

    current_hou_context:str = None

    shot_vars:dict = None
    current_shot_data:dict = None


class Shot_Builder(): 
    def __init__(self):
        from fireflies.houdini import hou_utils
        from fireflies.fireflies_utils.usd import usd_asset_importer_hou

        self.builder_context = Shot_Builder_Context()
        self._HOU_UTILS = hou_utils.hou_usd()
        self.CONTEXT = manage_context()

        self._ASSET_FINDER = usd_asset_importer_hou.import_usd_asset()


        self.task_dependencies = {
            "light": ["layout", "fx", "anim"], 
            "fx": ["layout", "anim"],
            "cfx": ["layout", "anim", "fx"]
        }


        self.downstream_dependencies = {
            "layout": ["fx", "cfx", "light"], 
            "cfx": ["fx", "light"], 
            "fx": ["light"],
            "anim": ["fx", "cfx", "light"]
        }


        self.dependencies_templates = {
            "fx": "Fireflies::fireflies_fx_template",
            "light": "Fireflies::fireflies_light_template", 
            "cfx": "Fireflies::fireflies_cfx_template"
        }



        self.update_context()

        self._hda_template_name = f"_SHOT_TEMPLATE_{self.builder_context.task_name.upper()}"



    def update_context(self):
        """
        Updates the linked dataclass (context) with the correct values.
        """

        current_scene_path = get_scene_path()
        self.builder_context.scene_path = current_scene_path
        
        CT_PATH = manage_paths(path=current_scene_path, is_asset=False)
        prod_name = CT_PATH.ct_prod
        seq_name = CT_PATH.ct_seq
        shot_name = CT_PATH.ct_shot
        task_name = CT_PATH.ct_task

        if not any([prod_name, shot_name, task_name]): 
            raise ValueError("### Please set a shot context ###")
        

        self.builder_context.prod_name = prod_name
        self.builder_context.task_name = task_name
        self.builder_context.shot_name = shot_name

        local_prod_dir = get_local_prod_path()
        self.prod_path = os.path.join(local_prod_dir, prod_name)

        kt_infos = self.CONTEXT.get_full_ct(current_scene_path, asset=False)
        self.builder_context.kt_context = kt_infos

        _, shot_vars = self._ASSET_FINDER.find_asset(shot_filter=True)
        self.builder_context.asset_vars = shot_vars

        shot_finder_name = f"_{seq_name}_{shot_name}_SHOT"

        current_shot_data = shot_vars.get(shot_finder_name, {})
        self.builder_context.current_shot_data = current_shot_data


    def get_dependencies(self, target_task:str=None) -> dict:
        """
        Get the correct tasks and versions related to the current main task.
        """

        task_name = self.builder_context.task_name if not target_task else target_task
        shot_data = self.builder_context.current_shot_data

        print(task_name)
        print(shot_data)

        dependant_tasks = self.task_dependencies.get(task_name, [])
        print(dependant_tasks)

        out_dependencies = {}

        if not shot_data: 
            print("### No published entities found for this shot ###")
            return
        
        for task in dependant_tasks: 
            last_version = None
            last_path = None

            for version in sorted(shot_data.keys()): 
                print(version)

                if task in shot_data[version].keys(): 
                    last_path = shot_data[version][task]['path']
                    last_version = version

            if last_path: 
                out_dependencies[task] = {
                    "path": last_path, 
                    "version": last_version
                }

        return out_dependencies



    def check_target_template(self, curr_network, template_name): 
        network_path = curr_network.path()

        hda_node = hou.node(f"{network_path}/{self._hda_template_name}")

        if not hda_node: 
            hda_node = curr_network.createNode(template_name, self._hda_template_name)
            hda_node.moveToGoodPosition()
            
            print("### Create template: {} ###".format(hda_node.path()))

        return hda_node



    def build_input_streams(self, curr_network, hda_node, target_dependencies):
        task_name = self.builder_context.task_name
        ordered_task = self.task_dependencies.get(task_name, [])

        task_color = {
            "fx": hou.Color((0.8, 0.2, 0.2)),
            "anim": hou.Color((0.3, 0.7, 0.3)), 
            "layout": hou.Color((0.5, 0.5, 0.5)), 
            "cfx": hou.Color((0.2, 0.4, 0.8))
        }

        # for idx, task in enumerate(ordered_task): 
        #     if task not in target_dependencies: 
        #         continue
            
        sop_name = f"SOP_{task_name.upper()}"
        sop_node = hou.node(f"{curr_network.path()}/{sop_name}")
        
        if not sop_node: 
            sop_node = curr_network.createNode('sopimport', sop_name)
            self.net_box.addItem(sop_node)


        null_name = f"IN_{task_name.upper()}"
        null_node = hou.node(f"{curr_network.path()}/{null_name}")

        if not null_node: 
            null_node = curr_network.createNode('null', null_name)
            self.net_box.addItem(null_node)

            null_node.setColor(task_color.get(task_name, hou.Color((0.8, 0.8, 0.8))))

        publish_name = f"PUBLISH_{task_name}_SHOT"
        publish_node = hou.node(f"{curr_network.path()}/{publish_name}")

        if not publish_node: 
            publish_node = curr_network.createNode('Fireflies::publish_work::1.0', publish_name)
            self.net_box.addItem(publish_node)


        null_node.setInput(0, sop_node)
        hda_node.setInput(0, null_node)
        null_node.setPosition(sop_node.position() + hou.Vector2(0, -1.5))
        publish_node.setInput(0, hda_node)

        hda_pos = hda_node.position()

        sop_node.setPosition(hda_pos + hou.Vector2(0, 3))
        null_node.setPosition(hda_pos + hou.Vector2(0, 1.5))
        publish_node.setPosition(hda_pos - hou.Vector2(0, 1.5))




    def update_hda_refs(self, hda_node):
        task_name = self.builder_context.task_name

        current_dir = os.path.dirname(self.builder_context.scene_path)
        layerStack_path = f"{current_dir}/working_stack/layerstack_{task_name}.usd".replace('\\', '/')

        if not hda_node.isEditable():
            hda_node.allowEditingOfContents()

        sublayer_node = hou.node(f"{hda_node.path()}/INPUT_LAYERS")
        
        if not sublayer_node:
            print("### Couldn't find the internal reference LOP node for the template ###")
            return
        

        if os.path.isabs(layerStack_path):
            layerStack_path = self._HOU_UTILS.path_converter(layerStack_path)

        sublayer_node.parm('num_files').set(1)
        sublayer_node.parm('filepath1').set(layerStack_path)

        print("### Refs checks done ###")



    def check_net_box(self, curr_network, box_name):
        target_net_box = None

        for net_box in curr_network.networkBoxes(): 
            if net_box.comment() == box_name: 
                target_net_box = net_box
                return
            
        if not target_net_box: 
            target_net_box = curr_network.createNetworkBox(box_name)
            target_net_box.setComment(box_name)

        return target_net_box



    def build_node_hierarchy(self):
        task_name = self.builder_context.task_name
        template_name = self.dependencies_templates.get(task_name)

        if not template_name: 
            print("### Couldn't find a template for this task ###")
            return
        
        target_dependencies = self.get_dependencies()

        if not target_dependencies: 
            print("### Couldn't find any dependencies published for this task ###")
            return
        
        curr_network = self._HOU_UTILS.get_current_context()
        network_path = curr_network.path()

        box_name = f"{task_name.upper()}_TEMPLATE"
        self.net_box = self.check_net_box(curr_network, box_name)

        hda_node = self.check_target_template(curr_network, template_name)
        self.net_box.addItem(hda_node)

        self.build_input_streams(curr_network, hda_node, target_dependencies)

        self.update_hda_refs(hda_node)

        self.net_box.fitAroundContents()
        hda_node.setDisplayFlag(True)

        print("### Template Updated ###")



    def get_layer_order_key(self, path):
        task = next((task for task in SHOT_TASKS if task in path), None) 
        tracker_position = shot_layers_order

        try:
            index = tracker_position.index(task)
            return index
        
        except ValueError:
            return 



    def build_dependencies_stack(self, published_path:str):
        current_task = self.builder_context.task_name
        target_tasks = self.downstream_dependencies.get(current_task, [])

        if not target_tasks: 
            print("### No dependencies found for this task ###")
            return
        
        published_path = os.path.normpath(published_path)
        print(published_path)

        try: 
            shot_root = published_path.split(f"\\{current_task}\\")[0]
            print(shot_root)

        except IndexError: 
            print("### Could not find shot root ###")
            return
        

        def update_single_layer(task):
            target_dir = f"{shot_root}/{task}"
            print(target_dir)

            layerStack_path = f"{target_dir}/working_stack/layerstack_{task}.usd"

            if not os.path.exists(layerStack_path):
                stage = Usd.Stage.CreateNew(layerStack_path)

            else:
                stage = Usd.Stage.Open(layerStack_path)

            root_layer = stage.GetRootLayer()

            sublayers = list(root_layer.subLayerPaths)
            sublayers = [path.strip('@') for path in sublayers]


            if os.path.isabs(published_path):
                rel_path = os.path.relpath(
                    published_path, os.path.dirname(layerStack_path)
                ).replace('\\', '/')


            if sublayers:
                found = False
                for idx, path in enumerate(sublayers): 
                    sub_task = next((task for task in SHOT_TASKS if task in path), None) 

                    if current_task == sub_task:
                        sublayers[idx] = rel_path
                        found = True
                        break

                if not found:
                    sublayers.append(rel_path)


            else:
                sublayers = [rel_path]


            sublayers = sorted(sublayers, key=self.get_layer_order_key)
            print(sublayers)

            root_layer.subLayerPaths = sublayers
            root_layer.Save()
            
            print("### Path set for working stack: {} | {} ###".format(task, published_path))

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(target_tasks)) as executor: 
            outputs = [executor.submit(update_single_layer, task) for task in target_tasks]
            for future in concurrent.futures.as_completed(outputs):
                print(future.result())



if __name__ == "__main__":
    pass

