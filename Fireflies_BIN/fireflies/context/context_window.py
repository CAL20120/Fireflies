from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

import os
import sys
import pathlib

import maya.cmds as cmds 
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

class context_window(QtWidgets.QDialog):
    def __init__(self):
        super(context_window, self).__init__()
        self.setWindowTitle("Set Context")
        self.setMinimumSize(702, 850)
        self.setMaximumSize(702, 850)

        self.f = open(r"C:\\Fireflies\\Common\\fmk_user_prefs\\user_prefs_dir.txt")
        # self.path = r"R:\\Christopher_LUCAS"
        self.path = os.path.normpath(self.f.read())

        self.create_widgets()
        self.update_prods()
        self.update_sequence()
        self.create_layout()
        self.create_connections()

    def maya_main_window():
        main_window_ptr = omui.MQtUtil.mainWindow()
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


    def get_flds(self):
        target_flds = os.listdir(self.path)
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

        ##########
        self.context_info = QtWidgets.QTableWidget()
        self.context_info.setColumnCount(3)
        # self.context_info.setColumnWidth(0, 200)
        self.context_info.setColumnWidth(0, 326)
        self.context_info.setColumnWidth(1, 175)
        self.context_info.setColumnWidth(2, 175)
        self.context_info.setHorizontalHeaderLabels(["Scene", "Modified", "User"])
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        header_view = self.context_info.horizontalHeader()
        header_view.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        self.start_shot_btn = QtWidgets.QPushButton("Start Shot")
        self.open_btn = QtWidgets.QPushButton("Open")
        self.close_btn = QtWidgets.QPushButton("Close")
        self.debug_btn = QtWidgets.QPushButton("Debug")

    def create_layout(self):
        self.set_shots_layout = QtWidgets.QHBoxLayout()
        self.set_shots_layout.addWidget(self.prod_combo)
        self.set_shots_layout.addWidget(self.sequence_combo)
        self.set_shots_layout.addWidget(self.shots_combo)
        self.set_shots_layout.addWidget(self.tasks_combo)

        self.bottom_btn_layout = QtWidgets.QHBoxLayout()
        self.bottom_btn_layout.addWidget(self.start_shot_btn)
        self.bottom_btn_layout.addWidget(self.open_btn)
        self.bottom_btn_layout.addWidget(self.close_btn)
        self.bottom_btn_layout.addWidget(self.debug_btn)



        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.set_shots_layout)
        self.main_layout.addWidget(self.context_info)
        self.main_layout.addWidget(self.refresh_btn)


        self.main_layout.addStretch()
        self.main_layout.addLayout(self.bottom_btn_layout)

    def create_connections(self):

        self.close_btn.clicked.connect(self.close)

        # self.prod_combo.currentIndexChanged.connect(self.update_prods)
        self.prod_combo.currentIndexChanged.connect(self.update_sequence)
        self.sequence_combo.currentIndexChanged.connect(self.update_shots)
        self.shots_combo.currentIndexChanged.connect(self.update_tasks)

        self.refresh_btn.clicked.connect(self.refresh_scene_ath)

        self.debug_btn.clicked.connect(self.test)
        self.start_shot_btn.clicked.connect(self.export_context_scene)
        # self.start_shot_btn.clicked.connect(self.export_context_scene)


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
        target_tasks = os.listdir(self.tasks_path)
        for fld in target_tasks:
            self.tasks_combo.addItem(fld)

    def build_scene_path(self):
        self.fullPath = f"{self.tasks_path}\\{self.tasks_combo.currentText()}"
        self.scene_name = f"{self.prod_name}_{self.sq_name}_{self.shot_name}_{self.tasks_combo.currentText()}.mb"
        self.export_path = f"{self.fullPath}\\{self.scene_name}"
        return self.fullPath

    def refresh_scene_ath(self):
        # self.scenes_on_disk = os.listdir(self.build_scene_path[0])
        test_path = f"{self.tasks_path}\\{self.tasks_combo.currentText()}"
        target_scenes = [f for  f in os.listdir(test_path) if f.endswith("mb") or f.endswith("ma")]
        self.context_info.setRowCount(0)

        for x in range(len(target_scenes)):
            for index, scenes in enumerate(target_scenes):
                print(index, scenes)
                self.context_info.insertRow(x)
            self.add_item_context_info(x, 0, scenes)

    def add_item_context_info(self, row, column, text):
        item = QtWidgets.QTableWidgetItem(text)
        self.context_info.setItem(row, column, item)   

    def export_context_scene(self):
        self.build_scene_path()
        cmds.file(rename=self.export_path)
        cmds.file(save=True)
        self.close()


    def test(self):
        self.build_scene_path()
        print(self.export_path)



if __name__ == "__main__":
    x = context_window()
    x.show()