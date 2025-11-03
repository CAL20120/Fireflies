#this tool is made for creating quick and automated previz within houdini
from datetime import datetime

import os

import hou

from PySide2 import QtWidgets, QtCore, QtGui

from fireflies.houdini import hou_utils

class quick_previz(QtWidgets.QDialog):
    def __init__(self):
        super(quick_previz, self).__init__()
        self.scene_path = hou.hipFile.path().rsplit("/", 1)[0]
        self.scene_name = self.scene_path.rsplit("/")[-1]


        self.setWindowTitle("Quick Previz")
        self.setMinimumSize(150, 50)

        self.create_widgets()
        self.create_layout()
        self.create_connections()


    def create_widgets(self):
        self.current_frame_btn = QtWidgets.QPushButton("Single Frame")

        self.frame_range_btn = QtWidgets.QPushButton("Frame Range")


    def create_layout(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.addWidget(self.current_frame_btn)
        self.main_layout.addWidget(self.frame_range_btn)

    
    def create_connections(self):
        self.current_frame_btn.clicked.connect(self.render_single_frame)
        self.frame_range_btn.clicked.connect(self.render_frame_range)

    
    def render_single_frame(self):
        self.quick_preview(single_frame=True)


    def render_frame_range(self):
        self.quick_preview(single_frame=False)



    def quick_preview(self, single_frame: bool):
        print("creating previz")

        current_time = datetime.now()

        desktop = hou.ui.curDesktop()
        target_pane = desktop.paneTabOfType(hou.paneTabType.SceneViewer)

        viewport = target_pane.curViewport()

        time_output = f"{current_time.year}_{current_time.month}_{current_time.day}_{current_time.hour}_{current_time.minute}"
        output = f"{self.scene_path}/quick_preview/{time_output}/{self.scene_name}_$F4.png"

        output_dir = f"{self.scene_path}/quick_preview/{time_output}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # f_start, f_end = hou.playbar.playbackRange()

        fbk_settings = target_pane.flipbookSettings().stash()
        
        if single_frame: 
            fbk_settings.frameRange((hou.frame(), hou.frame()))
        
        else:
            f_start, f_end = hou.playbar.playbackRange()
            fbk_settings.frameRange((f_start, f_end))

        fbk_settings.useResolution(True)
        fbk_settings.resolution((2560, 1440))
        fbk_settings.output(output)

        target_pane.flipbook(viewport, fbk_settings)

        print("preview exporter to: {}".format(output))


# def quick_previz_hou(scene_path):
#     print(scene_path)
#     images_out = "{}\\images".format(scene_path.rsplit("/", 1)[0])
    
#     if not os.path.exists(images_out):
#         os.makedirs(images_out)

#     scene_path = scene_path.replace("\\", "/")
#     print(scene_path)

#     task_path = scene_path.rsplit("/", 1)[0]
#     output_path = f"{task_path}/previz"

#     #we load into the file to launch the previz job
#     hou.hipFile.load(file_name=scene_path, ignore_load_warnings=True)

#     cur_desktop = hou.ui.curDesktop()
#     scene_viewer = hou.paneTabTtype.SceneViewer
#     print(scene_viewer.name())
#     scene = cur_desktop.paneTabOfType(scene_viewer)

#     f_start, f_end = hou.playbar.playbackRange()
    
#     scene.flipbookSettings().stash()
#     flip_options = scene.flipbookSettings()
    
#     flip_options.frameRange((f_start, f_end))
#     flip_options.useResolution(True)
#     flip_options.useResolution(2560, 1140)

#     flip_options.output(f"{images_out}/quick_previz_$F4.jpeg")
    
#     scene.flipbook(scene.curViewport(), flip_options)



x = quick_previz()
x.show()