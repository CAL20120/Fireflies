import os 
import sys 

from datetime import datetime
import subprocess
import re

import random

import collections

from functools import cache, lru_cache

# from fireflies.fireflies_utils.usd import fireflies_usd_viewer

from fireflies.context import prod_tracker

CURRENT_SCENE_PATH = None

CT_HOU = prod_tracker.CT_HOU
CT_MAYA = prod_tracker.CT_MAYA

#otherwise when we import this script in the standalone 
#assembly resolver it won't load
if CT_HOU:
    import hou
    from fireflies.houdini import hou_utils
    from pxr import Usd, UsdGeom, Sdf

    CURRENT_SCENE_PATH = hou.hipFile.path()

if CT_MAYA:
    import maya.cmds as cmds
    from fireflies.maya import maya_utils
    M_USD_UTILS = maya_utils.maya_usd()
    M_REGULAR_UTILS = maya_utils.maya_regular()

    CURRENT_SCENE_PATH = cmds.file(q=True, sn=True)

print(CURRENT_SCENE_PATH)

try:
    from PySide2 import QtCore, QtWidgets, QtGui

except:
    from PySide6 import QtCore, QtWidgets, QtGui


get_prod_path = lambda path: path.replace('\\', '/').rsplit("/", 4)[0].replace("/", os.sep)

class importer_window(QtWidgets.QDialog):
    import_target = QtCore.Signal(str)
    target_input = QtCore.Signal(str)

    def __init__(self, parent=None, import_classic:bool=None, prod_path:str=None):
        try: 
            parent = hou.qt.mainWindow()
        
        except:
            pass

        super(importer_window, self).__init__(parent)

        self.prod_path = prod_path
        print(self.prod_path)

        if self.prod_path is None:
            print("Couldn't resolve the production path")

        self.import_classic = import_classic
        self.target_input = None
        self.import_target = None

        self.setWindowTitle("Import USD Asset")
        self.setMinimumSize(750, 700)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.get_asset_paths()
        # self.import_comment()


    def get_asset_paths(self):
        if not self.prod_path:
            self.prod_path = get_prod_path(CURRENT_SCENE_PATH)
            print(self.prod_path)

        x = import_usd_asset(prod_path=self.prod_path)
        self.assets_name, self.assets_vars = x.find_asset()

        # self.assets_time = []
        # for path in self.paths:
        #     time_map = os.path.getmtime(path)
        #     modified_time = datetime.fromtimestamp(time_map)
        #     self.assets_time.append(str(modified_time))
        

        self.refresh_asset_table()


    def create_widgets(self):
        self.asset_table = QtWidgets.QTreeWidget()
        self.asset_table.setColumnCount(5)
        
        # self.header = self.asset_table.horizontalHeader()
        self.asset_table.setHeaderLabels(["Asset", "Version", "Type", "Path", "Date"])
        self.asset_table.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        # self.preview_btn = QtWidgets.QPushButton("Preview Asset")
        
        # self.refresh_btn = QtWidgets.QPushButton("Refresh")
        # self.asset_info_table = QtWidgets.QTableWidget()
        # self.asset_info_table.setColumnCount(4)
        # self.vertical_header = self.asset_info_table.verticalHeader()
        # self.asset_info_table.setHorizontalHeaderLabels(["Asset", "test", "4", "8"])

        # self.debug_btn = QtWidgets.QPushButton("debug")
        self.import_btn = QtWidgets.QPushButton("Import")
        self.close_btn = QtWidgets.QPushButton("Close")


    def create_layout(self):
        self.table_layout = QtWidgets.QVBoxLayout()
        self.table_layout.addWidget(self.asset_table)
        # self.table_layout.addWidget(self.preview_btn)
        # self.table_layout.addWidget(self.refresh_btn)

        self.asset_info_layout = QtWidgets.QHBoxLayout()
        # self.asset_info_layout.addWidget(self.asset_info_table)

        # self.metadata_layout = QtWidgets.QHBoxLayout()
        self.comment_layout = QtWidgets.QHBoxLayout()
        self.preview_layout = QtWidgets.QHBoxLayout()


        self.bottom_btn_layout = QtWidgets.QHBoxLayout()
        self.bottom_btn_layout.addWidget(self.import_btn)
        self.bottom_btn_layout.addWidget(self.close_btn)
        # self.bottom_btn_layout.addWidget(self.debug_btn)
            
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.table_layout)
        self.main_layout.addLayout(self.asset_info_layout)
        self.main_layout.addLayout(self.comment_layout)
        self.main_layout.addLayout(self.preview_layout)

        # self.main_layout.addStretch()
        self.main_layout.addLayout(self.bottom_btn_layout)


    def create_connections(self):
        self.close_btn.clicked.connect(self.close)
        # self.debug_btn.clicked.connect(import_usd_asset.find_asset)
        # self.refresh_btn.clicked.connect(self.refresh_asset_table)
        self.import_btn.clicked.connect(self.import_asset)       

        # self.asset_table.selectionModel().selectionChanged.connect(self.sel_changed)
        self.asset_table.selectionModel().selectionChanged.connect(self.import_comment)
        self.asset_table.selectionModel().selectionChanged.connect(self.import_preview)


    def refresh_asset_table(self):
        self.asset_table.clear()

        for name in self.assets_name:
            asset_item = QtWidgets.QTreeWidgetItem([name])
            
            self.asset_table.addTopLevelItem(asset_item)

            asset_versions = sorted(self.assets_vars[name].keys())


            target_tasks = []
            for version in asset_versions:
                for task in self.assets_vars[name][version].keys():
                    if task not in target_tasks:
                        target_tasks.append(task)


            for task in target_tasks:
                target_tasks_version = [
                    version for version in asset_versions if task in self.assets_vars[name][version]
                ]

                target_tasks_version = sorted(target_tasks_version)

                init_version = target_tasks_version[0]
                asset = self.assets_vars[name][init_version][task]

                child = QtWidgets.QTreeWidgetItem([task])
                asset_item.addChild(child)

                child.setText(2, asset['type'])

                self.version_combo = QtWidgets.QComboBox()
                self.version_combo.addItems(target_tasks_version)
                self.version_combo.setProperty('asset', name)
                self.version_combo.setProperty('task', task)
                self.version_combo.setProperty('child', child)

                self.version_combo.currentTextChanged.connect(self.refresh_version)
                self.version_combo.currentTextChanged.connect(self.import_comment)
                self.version_combo.currentTextChanged.connect(self.import_preview)

                self.asset_table.setItemWidget(child, 1, self.version_combo)

                asset_path = asset['path'] if asset['type'] == "asset" else asset['frames'][0]['path']

                child.setText(3, asset_path)

                time_map = os.path.getmtime(asset_path)
                modified_time = datetime.fromtimestamp(time_map)
                child.setText(4, str(modified_time))

            asset_item.setExpanded(True)

        # self.asset_table.setRowCount(0)

        # for x, asset in enumerate(self.assets_name):
        #     asset_versions = list(self.assets_vars[asset].keys())

        #     self.asset_table.insertRow(x)
        #     self.add_item(x, 0, asset)

        #     self.version_combo = QtWidgets.QComboBox()
        #     self.version_combo.addItems(asset_versions)
        #     self.version_combo.setProperty('row', x)

        #     self.version_combo.currentTextChanged.connect(self.refresh_version)
        #     self.asset_table.setCellWidget(x, 1, self.version_combo)

        #     target_version = asset_versions[0]

        #     target_asset = self.assets_vars[asset][target_version]
        #     target_type = target_asset['type']

        #     if target_type == "asset":
        #         asset_path = target_asset['path']

        #     elif target_type == "sequence":
        #         asset_path = target_asset['frames'][0]['path']

        #     self.add_item(x, 2, target_type)

        #     self.add_item(x, 3, asset_path)

        #     time_map = os.path.getmtime(asset_path)
        #     modified_time = datetime.fromtimestamp(time_map)
        #     self.add_item(x, 4, modified_time)


        # for x in range(len(self.assets)):
        #     self.combo_test = QtWidgets.QComboBox()
        #     self.asset_table.insertRow(x)
        #     self.add_item(x, 0, self.assets[x])

        #     self.combo_test.addItem(self.assets[x])
        #     self.asset_table.setCellWidget(x, 1, self.combo_test)

        #     self.add_item(x, 2, self.paths[x])
        #     self.add_item(x, 3, self.assets_time[x])
        #     # self.add_item(x, 2, str(self.date_ft[x]))
        #     # self.add_item(x, 3, self.user_ft[x])


    def refresh_version(self):

        #we need the get the qt signel to know which version changed in the ui
        target_combo = self.sender()

        child = target_combo.property('child')
        asset_name = target_combo.property('asset')
        task = target_combo.property('task')

        sel = target_combo.currentText()
        
        asset = self.assets_vars[asset_name][sel][task]

        asset_path = asset['path'] if asset['type'] == "asset" else asset['frames'][0]['path']

        child.setText(2, asset['type'])
        child.setText(3, asset_path)

        time_map = os.path.getmtime(asset_path)
        modified_time = datetime.fromtimestamp(time_map)
        child.setText(4, str(modified_time))


    def add_item(self, row, column, text) -> QtWidgets:
        item = QtWidgets.QTableWidgetItem(str(text))
        self.asset_table.setItem(row, column, item)


    def sel_changed(self):
        sel_item = self.asset_table.selectedItems()
        sel = sel_item[0]
        sel_name = sel.text()
        print(sel_name)
        item_index = sel_item[0].row()
        print(item_index)
        
        return sel_name, item_index


    def get_asset_data(self, output_task:bool=None) -> str:
        current_sel = self.asset_table.selectedItems()
        if not current_sel:
            print("No current selection")
            return
        
        target_task = current_sel[0]
        target_parent = target_task.parent()
        
        asset_name = target_parent.text(0)
        print(asset_name)

        task_name = target_task.text(0)

        # print(asset_name)

        target_combo = self.asset_table.itemWidget(target_task, 1)
        asset_version = target_combo.currentText()

        target_version = self.assets_vars[asset_name][asset_version][task_name]
        target_type = target_version['type']

        asset_path = target_version['path'] if target_type == "asset" else target_version['frames'][0]['path']

        if output_task:
            return asset_path, target_type, asset_name, task_name

        else:
            return asset_path, target_type, asset_name


    def import_asset(self):
        asset_path, asset_type, asset_name, current_task = self.get_asset_data(output_task=True)

        print(asset_name)

        # print(type(asset_path))
        # print(asset_path)
        
        # print(type(asset_type))
        # print(asset_type)
        
        hip_path = None
        if CT_HOU:
            utils = hou_utils.hou_usd()

            hip_path = utils.path_converter(path=asset_path)
            out_path = hip_path

            if self.import_classic:
                if asset_type == "asset":
                    utils.import_prod_usd_asset(asset_path=out_path)

                elif asset_type == "sequence":
                    utils.import_usd_sequence(asset_path=out_path)

            else:
                try:
                    if self.target_input:
                        self.import_target.parm(self.target_input).set(out_path)

                    # if not self.import_classic: 
                    self.import_target.parm('input_file').set(out_path)

                except:
                    print("### Error when trying to set path ###")

                try:
                    self.import_target.parm('current_task').set(current_task)
                    self.import_target.parm('`asset_name`').set(str(asset_name))

                except:
                    pass


        if CT_MAYA:

            
            if current_task == 'rig':
                M_REGULAR_UTILS.reference_maya_scene(scene_path=asset_path)

            if asset_type == "sequence":
                M_USD_UTILS.import_usd_animation(animation_path=asset_path, asset_name=asset_name)

            else:
                M_USD_UTILS.import_usd_asset(asset_path=asset_path, asset_name=asset_name)


        # print(asset_path)
        self.out_name = asset_name
        self.out_type = asset_type
        print(self.out_name)
        print(self.out_type)

        self.accept()

        if not hip_path:
            hip_path = "Undefined"

        return asset_name, asset_type, hip_path



    def import_comment(self):
        children = []
        for x in range(self.comment_layout.count()):
            child = self.comment_layout.itemAt(x).widget()
            
            if child:
                children.append(child)
        

        for child in children:
            child.deleteLater()

        current_sel = self.asset_table.selectedItems()
        current_task  = current_sel[0]
        parent = current_task.parent()
        name = parent.text(0)

        self.text_edit_comment = QtWidgets.QTextEdit()
        self.text_edit_comment.setReadOnly(True)

        # asset_path = self.get_asset_path()
        # path = os.path.dirname(asset_path)

        asset_path, _, _ = self.get_asset_data()

        version_path = os.path.dirname(asset_path)
        target_file = f"{version_path}/metadata/commentary/{name}_comment.txt"
        print(target_file)

        with open(target_file, "r") as f:
            comment = f.read()
        
        self.text_edit_comment.setPlainText(comment)

        self.comment_layout.addWidget(self.text_edit_comment)


    # def show_preview(self):
    #     _, index = self.sel_changed()
    #     self.x = hou_utils.hou_usd()
        
    #     target_path = self.paths[index]
    #     print(target_path)
    #     self.x.show_preview(asset_path=target_path)


    def import_preview(self):
        children = []
        for x in range(self.preview_layout.count()):
            child = self.preview_layout.itemAt(x).widget()
            
            if child:
                children.append(child)
        
        
        for child in children:
            child.deleteLater()

        current_sel = self.asset_table.selectedItems()
        current_task  = current_sel[0]
        parent = current_task.parent()
        name = parent.text(0)

        asset_path, _, _ = self.get_asset_data()
        version_path = os.path.dirname(asset_path)
        target_file = f"{version_path}/metadata/preview/{name}_preview.jpg"

        if os.path.exists(target_file):
            label = QtWidgets.QLabel()

            texture = QtGui.QPixmap(target_file)
            label.setPixmap(
                texture.scaled(426, 240, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            )

            self.preview_layout.addWidget(label)


class import_usd_asset():
    def __init__(self, prod_path:str=None):
        super(import_usd_asset, self).__init__()

        self.prod_path = prod_path
        
        if not any([CURRENT_SCENE_PATH, prod_path]):
            return

        if not prod_path:
            self.prod_path = get_prod_path(CURRENT_SCENE_PATH)
        
    # @lru_cache(maxsize=None)
    def find_asset(self) -> str | collections.defaultdict:
        """
        the purpose here is to build a dict with each assets and its version to 
        make the asset versions tracking easier 
        """

        self.assets_vars = collections.defaultdict(dict)


        # self.result_dirs = []
        # self.result_published = []
        # self.result_usd_path = []


        target_ext = [".usd", ".mb"] if CT_MAYA else [".usd"]
        exclude_tasks = ['to_validate']

        #important usd files but we import them if needed, we only want to get
        #or display the main tasks and assets
        exclude_names = ['topology', 'manifest', 'master']

        self.usd_publied_dir = []
        for root, subdir, files in os.walk(self.prod_path):
            if CT_MAYA:
                target_fld = next(
                    (target for target in ["usd_published", "mb_published"] if target in subdir), None
                )

                if target_fld in subdir:
                    self.usd_publied_dir.append(os.path.join(root, target_fld))

            else:
                if "usd_published" in subdir:
                    self.usd_publied_dir.append(os.path.join(root, "usd_published"))


        self.assets = []
        for dirs in self.usd_publied_dir:
            
            for asset in os.listdir(dirs):
                asset_dir = os.path.join(dirs, asset)

                if os.path.isdir(asset_dir):
                    self.assets.append(asset_dir)


        self.asset_versions = []
        for asset_dir in self.assets:
            asset_name = os.path.basename(asset_dir)

            for version in os.listdir(asset_dir):
                version_dir = os.path.join(asset_dir, version)

                if not os.path.isdir(asset_dir):
                    continue

                #we do not want to get the metadata folder otherwise in the dict 
                #we get keys related to the metadata
                target = re.match(rf"{asset_name}_(\d+)$", version)
                if not target:
                    continue

                self.asset_versions.append(version_dir)


        self.asset_file = []
        for version_dir in self.asset_versions:
            # print(version_dir) 
            for file in os.listdir(version_dir):
                # print(target_ext)
                if any(ext for ext in target_ext if file.endswith(ext)):
                    asset_path = os.path.join(version_dir, file)
                    correct_path = asset_path.replace("\\", "/")
                    
                    self.asset_file.append(correct_path)


        #time to build the dict
        for asset in self.asset_file:
            file = os.path.basename(asset)

            version_fld = os.path.basename(os.path.dirname(asset))
            target_version = re.search(r'(\d+)$', version_fld)

            if not target_version:
                continue

            target_dir = os.path.dirname(asset)
            current_task = self.find_current_task(target_dir=target_dir)

            version_path = f"{int(target_version.group()):03d}"

            asset_pattern = re.compile(r'(.*)\.usd$')
            anim_pattern = re.compile(r'(.+?)_(\d+)\.usd$')

            if current_task == 'rig':
                asset_pattern = re.compile(r'(.*)\.mb$')


            asset_target = asset_pattern.match(file)
            anim_target = anim_pattern.match(file)

            #we need to find the related task

            if any([CT_HOU, CT_MAYA]):
                if any(task for task in exclude_tasks if task in current_task):
                    continue

            
            if asset_target and not anim_target:
                name = asset_target.group(1)
                
                if any(substr in name for substr in exclude_names):
                    continue

                # if version_path not in self.assets_vars[name]:
                #     self.assets_vars[name][version_path] = {}

                asset_dict = self.assets_vars[name].setdefault(version_path, {})

                # self.assets_vars[name][version_path][current_task] = {
                #     "type": "asset",
                #     "path": asset
                # }

                target = asset_dict.setdefault(
                    current_task,
                    {
                        "type": "asset",
                        "path": asset
                    }
                )

                continue

            if anim_target:
                name = anim_target.group(1)
                frame = int(anim_target.group(2))

                anim_dict = self.assets_vars[name].setdefault(version_path, {})

                #important to use setdefault to create a value for each frame
                target = anim_dict.setdefault(
                    current_task,
                    {
                        "type": "sequence",
                        "frames": []
                    }
                )

                target['frames'].append(
                    {
                        "frame": frame,
                        "path": asset
                    }
                )
                continue

        # for dir, subdir, files in os.walk(self.prod_path):
        #     if "usd_published" in dir:
        #         self.result_dirs.append(dir)

        # for index, dir in enumerate(self.result_dirs):
        #     for file in os.listdir(dir):
                
        #         if file.endswith(".usd"):
        #             self.result_published.append(file.rsplit(".", 1)[0])
        #             usd_path = os.path.join(dir, file).replace("\\", "/")
        #             self.result_usd_path.append(usd_path)

        # return self.result_published, self.result_usd_path


        # print(self.assets_vars)

        return list(self.assets_vars.keys()), self.assets_vars


    def find_asset_by_name(self, asset_name):
        _, asset_vars = self.find_asset()

        target_asset = self.assets_vars.get(asset_name)

        return target_asset



    def find_current_task(self, target_dir:str) -> str:
        target_tasks = prod_tracker.TARGET_TASKS

        target_match = []
        for task in target_tasks:
            index = target_dir.find(task)

            if index != -1:
                target_match.append((index, task))


        if target_match:
            # print(target_match)
            target_match.sort()

            return target_match[0][1]

        # if tasks_iter:
        #     current_task = tasks_iter
        #     return current_task

        else:
            # print("no task found")
            pass



if __name__ == "__main__":
    x = importer_window(import_classic=True)
    x.show()

# x = import_usd_asset()
# x.find_asset()

