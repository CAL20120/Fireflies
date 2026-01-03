import os 
import sys
import re

import subprocess 

from datetime import datetime
import random

import hou 

from fireflies.houdini import hou_utils
from fireflies.fireflies_utils import fireflies_requests

class hou_deadline_submitter():
    def __init__(self):
        self.hython_path = "C:\\Fireflies\\Common\\Houdini_vars\\houdini_205445\\Houdini20.5.445\\bin\\hython.exe"
        self.deadline_hython = "C:\\Fireflies\\Fireflies_BIN\\Sidefx\\env\\deadline_hython_310.bat"

        self.deadline_ex = "C:\\Fireflies\\Deadline\\bin\\deadlinecommand.exe"
        self.husk_ex = "C:\\Fireflies\\Fireflies_BIN\\Sidefx\\env\\husk_dl.bat"

        self.tmp_dir = os.environ.get('TMP')


    def write_target_file(self, file_path, content):
        with open(file_path, 'w') as f:
            f.write(content)

        return file_path


    def hou_job_info(self, job_name, frames, priority:str, comment, machine_sel:str) -> str:
        info_txt = 'Plugin=CommandLine\n' \
                    'Name={} [Write stage]\n' \
                    'Comment={}\n' \
                    'Pool=none\n' \
                    'Group=none\n' \
                    'Priority={}\n' \
                    'Department=Usd generation\n' \
                    'Frames={}\n' \
                    'ChunkSize=100\n' \
                    'MachineLimit=1\n' \
                    'ConcurrentTasks=1\n'.format(job_name, comment, priority, frames)


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
    

    def hou_render_job_info(self, job_name, priority:str, frames, id, department, comment, machine_sel:str) -> str:
        info_txt = 'Plugin=CommandLine\n' \
                    'Name={} [Render]\n' \
                    'Comment={}\n' \
                    'Pool=none\n' \
                    'Group=none\n' \
                    'Priority={}\n' \
                    'Department={}\n' \
                    'Frames={}\n' \
                    'ChunkSize=1\n' \
                    'JobDependency0={}\n'.format(job_name, comment, priority, department, frames, id)
        

        if machine_sel:
                info_txt += 'Allowlist={}\n'.format(machine_sel)
                print(f"### Selected Machine: {machine_sel} ###")
        
        target_path = os.path.join(self.tmp_dir, 'render_job_info.job')

        out = self.write_target_file(target_path, info_txt)

        return out


    def hou_render_plugin_info(self, usd_file:os.path, out_images) -> str:
        args = f'-R HdPrmanXpuLoaderRendererPlugin -V 1 -o {out_images} {usd_file}'

        plugin_txt = 'Executable={}\n' \
                    'Arguments={}\n' \
                    'StartupDirectory=\n' \
                    'SingleFramesOnly=False'.format(self.husk_ex, args)
        
        target_path = os.path.join(self.tmp_dir, 'render_plugin_info.job')

        out = self.write_target_file(target_path, plugin_txt)

        return out 
    


    def sumbit_usd_render_job(self):
        local_nas_prod = "Z:/PRODS"

        target_node = hou.pwd()
        scene_path = hou.hipFile.path()

        new_path = scene_path.split('PRODS', 1)
        # print(new_path)

        scene_path = local_nas_prod + new_path[-1]


        if not os.path.exists(local_nas_prod) and "PROD" not in scene_path:
            print("## Issue related to the PROD directory -- Exiting ##")
            return

        
        if not target_node.evalParm('cam'):
            print("## No camera was selecled -- Exiting ##")
            return

        node_job_name = target_node.evalParm('dl_job_name')
        
        if node_job_name:
            job_name = node_job_name

        else: 
            job_name = hou.hipFile.basename().rsplit('.', 1)[0]
        
        departement = scene_path.split('/')[-2]

        user_range = target_node.evalParm('trange')


        f_start = int(hou.frame())
        f_end = f_start

        if user_range != 0:
            f_start, f_end = hou.playbar.playbackRange()
            
            f_start = int(f_start)
            f_end = int(f_end)



        priority_ints = [10, 50, 100]
        priority_index = target_node.evalParm('dl_priority')

        dl_priority = priority_ints[priority_index]
        print("Selected priority: " + str(dl_priority))

        dl_comment = target_node.evalParm('dl_comment')

        out_images = target_node.evalParm('output')
        print(out_images)

        new_path = out_images.split('PRODS', 1)
        print(new_path)

        out_images = local_nas_prod + new_path[-1]

        target_frame = re.search(r'\d+', out_images)

        if not target_frame:
            print("### Couldn't find a frame number in the export path -- Exiting ###")

        # print(target_frame.group())

        out_images = out_images.replace(target_frame.group(), '$F')

        print(f"### EXPORT PATH: {out_images} ###")

        dl_path = out_images.replace('$F', '__target_frames__')
        # dl_path = hou.text.expandString(dl_path)

        # print(dl_path)

        out_dir = os.path.dirname(out_images)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)


        husk_out_images = dl_path.replace('__target_frames__', '<STARTFRAME>')

        if not out_images:
            print("### No path out path for the images was found -- Exiting ###")
            return
        
        hou.hipFile.save()


        dl_frames = f"{f_start}-{f_end}"


        scene_dir = os.path.dirname(scene_path)
        export_dir = os.path.join(scene_dir, "deadline_usd").replace('\\', '/')

        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        export_path = os.path.join(
            export_dir, "__render__.$F4.usd"
        ).replace("\\", '/')


        machine_sel = False
        if target_node.evalParm('dl_machine_sel'):
            machine_sel = target_node.evalParm('dl_machine_list')


        usd_export_job = self.hou_job_info(job_name, dl_frames, dl_priority, dl_comment, machine_sel)
        usd_export_plugin = self.hou_plugin_info(scene_path, target_node.path(), export_path)

        job_cmd = [self.deadline_ex, usd_export_job, usd_export_plugin]
        
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

        render_job = self.hou_render_job_info(job_name, dl_priority, dl_frames, usd_job_id, departement, dl_comment, machine_sel)
        render_plugin = self.hou_render_plugin_info(usd_file=husk_render_input, out_images=husk_out_images)

        render_job_cmd = [self.deadline_ex, render_job, render_plugin]

        render_proc = subprocess.Popen(
            render_job_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        stdout_job, stderr_job = render_proc.communicate()


if __name__ == "__main__":
    pass