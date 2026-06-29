import os 
import sys

import re
import shutil
import time

import json

import subprocess 

from datetime import date
import random

from dataclasses import dataclass


import gazu

from fireflies.context import prod_tracker
CONTEXT = prod_tracker.manage_context()


try:
    import hou 
    from fireflies.houdini import hou_utils

except:
    pass

# from fireflies.context.prod_tracker import get_context
# from fireflies.fireflies_utils import fireflies_requests



LOCAL_NAS_PROD = "Z:/PRODS"
LOCAL_NAS_CACHE = "Z:/PROD_CACHE"
if not os.path.exists(LOCAL_NAS_PROD):
    print("### Couldn't find the prod nas dir -- Exiting ###")

convert = lambda path : LOCAL_NAS_PROD + path.split('PRODS', 1)[-1]

class hou_deadline_submitter():
    def __init__(self):
        self.hython_path = "C:\\Fireflies\\Common\\Houdini_vars\\houdini_205445\\Houdini20.5.445\\bin\\hython.exe"
        self.deadline_hython = "C:\\Fireflies\\Fireflies_BIN\\Sidefx\\env\\deadline_hython_310.bat"

        self.deadline_ex = "C:\\Fireflies\\Deadline\\bin\\deadlinecommand.exe"
        self.husk_ex = "C:\\Fireflies\\Fireflies_BIN\\Sidefx\\env\\husk_684_dl.bat"

        self.tmp_dir = os.environ.get('TMP')

        self.utils = hou_utils.hou_usd()


    def write_target_file(self, file_path, content):
        with open(file_path, 'w') as f:
            f.write(content)

        return file_path


    def get_job_info(self, target_node:str, scene_path:str) -> list:
        # node = target_node
        # if isinstance(target_node, str):
        node = hou.node(target_node)


        out_images = None
        try:
            out_images = node.evalParm('output')

            out_dir = os.path.dirname(out_images)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)

            # new_path = out_images.split('PRODS', 1)
            out_images = convert(out_images)

        except:
            pass


        priority_ints = [10, 50, 100]
        priority_index = node.evalParm('dl_priority')

        dl_priority = priority_ints[priority_index]

        node_job_name = node.evalParm('dl_job_name')

        if node_job_name:
            job_name = node_job_name

        else: 
            job_name = hou.hipFile.basename().rsplit('.', 1)[0]

        scene_path = scene_path.replace(os.sep, '/')
                                        
        departement = scene_path.split('/')[-2]

        dl_comment = node.evalParm('dl_comment')

        user_range = node.evalParm('trange')

        machine_sel = False
        if node.evalParm('dl_machine_sel'):
            machine_sel = node.parm('dl_machine_list').evalAsString()


        f_start = int(hou.frame())
        f_end = f_start

        if user_range != 0:
            f_start, f_end = hou.playbar.playbackRange()
            
            f_start = int(node.evalParm('f1'))
            f_end = int(node.evalParm('f2'))


        # new_path = scene_path.split('PRODS', 1)
        # new_scene = LOCAL_NAS_PROD + new_path[-1]

        new_scene = convert(scene_path)

        
        infos = [
            dl_priority, 
            job_name,
            dl_comment,
            departement,
            machine_sel,
            f_start, 
            f_end,
            new_scene
        ]

        if out_images:
            infos.insert(0, out_images)

        return infos


    def hou_job_info(self, job_name, frames, priority:str, comment, machine_sel:str) -> str:
        info_txt = 'Plugin=CommandLine\n' \
                    'Name={} [Write stage]\n' \
                    'BatchName={}\n' \
                    'Comment={}\n' \
                    'Pool=none\n' \
                    'Group=none\n' \
                    'Priority={}\n' \
                    'Department=Usd generation\n' \
                    'Frames={}\n' \
                    'ChunkSize=128\n' \
                    'MachineLimit=0\n' \
                    'ConcurrentTasks=1\n'.format(job_name, job_name, comment, priority, frames)


        if machine_sel:
                info_txt += 'Allowlist={}\n'.format(machine_sel)
                # print(f"### Selected Machine: {machine_sel} ###")

        target_path = os.path.join(self.tmp_dir, 'export_job_info.job')

        out = self.write_target_file(target_path, info_txt)

        return out


    def hou_plugin_info(self, scene_path, target_node, export_path) -> str:

        generate_usd_script = "C:\\Fireflies\\Fireflies_BIN\\fireflies\\houdini\\usd_render_call.py"
        

        args = f'{generate_usd_script} -scene_path "{scene_path}" -node_path "{target_node}" -export_path "{export_path}" -f_start <STARTFRAME> -f_end <ENDFRAME>'
                        
        plugin_txt = 'Executable={}\n' \
                     'Arguments={}\n' \
                     'StartupDirectory=\n' \
                     'SingleFramesOnly=False'.format(self.deadline_hython, args)
        
        target_path = os.path.join(self.tmp_dir, 'export_plugin_info.job')

        out = self.write_target_file(target_path, plugin_txt)

        return out
    

    def hou_render_job_info(self, job_name, priority:str, frames, id,
                            department, comment, machine_sel:str, nas_usd_dir:str) -> str:
        
        raidrive_pre_script = "C:\\Fireflies\\Fireflies_BIN\\fireflies\\fireflies_utils\\pre_render_raidrive.py"

        info_txt = 'Plugin=CommandLine\n' \
                    'Name={} [Render]\n' \
                    'BatchName={}\n' \
                    'Comment={}\n' \
                    'Pool=none\n' \
                    'Group=none\n' \
                    'Priority={}\n' \
                    'Department={}\n' \
                    'Frames={}\n' \
                    'ChunkSize=1\n' \
                    'JobDependency0={}\n' \
                    'EnvironmentKeyValue0=NAS_USD_DIR={}\n'.format(job_name, job_name, comment,
                                                                   priority, department, frames,
                                                                   id, nas_usd_dir)
        

        if machine_sel:
                info_txt += 'Allowlist={}\n'.format(machine_sel)
                print(f"### Selected Machine: {machine_sel} ###")
        
        target_path = os.path.join(self.tmp_dir, 'render_job_info.job')

        out = self.write_target_file(target_path, info_txt)

        return out


    def hou_render_plugin_info(self, usd_file:str, out_images:str, render_delegate:str) -> str:
        render_script = "C:\\Fireflies\\Fireflies_BIN\\fireflies\\houdini\\usd_render_call.py"
        # args = f'-R {render_delegate} -V 3 --exrmode 1 -s /Render/rendersettings -o {out_images} {usd_file} --frame <STARTFRAME>'

        args = (
            f'{render_script}'
            f' -mode render'
            f' -delegate {render_delegate}'
            f' -usd_path {usd_file}'
            f' -out_images {out_images}'
            f' -frame <STARTFRAME>'
            f' -husk_path {self.husk_ex}'
        )

        plugin_txt = 'Executable={}\n' \
                    'Arguments={}\n' \
                    'StartupDirectory=\n' \
                    'SingleFramesOnly=False'.format(self.deadline_hython, args)
        
        target_path = os.path.join(self.tmp_dir, 'render_plugin_info.job')

        out = self.write_target_file(target_path, plugin_txt)

        return out 
    


    def sumbit_usd_render_job(self, target_node_path=None):

        if not target_node_path:
            target_node = hou.pwd()
        
        else: 
            target_node = hou.node(target_node_path)

        scene_path = hou.hipFile.path()
        local_scene_path = scene_path


        (out_images, dl_priority, job_name, dl_comment,
        departement, machine_sel, f_start, f_end, new_scene) = self.get_job_info(target_node.path(), scene_path)

        print(out_images)

        rm_delegates = ['HdPrmanXpuLoaderRendererPlugin', 'HdPrmanLoaderRendererPlugin']
        render_delegate = rm_delegates[target_node.evalParm('rm_delegate')]


        target_dir = os.path.dirname(out_images)
        export_dir = os.path.join(target_dir, "deadline_usd")
        export_dir = export_dir.replace('/', '\\')

        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        scene_path = new_scene

        print("#### NAS SCENE: {} ####".format(scene_path))

        if not os.path.exists(LOCAL_NAS_PROD) and "PROD" not in scene_path:
            print("## Issue related to the PROD directory -- Exiting ##")
            return

        
        if not target_node.evalParm('cam'):
            print("## No camera was selecled -- Exiting ##")
            return


        print("Selected priority: " + str(dl_priority))

        # new_path = out_images.split('PRODS', 1)
        # print(new_path)


        fld, file = os.path.split(out_images)
        out_dir = os.path.dirname(out_images)


        target_frame = re.search(r'\d+', file)

        if not target_frame:
            print("### Couldn't find a frame number in the export path -- Exiting ###")

        fixed_name = file.replace(target_frame.group(), '$F')

        out_images = os.path.join(fld, fixed_name).replace('\\', '/')
        

        print(f"### EXPORT PATH: {out_images} ###")

        dl_path = out_images.replace('$F', '__target_frames__')
        # dl_path = hou.text.expandString(dl_path)

        # print(dl_path)

        husk_out_images = dl_path.replace('__target_frames__', '<STARTFRAME>')

        if not out_images:
            print("### No path out path for the images was found -- Exiting ###")
            return
        
        hou.hipFile.save()


        dl_frames = f"{f_start}-{f_end}"

        print("####### EXPORT DIR: {} ######".format(export_dir))

        export_dir = export_dir.replace(os.sep, '/')

        export_path = os.path.join(
            export_dir, "__render__.$F4.usdc"
        ).replace("\\", '/')

        print("### USD EXPORT PATH: {} ###".format(export_path))


        usd_export_job = self.hou_job_info(job_name, dl_frames, dl_priority, dl_comment, machine_sel)
        usd_export_plugin = self.hou_plugin_info(scene_path, target_node.path(), export_path)

        job_cmd = [self.deadline_ex, usd_export_job, usd_export_plugin]
        
        print("### Launching jobs ###")

        dl_proc = subprocess.Popen(
            job_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        stdout_job, stderr_job = dl_proc.communicate()

        usd_job_id = ""

        for line in stdout_job.splitlines():
            if "JobID=" in line:
                usd_job_id = line.split("=")[1].strip()

        if not usd_job_id:
            print("Couldn't find the usd creation job id")
            
            print(stdout_job)
            print("#####################")
            print(stderr_job)
            return
        
        print(usd_job_id)

        husk_render_input = export_path.replace('$F4', "<STARTFRAME%4>").replace('$F', '<STARTFRAME>')

        render_job = self.hou_render_job_info(job_name, dl_priority, dl_frames, usd_job_id,
                                              departement, dl_comment, machine_sel, export_dir)
        render_plugin = self.hou_render_plugin_info(usd_file=husk_render_input, out_images=husk_out_images, render_delegate=render_delegate)

        render_job_cmd = [self.deadline_ex, render_job, render_plugin]

        render_proc = subprocess.Popen(
            render_job_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        stdout_job, stderr_job = render_proc.communicate()

        out_usd_dir = os.path.dirname(export_path)
        target_dir = os.path.basename(out_usd_dir)
        


    #### HOUDINI CACHES ####

    def hou_cache_job(self, job_name, comment, priority, frames, machine_sel) -> str:
        info_txt = 'Plugin=CommandLine\n' \
                    'Name={} [Cache]\n' \
                    'BatchName={}\n' \
                    'Comment={}\n' \
                    'Pool=none\n' \
                    'Group=none\n' \
                    'Priority={}\n' \
                    'Department=Sop cache\n' \
                    'Frames={}\n' \
                    'ChunkSize=2000\n' \
                    'MachineLimit=1\n' \
                    'ConcurrentTasks=1\n'.format(job_name, job_name, comment, priority, frames)

        if machine_sel:
                info_txt += 'Allowlist={}\n'.format(machine_sel)
                print(f"### Selected Machine: {machine_sel} ###")


        target_path = os.path.join(self.tmp_dir, 'export_job_info.job')

        out = self.write_target_file(target_path, info_txt)

        return out



    def hou_cache_plugin(self, scene_path:str, target_node, render_dir:str, render_path:str):
        generate_usd_script = "C:\\Fireflies\\Fireflies_BIN\\fireflies\\houdini\\cache_render_call.py"
        

        args = f'{generate_usd_script} -scene_path "{scene_path}" -node_path "{target_node}" -render_dir "{render_dir}" -render_path "{render_path}"'
                        
        plugin_txt = 'Executable={}\n' \
                     'Arguments={}\n' \
                     'StartupDirectory=\n' \
                     'SingleFramesOnly=False'.format(self.deadline_hython, args)
        
        target_path = os.path.join(self.tmp_dir, 'export_plugin_info.job')

        out = self.write_target_file(target_path, plugin_txt)

        return out


    def get_cache_paths(self, node_path:str) -> str:
        cache_node = hou.node(node_path)

        cache_dir = cache_node.evalParm('cachedir')
        cache_name = cache_node.evalParm('cachename')

        init_path = f"{cache_dir}/{cache_name}"

        target_frame = re.search(r'\d{4}', init_path)
        print(target_frame.group())
        init_path = init_path.replace(target_frame.group(), '$F')

        path = init_path
        dir, target = path.split('PRODS', 1)
        
        nas_cache_path = f"{LOCAL_NAS_CACHE}{target}"
        print("### {} ###".format(nas_cache_path))

        local_cache_path = f"{dir}PROD_CACHE{target}"

        cache_hip_path = self.utils.path_converter(local_cache_path)
        cache_node.parm('sopoutput').set(cache_hip_path)
        print("Path set...")

        print("### PROD CACHE PATH: {} ###".format(local_cache_path))


        return nas_cache_path, local_cache_path



    def launch_cache_job(self, target_node_path=None):
        hou.hipFile.save()

        if not target_node_path:
            target_node = hou.pwd()

        else: 
            target_node = hou.node(target_node_path)
    
        target_node.allowEditingOfContents()

        node_path = target_node.path()
        cache_node_path = f"{node_path}/target_cache"
        cache_node = hou.node(cache_node_path)
        
        nas_cache_path, local_cache_path = self.get_cache_paths(cache_node_path)
        # hip_cache_path = self.utils.path_converter(nas_cache_path)

        output_path = nas_cache_path

        output_dir = os.path.dirname(output_path)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        output_path = nas_cache_path

        scene_path = hou.hipFile.path()

        nas_scene = convert(scene_path)
        nas_scene_dir = os.path.dirname(nas_scene)

        file_name, ext = os.path.basename(scene_path).rsplit('.', 1)

        local_output_dir = os.path.dirname(local_cache_path)

        if not os.path.exists(local_output_dir):
            os.makedirs(local_output_dir)


        new_name = f"{file_name}_FARM_{date.today()}.{ext}"
        new_path = os.path.join(local_output_dir, new_name)

        new_path = new_path.replace('/', os.sep)

        try:
            shutil.copyfile(scene_path, new_path)
            time.sleep(3)
            print("### Scene copied to: {} ###".format(new_path))

        except PermissionError as e:
            print("### Couldn't copy file: {} ###".format(e))
            return


        dl_priority, job_name, dl_comment, departement, machine_sel, f_start, f_end, _ = self.get_job_info(target_node.path(), new_path)

        new_scene = LOCAL_NAS_CACHE + new_path.split('PROD_CACHE', 1)[-1].replace('\\', '/')

        try:
            shutil.copyfile(new_path, new_scene)
        except:
            pass


        hip_dir = os.path.dirname(new_scene)

        print("### SCENE : {} ###".format(new_scene))

        dl_frames = f"{f_start}-{f_end}"

        cache_job = self.hou_cache_job(job_name, dl_comment, dl_priority, dl_frames, machine_sel)
        cache_plugin = self.hou_cache_plugin(new_scene, target_node.path(), nas_scene_dir, nas_cache_path)

        cmd = [self.deadline_ex, cache_job, cache_plugin]
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        stdout, stderr = proc.communicate()

        print(stdout + stderr)
        


class Resolver_Renders():
    def __init__(self, context:dataclass):
        self.curr_context = context
        self.deadline_hython = "C:\\Fireflies\\Fireflies_BIN\\Sidefx\\env\\deadline_hython_310.bat"

        self.get_render_parms()


    def get_render_parms(self):
        kt_curr_entity = self.curr_context.kt_entity_sel

        kt_task = gazu.task.get_task(kt_curr_entity['id'])
        kt_task_data = kt_task['entity']['data']        

        f_start = kt_task_data['frame_in']
        f_end = kt_task_data['frame_out']

        resolution_str = kt_task['project']['resolution']
        res_w, res_h = resolution_str.split('x')

        shot_name = kt_task['entity']['name']

        self.rm_render_parms_main = {
            "trange": {
                'value': "1", 
                'name': "Frame Range",
                'choices': [("0", "Render Current Frame"), ("1", "Render Frame Range")], 
                'type': 'menu'
            },
            "f1": {'value': f_start, 'name': 'Start Frame', 'type': 'float'},
            "f2": {'value': f_end, 'name': 'End Frame', 'type': 'float'},

            "cam": {'value': "/cameras/camera2", 'name': 'Camera', 'type': 'camera'},
            "resolution1": {'value': res_w, 'name': 'Resolution Width', 'type': 'int'},
            "resolution2": {'value': res_h, 'name': 'Resolution Height', 'type': 'int'},

            "xn__rihiderminsamples_n3af": {'value': "128", 'name': 'Min Samples', 'type': 'int'},
            "xn__rihidermaxsamples_n3af": {'value': "256", 'name': 'Max Samples', 'type': 'int'},
   
            "xn__riRiPixelVariance_n3ac": {'value': "0.01", 'name': 'Pixel Variance', 'type': 'float'},

            "dl_job_name": {'value': f"DELIVERY - {shot_name}", 'name': 'Job Name', 'type': 'str'},
            "dl_machine_list": {'value': "", 'name': 'Assign Workers', 'type': 'str'}
        }

        self.rm_render_parms_locked = {
            "unlock_path": 1,
            "output": "",
            "xn__rihiderminsamples_control_ohbf": "set",
            "xn__riRiPixelVariance_control_ohbc": "set",
            "xn__rihidermaxsamples_control_ohbf": "set",
            "dl_machine_sel": "1"
        }


    def submit_delivery(self, scene_path:str, render_settings_path:str,
                        validate_path:str):
        """
        Launches the script that creates the delivery scene 
        and sends the render jobs.
        """

        script_path = "C:\\Fireflies\\Fireflies_BIN\\fireflies\\houdini\\submit_delivery_job.py"

        proc_env = os.environ.copy()
        proc_env.pop("PYTHONPATH", None)
        proc_env.pop("PYTHONHOME", None)

        cmd = [self.deadline_hython, script_path, 
               '-scene_path', scene_path,
               '-render_settings', render_settings_path, 
               '-validate_path', validate_path
            ]

        proc = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=proc_env
        )

        stdout, stderr = proc.communicate()

        print(stdout, stderr)


if __name__ == "__main__":
    pass

