try:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance

except:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance


from datetime import datetime

import os
import sys
import pathlib

import gazu

from fireflies.context import prod_tracker
from fireflies.context.prod_tracker import CT_HOU, CT_MAYA, CT_NUKE

CONTEXT = prod_tracker.manage_context()


if CT_MAYA:
    import maya.cmds as cmds #type: ignore
    import maya.OpenMayaUI as omui #type: ignore
    import maya.mel as mel
    # import maya.OpenMaya as maya_api 

    from fireflies.maya import maya_utils

    parent = maya_utils.maya_main_window()

if CT_HOU:
    import hou


if __name__ == "__main__":
    app = QtWidgets.QApplication()

    import qdarktheme

    qdarktheme.setup_theme(
        theme='dark', 
        corner_shape='rounded',
        custom_colors= {
            "primary": "#C00000FF"
        } 

    )


class context_window(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(context_window, self).__init__(parent)

        self.setWindowTitle("Set Context")
        self.setMinimumSize(702, 850)
        # self.setMaximumSize(702, 850)

        self.f = open(r"C:\\Fireflies\\Common\\fmk_user_prefs\\user_prefs_dir.txt")
        # self.path = r"R:\\Christopher_LUCAS"
        self.path = os.path.normpath(self.f.read())

        self.create_widgets()

        self.update_prods()
        self.update_sequence()
        self.create_layout()
        self.create_connections()


    def get_flds(self):
        exclude_list = [
            "fireflies_tracker",
            "desktop.ini",
            ".SynologyWorkingDirectory"
        ]

        target_flds = [
            fld for fld in os.listdir(self.path) if fld not in exclude_list
        ]

        # for x, fld in enumerate(target_flds):
        #     if any(ex in fld for ex in exclude_list):
        #         target_flds.pop(x)
        # target_flds = [path for path in self.path.iterdir() if path.is_dir()]

        return target_flds
    

    def create_widgets(self):
        self.prod_combo = QtWidgets.QComboBox()
        # self.prod_combo.addItem("Prod")

        self.sequence_combo = QtWidgets.QComboBox()
        self.sequence_combo.addItem("Sequence")

        self.shots_combo = QtWidgets.QComboBox()
        self.shots_combo.addItem("Shot")

        self.tasks_combo = QtWidgets.QComboBox()
        self.tasks_combo.addItem("Task")
        self.tasks_combo.addItem("Model")
        self.tasks_combo.addItem("Lookdev")

        self.custom_name_line = QtWidgets.QLineEdit()

        ##########
        self.context_info = QtWidgets.QTableWidget()
        self.context_info.setColumnCount(2)
        # self.context_info.setColumnWidth(0, 200)
        self.context_info.setColumnWidth(0, 326)
        self.context_info.setColumnWidth(1, 175)
        # self.context_info.setColumnWidth(2, 175)
        
        self.context_info.setHorizontalHeaderLabels(["Scene", "Modified", "User"])
        # self.refresh_btn = QtWidgets.QPushButton("Refresh")
        header_view = self.context_info.horizontalHeader()
        header_view.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)


        self.ct_prod_btn = QtWidgets.QPushButton("Prod")
        self.ct_seq_btn = QtWidgets.QPushButton("Sequence")
        self.ct_shot_btn = QtWidgets.QPushButton("Shot")
        self.ct_task_btn = QtWidgets.QPushButton("Task")

        self.kt_info_table = QtWidgets.QTableWidget()
        self.kt_info_table.setColumnCount(1)
        self.kt_info_table.setRowCount(4)
        self.kt_info_table.setVerticalHeaderLabels(['Status', 'Start Date', 'Due Date', 'Assigned Artists'])
        self.kt_info_table.horizontalHeader().hide()
        kt_header_view = self.kt_info_table.verticalHeader()
        self.kt_info_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        for x in range(5):
            self.kt_info_table.setItem(0, x, QtWidgets.QTableWidgetItem('Waiting'))


        self.start_shot_btn = QtWidgets.QPushButton("Start/Save Shot")
        self.open_btn = QtWidgets.QPushButton("Open")
        self.close_btn = QtWidgets.QPushButton("Close")
        # self.debug_btn = QtWidgets.QPushButton("Debug")


    def create_layout(self):
        self.set_shots_layout = QtWidgets.QHBoxLayout()
        self.set_shots_layout.addWidget(self.prod_combo)
        self.set_shots_layout.addWidget(self.sequence_combo)
        self.set_shots_layout.addWidget(self.shots_combo)
        self.set_shots_layout.addWidget(self.tasks_combo)

        self.ct_layout = QtWidgets.QHBoxLayout()
        self.ct_layout.addWidget(self.ct_prod_btn)
        self.ct_layout.addWidget(self.ct_seq_btn)
        self.ct_layout.addWidget(self.ct_shot_btn)
        self.ct_layout.addWidget(self.ct_task_btn)

        self.kt_info_layout = QtWidgets.QVBoxLayout()
        self.kt_info_layout.addWidget(self.kt_info_table)

        self.bottom_btn_layout = QtWidgets.QHBoxLayout()
        self.bottom_btn_layout.addWidget(self.start_shot_btn)
        self.bottom_btn_layout.addWidget(self.open_btn)
        self.bottom_btn_layout.addWidget(self.close_btn)
        # self.bottom_btn_layout.addWidget(self.debug_btn)


        self.preview_layout = QtWidgets.QHBoxLayout()


        self.line_layout = QtWidgets.QFormLayout()
        self.line_layout.addRow("Custom name: ", self.custom_name_line)


        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.set_shots_layout)
        self.main_layout.addWidget(self.context_info)

        self.main_layout.addLayout(self.line_layout)
        self.main_layout.addLayout(self.ct_layout)
        self.main_layout.addLayout(self.preview_layout)
        # self.main_layout.addWidget(self.refresh_btn)

        self.main_layout.addLayout(self.kt_info_layout)

        self.main_layout.addStretch()
        self.main_layout.addLayout(self.bottom_btn_layout)


    def create_connections(self):
        self.close_btn.clicked.connect(self.close)

        # self.prod_combo.currentIndexChanged.connect(self.update_prods)
        self.prod_combo.currentIndexChanged.connect(self.update_sequence)
        self.sequence_combo.currentIndexChanged.connect(self.update_shots)
        self.shots_combo.currentIndexChanged.connect(self.update_tasks)
        # self.tasks_combo.currentIndexChanged.connect(self.update_tasks)
        self.shots_combo.currentIndexChanged.connect(self.refresh_scene_ath)
        self.tasks_combo.currentIndexChanged.connect(self.refresh_scene_ath)
        self.tasks_combo.currentIndexChanged.connect(self.update_kt_table)

        self.context_info.selectionModel().selectionChanged.connect(self.sel_changed)

        if prod_tracker.CT_HOU:
            self.start_shot_btn.clicked.connect(self.export_context_scene)
            self.open_btn.clicked.connect(self.open_scene)
        # self.context_info.selectionModel().selectionChanged.connect(self.import_preview)

        elif prod_tracker.CT_MAYA:
            self.start_shot_btn.clicked.connect(self.export_scene_maya)
            self.open_btn.clicked.connect(self.open_scene_maya)

        elif prod_tracker.CT_NUKE:
            self.start_shot_btn.clicked.connect(self.export_scene_nuke)
            self.open_btn.clicked.connect(lambda: self.export_scene_nuke(open_scene=True))


        # self.custom_name_line.textChanged.connect(self.test_print)

        self.start_shot_btn.clicked.connect(self.export_context_scene)


        self.ct_prod_btn.clicked.connect(lambda: self.create_target_fld("prod"))
        self.ct_seq_btn.clicked.connect(lambda: self.create_target_fld("seq"))
        self.ct_shot_btn.clicked.connect(lambda: self.create_target_fld("shot"))
        self.ct_task_btn.clicked.connect(lambda: self.create_target_fld("task"))


    def update_all(self):
        self.update_prods()
        self.update_sequence()
        self.update_shots()
        self.update_tasks()
        pass


    def create_target_fld(self, target:str):
        regular_targets = ["prod", "seq", "shot"]

        if any(name in target for name in regular_targets):

            self.win = pop_up_win()
            self.win.text_signal.connect(self.target_fld_callback)

            self.win.show()


        else:
            props_check = False
            if self.sequence_combo.currentText() == 'props':
                props_check = True

            self.win = task_win(props_check)
            self.win.task_signal.connect(self.target_fld_callback)

            self.win.show()


        self.current_target = target



    def target_fld_callback(self, target_name):
        prod = self.prod_combo.currentText()
        seq = self.sequence_combo.currentText()
        shot = self.shots_combo.currentText()

        props_check = False
        if any('props' in item for item in [target_name, seq]):
            props_check = True


        if self.current_target == "prod":
            init_path = self.path

        elif self.current_target == "seq":
            init_path = os.path.join(self.path, prod)
            
            if not props_check:
                CONTEXT.add_seq(target_name, prod)
 
        elif self.current_target == "shot":
            init_path = os.path.join(self.path, prod, seq)
            
            if not props_check:
                CONTEXT.add_shot(prod, seq, target_name)

        else: 
            init_path = os.path.join(self.path, prod, seq, shot)

            if not props_check:
                CONTEXT.add_task(prod, seq, shot, target_name)


        out_path = os.path.join(init_path, target_name)

        if not os.path.exists(out_path):
            os.makedirs(out_path)




    def test_print(self):
        self.build_scene_path()
        print(self.scene_name)


    def update_prods(self):
        for fld in self.get_flds():
            self.prod_combo.addItem(fld)
        
        self.prod_name = self.prod_combo.currentText()
        
        return


    def update_sequence(self):
        self.sequence_combo.clear()
        self.sq_name = self.prod_combo.currentText()
        
        self.seq_path = f"{self.path}\\{self.sq_name}"
        self.target_sequences = os.listdir(self.seq_path)
        
        for fld in self.target_sequences:
            self.sequence_combo.addItem(fld)


    def update_shots(self):
        self.shots_combo.clear()
        self.shot_name = self.sequence_combo.currentText()
        self.shots_path = f"{self.seq_path}\\{self.shot_name}"
        
        target_shots = os.listdir(self.shots_path)
        
        print(target_shots)
        
        for fld in target_shots:
            self.shots_combo.addItem(fld)
    

    def update_tasks(self):
        self.tasks_combo.clear()
        self.tasks_name = self.shots_combo.currentText()
        self.tasks_path = f"{self.shots_path}\\{self.tasks_name}"
        
        print(self.tasks_path)
        
        target_tasks = [
            task for task in os.listdir(self.tasks_path) if task in prod_tracker.TARGET_TASKS
        ]
        
        for fld in target_tasks:
            self.tasks_combo.addItem(fld)



    def build_scene_path(self):
        self.fullPath = f"{self.tasks_path}\\{self.tasks_combo.currentText()}"

        if prod_tracker.CT_MAYA:
            ext = ".mb"

        elif prod_tracker.CT_NUKE:
            ext = ".nk"

        elif prod_tracker.CT_HOU:
            ext = ".hipnc"


        if self.custom_name_line.text() == "":
            self.scene_name = f"{self.prod_combo.currentText()}_{self.sequence_combo.currentText()}_{self.shots_combo.currentText()}_{self.tasks_combo.currentText()}{ext}"
        
        else: 
            self.scene_name = f"{self.prod_combo.currentText()}_{self.sequence_combo.currentText()}_{self.shots_combo.currentText()}_{self.tasks_combo.currentText()}_{self.custom_name_line.text()}{ext}"

        self.export_path = f"{self.fullPath}\\{self.scene_name}"



    def refresh_scene_ath(self):
        # self.scenes_on_disk = os.listdir(self.build_scene_path[0])
        self.scenes_time = []

        init_path = f"{self.tasks_path}\\{self.tasks_combo.currentText()}"

        if prod_tracker.CT_MAYA:
            print("MAYAAAAAAAAAA")
            self.target_scenes = [f for  f in os.listdir(init_path) if f.endswith(".mb") or f.endswith(".ma")]

        elif prod_tracker.CT_NUKE:
            self.target_scenes = [f for  f in os.listdir(init_path) if f.endswith(".nk")]

        elif prod_tracker.CT_HOU:
            self.target_scenes = [f for  f in os.listdir(init_path) if f.endswith(".hip") or f.endswith("hipnc") or f.endswith("hiplc")]

        print(self.target_scenes)

        self.build_scene_path()

        for path in self.target_scenes:
            valid_path = os.path.join(self.fullPath, path)
            # print(valid_path)
            
            time_map = os.path.getmtime(valid_path)
            modified_time = datetime.fromtimestamp(time_map)

            self.scenes_time.append(str(modified_time))


        self.context_info.setRowCount(0)

        for x in range(len(self.target_scenes)):
            self.context_info.insertRow(x)
            self.add_item_context_info(x, 0, self.target_scenes[x])
            
            # if x < len(self.scenes_time):
            #     self.add_item_context_info(x, 1, self.scenes_time[x])
            self.add_item_context_info(x, 1, self.scenes_time[x])

        # self.export_preview()

        return self.target_scenes


    def add_item_context_info(self, row, column, text):
        item = QtWidgets.QTableWidgetItem(text)
        self.context_info.setItem(row, column, item)


    #linked to the context manager to gather task information from kitsu and display it
    def update_kt_table(self):
        self.build_scene_path()
        print(self.fullPath)

        if 'props' in self.fullPath.lower():
            print("### Not tracking props in the scene context ###")
            return

        kt_infos = CONTEXT.get_full_ct(self.fullPath)
        
        if not kt_infos:
            return

        self.kt_status = kt_infos['status']
        self.kt_start = kt_infos['start_date']
        self.kt_end = kt_infos['end_date']

        kt_user_list = kt_infos['assigned_users']
        map_users = map(str, kt_user_list)
        self.kt_assigned_user = ', '.join(map_users)

        self.kt_info_table.setItem(0, 0, QtWidgets.QTableWidgetItem(self.kt_status))
        self.kt_info_table.setItem(1, 0, QtWidgets.QTableWidgetItem(self.kt_start))
        self.kt_info_table.setItem(2, 0, QtWidgets.QTableWidgetItem(self.kt_end))
        self.kt_info_table.setItem(3, 0, QtWidgets.QTableWidgetItem(self.kt_assigned_user))



    def sel_changed(self):
        try:
            sel = self.context_info.selectedItems()[0]
            sel_name = sel.text()
            print(sel.text())
            return sel_name
        
        except:
            return        


    def open_scene(self):
        self.build_scene_path()
        open_path = f"{self.fullPath}/{self.sel_changed()}"
        print(open_path)
        
        hou.hipFile.load(open_path.replace("\\", "/"))
        self.close()


    def export_context_scene(self):
        self.build_scene_path()
        print(self.export_path)
        # cmds.file(rename=self.export_path)
        
        hou.hipFile.save(file_name=self.export_path)

        # cmds.file(save=True)
        # self.export_preview()
        self.close()


    def test(self):
        target_base = self.build_scene_path()
        # print(target_base)
        test_path = f"{self.tasks_path}\\{self.tasks_combo.currentText()}"
        
        self.target_scene = [
            f for  f in os.listdir(test_path) if f.endswith(".hip") or f.endswith("hipnc") or f.endswith("hiplc")
        ]

        for path in self.target_scene:
            valid_path = os.path.join(target_base, path)
            print(valid_path)


    def open_scene_maya(self):
        self.build_scene_path()

        init_path = self.fullPath.replace('\\', '/')
        open_path = f"{init_path}/{self.sel_changed()}"
        print(open_path)

        scene_dir = os.path.dirname(open_path)
        
        os.environ['MIP'] = scene_dir
        mel.eval(f'putenv "MIP" "{scene_dir}";')

        cmds.file(open_path, open=True, force=True)

        self.close()


    def export_scene_maya(self):
        self.build_scene_path()
        print(self.export_path)
        
        cmds.file(rename=self.export_path)
        cmds.file(save=True)
        
        # self.export_preview()
        self.close()


    def export_scene_nuke(self, open_scene:bool=None):
        self.build_scene_path()
        open_path = f"{self.fullPath}/{self.sel_changed()}"

        if open_scene:
            nuke.scriptOpen(open_path)

        else: 
            nuke.scriptSaveAs(self.export_path)

        print(self.export_path)

        self.close()





class pop_up_win(QtWidgets.QDialog):
    text_signal = QtCore.Signal(str)

    def __init__(self):
        super(pop_up_win, self).__init__()

        self.setWindowTitle("Set name")
        self.setMinimumSize(100, 50)
        
        self.create_elements()


    def create_elements(self):
        self.input_line = QtWidgets.QLineEdit()

        self.create_btn = QtWidgets.QPushButton("Create")
        self.close_btn = QtWidgets.QPushButton("Close")

        self.input_layout = QtWidgets.QFormLayout()
        self.input_layout.addRow("Name: ", self.input_line)

        
        self.btn_layout = QtWidgets.QHBoxLayout()
        self.btn_layout.addWidget(self.create_btn)
        self.btn_layout.addWidget(self.close_btn)
        
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.input_layout)
        self.main_layout.addLayout(self.btn_layout)

        self.create_btn.clicked.connect(self.out_val)
        self.close_btn.clicked.connect(self.close)


    def out_val(self):
        out_text = self.input_line.text()

        if out_text:
            print(out_text)
            self.text_signal.emit(out_text)

            # TRACKER.add_task(name=out_text)

        else: 
            print("No input detected")
            return

        self.accept()


class task_win(QtWidgets.QDialog):
    task_signal = QtCore.Signal(str)

    def __init__(self, target_props:bool=None):
        super(task_win, self).__init__()

        self.target_props = target_props

        self.setWindowTitle("Set name")
        self.setMinimumSize(100, 50)
        
        self.create_elements()


    def create_elements(self):
        self.task_combo = QtWidgets.QComboBox()

        self.create_btn = QtWidgets.QPushButton("Create")
        self.close_btn = QtWidgets.QPushButton("Close")

        self.input_layout = QtWidgets.QFormLayout()
        self.input_layout.addRow("Name: ", self.task_combo)

        
        self.btn_layout = QtWidgets.QHBoxLayout()
        self.btn_layout.addWidget(self.create_btn)
        self.btn_layout.addWidget(self.close_btn)
        
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.input_layout)
        self.main_layout.addLayout(self.btn_layout)

        self.create_btn.clicked.connect(self.out_val)
        self.close_btn.clicked.connect(self.close)

        target_tasks = prod_tracker.SHOT_TASKS

        if self.target_props:
            target_tasks = prod_tracker.ASSET_TASKS

        remove_targets = ['validate', 'to_validate']

        target_tasks = [item for item in target_tasks if item not in remove_targets]

        self.task_combo.addItems(target_tasks)


    def out_val(self):
        out_text = self.task_combo.currentText()

        if out_text:
            print(out_text)
            self.task_signal.emit(out_text)

        else: 
            print("No input detected")
            return

        self.accept()




if __name__ == "__main__":
    x = context_window()
    x.show()

    app.exec_()