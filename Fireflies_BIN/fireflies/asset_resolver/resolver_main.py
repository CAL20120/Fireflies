import os
import sys
import re
from datetime import datetime

import pathlib

import subprocess

from PySide2 import QtCore, QtWidgets, QtGui
from qt_material import apply_stylesheet, list_themes


#to get the asset vars dict
from fireflies.fireflies_utils.usd import usd_asset_importer_hou, fireflies_usd_viewer


from pxr import Usd, UsdGeom, Vt, Ar, Sdf



app = QtWidgets.QApplication.instance()

if app is None:
    app = QtWidgets.QApplication(sys.argv)

# print(list_themes())
apply_stylesheet(app, theme="dark_blue.xml")


class Resolver_window(QtWidgets.QDialog):
    def __init__(self):
        super(Resolver_window, self).__init__()

        app_icon = QtGui.QIcon("C:\\Fireflies\\Fireflies_BIN\\fireflies\\logos\\assembly_maker.png")
        self.setWindowIcon(app_icon)

        self.setWindowTitle("Fireflies Asset Resolver")
        self.setMinimumSize(1300, 950)
        # self.setStyleSheet("background-color:gray;")

        self.create_widgets()
        self.create_layout()

        self.get_prod_data()
        self.refresh_prod_combo()

        self.create_connections()

        # self.refresh_win()
        self.usd_viewer = None
        self.task_preview = None
        self.task_comment = None


    def get_prod_data(self):
        prefs_path = open(r"C:\\Fireflies\\Common\\fmk_user_prefs\\user_prefs_dir.txt")
        self.prod_dir = os.path.normpath(prefs_path.read())

        if not self.prod_dir:
            raise Exception(
                "Prod PATH couldn't not be found, please reference it in the framework."
            )

        self.prod_paths = []

        for path in os.listdir(self.prod_dir):
            target_exclude = [
                "synology",
                ".ini"
            ]

            if any(substr in path.lower() for substr in target_exclude):
                continue

            current_path = os.path.join(self.prod_dir, path)
            self.prod_paths.append(current_path)
            # print(path)

        self.asset_finder = usd_asset_importer_hou.import_usd_asset()


        if self.prod_combo.count() == 0:
            self.asset_finder.prod_path = self.prod_paths[0]
        else: 
            self.asset_finder.prod_path = self.prod_paths[self.prod_combo.currentIndex()]


        self.asset_name, self.asset_vars = self.asset_finder.find_asset()
        
        # print(self.asset_vars)

        # print("##########")
        # print(self.prod_paths[1])
        # print("##########")

        self.refresh_win()


    def create_widgets(self):
        self.test_btn = QtWidgets.QPushButton("debug")
        self.prod_label = QtWidgets.QLabel('PRODS: ')

        self.prod_combo = QtWidgets.QComboBox()

        self.update_btn = QtWidgets.QPushButton("Update assembly")

        self.published_assets_table = QtWidgets.QTableWidget()
        self.published_assets_table.setColumnCount(2)
        self.published_assets_table.setColumnWidth(0, 300)
        self.published_assets_table.setHorizontalHeaderLabels(['Published Assembly', ''])
        # self.published_assets_table.setSelectionModel

        published_headerview = self.published_assets_table.horizontalHeader()
        published_headerview.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)


        # self.asset_info_table = QtWidgets.QTableWidget()
        # self.asset_info_table.setColumnCount(1)


        self.version_tree = QtWidgets.QTreeWidget()
        self.version_tree.setColumnCount(2)

        self.version_tree.setHeaderLabels(['Task', 'Changed Version'])
        self.version_tree.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)


        # info_header = self.asset_info_table.verticalHeader()
        # info_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

    def create_layout(self):
        self.top_layout = QtWidgets.QVBoxLayout()
        self.top_layout.addWidget(self.prod_label)
        self.top_layout.addWidget(self.prod_combo)
        # self.top_layout.addWidget(self.test_btn)

        self.asset_layout = QtWidgets.QHBoxLayout()
        self.asset_layout.addWidget(self.published_assets_table)


        self.table_layout = QtWidgets.QHBoxLayout()
        self.table_layout.addWidget(self.version_tree)


        # self.table_layout.addWidget(self.asset_info_table)


        self.btn_layout = QtWidgets.QHBoxLayout()
        self.btn_layout.addWidget(self.update_btn)


        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.top_layout)
        # self.main_layout.addStretch()

        self.main_layout.addLayout(self.asset_layout)

        # self.main_layout.addStretch()
        self.main_layout.addLayout(self.table_layout)

        self.main_layout.addLayout(self.btn_layout)



    def create_connections(self):
        # self.test_btn.clicked.connect(self.debug_func)
        
        self.prod_combo.currentIndexChanged.connect(self.get_prod_data)
        self.prod_combo.currentIndexChanged.connect(self.get_task_meta)


        self.published_assets_table.selectionModel().selectionChanged.connect(self.refresh_asset_info)
        self.published_assets_table.selectionModel().selectionChanged.connect(self.preview_asset)

        self.version_tree.selectionModel().selectionChanged.connect(self.get_task_meta)

        self.update_btn.clicked.connect(self.update_local_layers)


    def refresh_prod_combo(self):
        # self.prod_combo.clear()
        # self.prod_combo.addItems(os.path.dirname(self.prod_paths))
        
        for x, asset in enumerate(self.prod_paths):
            self.prod_combo.addItem(os.path.basename(asset))



    def refresh_win(self):
        print("Refresh")

        self.published_assets_table.setRowCount(0)
        # self.asset_info_table.setRowCount(0)

        self.asset_dir = []
        self.target_name = []

        self.asset_path = []

        target_task = "assembly"

        for name in self.asset_name:
            asset_versions = sorted(self.asset_vars[name].keys())

            for version in reversed(asset_versions):
                tasks = self.asset_vars[name][version].keys()
                
                for task in tasks:
                    if target_task not in task:
                        continue

                    print(task)
                    if name not in self.target_name:
                        self.target_name.append(name)
                        
                        path = self.asset_vars[name][version][target_task]['path']
                        self.asset_path.append(path)
                        break


        print(self.asset_path)

        for x in range(len(self.target_name)):
            published_date = self.get_useful_data(
                self.asset_path[self.published_assets_table.currentRow()]
            )

            print(published_date)

            self.published_assets_table.insertRow(x)
            # self.asset_info_table.insertRow(x)
            
            self.add_item(x, 0, self.target_name[x], table=self.published_assets_table)
            self.published_assets_table.setCellWidget(
                x, 1, self.get_preview(
                    asset_path=self.asset_path[x], name=self.target_name[x]
                )
            )

            self.published_assets_table.setRowHeight(x, 120)

            # self.add_item(0, 0, published_date, table=self.asset_info_table)



    def refresh_asset_info(self):
        # self.asset_info_table.setRowCount(0)

        print("###########")

        asset_sel = self.published_assets_table.currentRow()
        print(asset_sel)

        # if asset_sel < 1:
        #     print("No current selection")
        #     return


        # self.asset_info_table.setRowCount(len(self.target_name))


        published_date = self.get_useful_data(
            self.asset_path[asset_sel]
        )

        print(published_date)
        # for x in range(len(self.target_name)):
        #     print(x)

        # self.add_item(0, 0, published_date, table=self.asset_info_table)

        # self.get_current_layers()

        # self.add_item(1, 0, self.asset_data, table=self.asset_info_table)

        # self.asset_info_table.setVerticalHeaderLabels(['Date', 'Current versions'])
        # info_header = self.asset_info_table.verticalHeader()
        # info_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Interactive)


        self.manage_asset_tree()


        # self.asset_info_table.setRowCount(0)

        # self.add_item(0, 0, published_date, table=self.asset_info_table)


    def add_item(self, row, column, text, table:QtWidgets.QTableWidget) -> QtWidgets:
        item = QtWidgets.QTableWidgetItem(str(text))
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        
        table.setItem(row, column, item)


    def get_useful_data(self, asset_path:str):
        time_map = os.path.getmtime(asset_path)
        modified_time = datetime.fromtimestamp(time_map)

        return str(modified_time)


    def get_preview(self, asset_path, name) -> QtGui.QPixmap:
        label = QtWidgets.QLabel()

        asset_dir = os.path.dirname(asset_path)

        target_file = f"{asset_dir}/metadata/preview/{name}_preview.jpg"

        texture = QtGui.QPixmap(target_file)

        label.setPixmap(
            texture.scaled(213, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        )

        return label
    

    def debug_func(self):
        self.update_local_layers()


    def preview_asset(self):
        if self.usd_viewer:
            self.usd_viewer.deleteLater()

        asset_sel = self.published_assets_table.currentRow()

        asset_path = self.asset_path[asset_sel]

        # subprocess.run(
        #     [
        #         sys.executable,
        #         r'C:\Fireflies\Fireflies_BIN\fireflies\fireflies_utils\usd\fireflies_usd_viewer.py', 
        #         "-asset_path",
        #         asset_path
        #     ],
        #     shell=True
        # )
        
        self.usd_viewer = fireflies_usd_viewer.Usd_Viewer_hou()
        self.usd_viewer.load_stage(asset_path)

        self.asset_layout.addWidget(self.usd_viewer)


    def get_task_meta(self):
        if self.task_preview or self.task_comment:
            try: 
                self.task_preview.deleteLater()
                self.task_comment.deleteLater()
            
            except: 
                self.task_preview = None
                self.task_comment = None


        sel = self.version_tree.selectedItems()

        if not sel:
            print("You may select a task")
            return

        current_task = sel[0]

        if current_task.parent() == None:
            print("You may select a task")
            return

        task_name = current_task.text(0)

        current_asset_sel = self.published_assets_table.currentRow()
        if current_asset_sel < 0:
            return

        name = self.target_name[current_asset_sel]

        target_combo = self.version_tree.itemWidget(current_task, 1)
        
        target_version = target_combo.currentText()

        asset = self.asset_vars[name][target_version][task_name]
        asset_path = asset['path'] if asset.get('type') == "asset" else None


        if not os.path.exists(asset_path):
            print("Stage file does not exists")
            return


        self.task_preview = QtWidgets.QLabel()

        asset_dir = os.path.dirname(asset_path)

        target_dir = f"{asset_dir}/metadata/"

        target_file = f"{target_dir}/preview/{name}_preview.jpg"
        target_comment = f"{target_dir}/commentary/{name}_comment.txt"

        
        exist_test = [target_file, target_comment]

        for path in exist_test:
            if not os.path.exists(path):
                print("Couldn't find the related task metadata")
                return


        texture = QtGui.QPixmap(target_file)

        self.task_preview.setPixmap(
            texture.scaled(426, 240, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        )


        self.task_comment = QtWidgets.QTextEdit()
        self.task_comment.setReadOnly(True)
        

        with open(target_comment, "r") as f:
            comment = f.read()

        self.task_comment.setPlainText(comment)

        self.table_layout.addWidget(self.task_preview)
        self.table_layout.addWidget(self.task_comment)



    def get_current_layers(self) -> Sdf:
        self.asset_data = []

        target_stage = self.asset_path[self.published_assets_table.currentRow()]

        if not os.path.exists(target_stage):
            print("Target stage does not exists")
            return

        stage = Usd.Stage.Open(target_stage)

        # print(stage)

        root = stage.GetRootLayer()

        print("#### CURRENT SUBLAYERS ####")

        target_layers = []
        self.current_tasks = []
        for path in root.subLayerPaths:
            # path = os.path.abspath(path)
            # print(path)

            current_task = self.asset_finder.find_current_task(target_dir=path)
            if current_task:
                print(current_task)
                print("current task: %s" %current_task + "\n %s" %path)
                

            path_object = pathlib.Path(path)

            task_var = path_object.parts[-2].rsplit('_', 1)[-1]

            print(task_var)

            name = path_object.stem
            target_local_var = self.asset_vars[name][task_var][current_task]
            print(target_local_var)
        
            self.asset_data.append(current_task)
            self.asset_data.append(task_var)
            self.current_tasks.append(current_task)




    def manage_asset_tree(self):
        print("#### Refreshing asset tree ####")

        self.version_tree.clear()
        
        asset_row = self.published_assets_table.currentRow()
        
        # if asset_row <= 0:
        #     print("No asset selected")
        #     return

        current_name = self.target_name[asset_row]
        print(self.asset_name)
        print(current_name)

        stage_path = self.asset_path[asset_row]

        current_tasks = []

        if os.path.exists(stage_path):
            stage = Usd.Stage.Open(stage_path)
            root_layer = stage.GetRootLayer()

            for path in root_layer.subLayerPaths:
                target_task = self.asset_finder.find_current_task(target_dir=path)

                if target_task and target_task not in current_tasks:
                    current_tasks.append(target_task)


        asset_item = QtWidgets.QTreeWidgetItem([current_name])
        self.version_tree.addTopLevelItem(asset_item)
        
        asset_versions = sorted(self.asset_vars[current_name].keys())


        # asset_tasks = []
        # for version in asset_versions:
        #     for task in self.asset_vars[current_name][version].keys():
        #         print(task)
        #         if task in self.current_tasks and task not in asset_tasks:
        #             # print("############ current_task: {} ############".format(task))
        #             asset_tasks.append(task)


        asset_tasks = []
        for version in asset_versions:
            asset_versions = sorted(self.asset_vars[current_name].keys())

            for version in asset_versions:
                tasks = self.asset_vars[current_name][version].keys()

                for task in tasks:
                    if "assembly" in task:
                        continue
                    
                    if task not in current_tasks:
                        continue

                    if task not in asset_tasks:
                        asset_tasks.append(task)
                        


        for task in asset_tasks:
            target_tasks_version = [
                version for version in asset_versions if task in self.asset_vars[current_name][version]
            ]

            target_tasks_version = sorted(target_tasks_version)

            task_item = QtWidgets.QTreeWidgetItem([task])
            asset_item.addChild(task_item)

            asset_item.setExpanded(True)

            self.task_combo = QtWidgets.QComboBox()
            self.task_combo.addItems(target_tasks_version)


            self.version_tree.setItemWidget(task_item, 1, self.task_combo)

            self.task_combo.currentTextChanged.connect(self.get_task_meta)

        # print(stage.GetLayerStack())

        # for layer in stage.GetLayerStack():
        #     print(layer.identifier)


        # for layer in stage.GetSessionLayer().GetCompositionNodes():
        #     print(layer.layer.identifier)


        # for layer in stage.GetUsedLayers():
        #     print(layer.identifier)



    # current_sel = lambda self: self.main_layout.addLayout(self.top_layout)


    def update_local_layers(self):
        current_sel = self.published_assets_table.currentRow()

        if current_sel < 0:
            print("Please select an asset to update")
            return
        
        asset_name = self.target_name[current_sel]

        stage_path = self.asset_path[current_sel]

        target_rel = os.path.dirname(stage_path)

        if not os.path.exists(stage_path):
            print("Couldn't find the stage at %s" % stage_path)
            return
        
        target_task_versions = {}

        asset_item = self.version_tree.topLevelItem(0)

        if asset_item:
            childs = asset_item.childCount()

            for x in range(childs):
                task_item = asset_item.child(x)
                task_name = task_item.text(0)

                target_combo = self.version_tree.itemWidget(task_item, 1)

                version_sel = target_combo.currentText()
                target_task_versions[task_name] = version_sel

            print(target_task_versions)
        
        stage = Usd.Stage.Open(stage_path)
        root_layer = stage.GetRootLayer()


        out_sublayers = []
        for path in root_layer.subLayerPaths:
            if "anon" in path:
                continue

            target_path = path

            current_task = self.asset_finder.find_current_task(target_dir=path)

            if current_task and current_task in target_task_versions:
                target_version = target_task_versions[current_task]

                changed_path = self.asset_vars[asset_name][target_version][current_task]['path']

                if os.path.isabs(changed_path):
                    relative_path = os.path.relpath(changed_path, target_rel)
                    out_relative = relative_path.replace("\\", "/")

                    out_sublayers.append(out_relative)

        root_layer.subLayerPaths = out_sublayers

        root_layer.Save()

        print("#### Assembly modified ####")

        self.preview_asset()





if __name__ == "__main__":
    print(sys.executable)
    print(sys.argv[0])
    print(sys.meta_path)

    window = Resolver_window()
    window.show()
    app.exec_()

