import os
import sys
import re
from datetime import datetime

import pathlib
import shutil

import subprocess

from colorama import Fore

import gazu

from fireflies.context import prod_tracker
CONTEXT = prod_tracker.manage_context()

from fireflies.houdini import abstract_hou_publish

ABS_PUBLISH = abstract_hou_publish.hou_publish
PUBLISH_CHECKS = abstract_hou_publish.Publish_checks()


from PySide2 import QtCore, QtWidgets, QtGui

# from qt_material import apply_stylesheet, list_themes
# import qtmodern.styles
# import qtmodern.windows
# import qfluentwidgets

#to get the asset vars dict

try:
    from fireflies.fireflies_utils.usd import usd_asset_importer_hou, fireflies_usd_viewer
except:
    pass


try:
    from pxr import Usd, UsdGeom, Vt, Ar, Sdf
except:
    pass

ASSET_FINDER = usd_asset_importer_hou.import_usd_asset()


if __name__ == "__main__":
    import qdarktheme

    app = QtWidgets.QApplication.instance()

    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    #Style tests

    qdarktheme.setup_theme(
        theme='dark', 
        corner_shape='rounded',
        custom_colors= {
            "primary": "#C00000FF"
        } 

    )


relative_subpath = lambda first_stage_path, target_rel: os.path.relpath(first_stage_path, os.path.dirname(target_rel)).replace('\\', '/')


def add_item(row, column, text, table:QtWidgets.QTableWidget) -> QtWidgets:
    item = QtWidgets.QTableWidgetItem(str(text))
    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
    
    table.setItem(row, column, item)


class Resolver_window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Resolver_window, self).__init__()

        app_icon = QtGui.QIcon("C:\\Fireflies\\Fireflies_BIN\\fireflies\\logos\\assembly_maker.png")
        self.setWindowIcon(app_icon)

        self.setWindowTitle("Fireflies - Asset Resolver")
        self.setMinimumSize(1280, 900)


        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )

        self.current_task_mode = False

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
        global prefs_path 
        prefs_path = open(r"C:\\Fireflies\\Common\\fmk_user_prefs\\user_prefs_dir.txt")
        
        global prod_dir 
        prod_dir = os.path.normpath(prefs_path.read())

        if not prod_dir:
            raise Exception(
                "Prod PATH couldn't not be found, please reference it in the framework."
            )

        self._prod_paths = []

        for path in os.listdir(prod_dir):
            target_exclude = [
                "synology",
                ".ini"
            ]

            if any(substr in path.lower() for substr in target_exclude):
                continue

            current_path = os.path.join(prod_dir, path)
            self._prod_paths.append(current_path)
            # print(path)

        self.get_asset_dict()
        
        self.current_prod_path = self._prod_paths[self.prod_combo.currentIndex()]
        self.current_prod_name = self.prod_combo.currentText()

        # print(asset_vars)

        # print("##########")
        # print(self._prod_paths[1])
        # print("##########")

        self.refresh_win()

    def get_asset_dict(self):
        if self.prod_combo.count() == 0:
            print("### PROD INDEX 0 ###")
            ASSET_FINDER.prod_path = self._prod_paths[0]
        else: 
            ASSET_FINDER.prod_path = self._prod_paths[self.prod_combo.currentIndex()]

        global asset_vars
        self.asset_name, asset_vars = ASSET_FINDER.find_asset()

        return asset_vars


    def create_widgets(self):
        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)

        self.test_btn = QtWidgets.QPushButton("debug")

        self.prod_label = QtWidgets.QLabel('PRODS: ')
        self.prod_combo = QtWidgets.QComboBox()

        self.update_btn = QtWidgets.QPushButton("Update asset")

        self.published_assets_table = QtWidgets.QTableWidget()
        self.published_assets_table.setColumnCount(2)
        self.published_assets_table.setColumnWidth(0, 200)
        self.published_assets_table.setColumnWidth(1, 200)
        self.published_assets_table.setHorizontalHeaderLabels(['Target Asset', ''])
        # self.published_assets_table.setSelectionModel

        published_headerview = self.published_assets_table.horizontalHeader()
        published_headerview.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)


        # self.asset_info_table = QtWidgets.QTableWidget()
        # self.asset_info_table.setColumnCount(1)


        self.version_tree = QtWidgets.QTreeWidget()
        self.version_tree.setColumnCount(3)

        self.version_tree.setHeaderLabels(['Task', 'Active (Validate Only)', 'Changed Version'])
        self.version_tree.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)


        self.top_menu_bar = QtWidgets.QMenuBar()
        main_menu = self.top_menu_bar.addMenu('Options')
        validate_menu = self.top_menu_bar.addMenu('Validates')
        
        self.toggle_asset_mode = QtWidgets.QAction("Switch to Validate", self)
        self.toggle_asset_mode.setCheckable(True)
        main_menu.addAction(self.toggle_asset_mode)

        self.create_validate_btn = QtWidgets.QAction(
            "Create Validate", self
        )
        validate_menu.addAction(self.create_validate_btn)
        
        self.add_validate_task_btn = QtWidgets.QAction("Add task", self)
        validate_menu.addAction(self.add_validate_task_btn)

        self.validate_target_task = QtWidgets.QAction("Validate selected task", self)
        validate_menu.addAction(self.validate_target_task)


        # info_header = self.asset_info_table.verticalHeader()
        # info_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)



    def create_layout(self):
        self.top_layout = QtWidgets.QVBoxLayout()
        self.top_layout.addWidget(self.top_menu_bar)
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


        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
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

        self.create_validate_btn.triggered.connect(self.create_validate)

        self.toggle_asset_mode.triggered.connect(self.check_current_mode)
        self.add_validate_task_btn.triggered.connect(self.add_validate_task)
        self.validate_target_task.triggered.connect(self.call_validate_task)


    def check_current_mode(self):
        self.current_task_mode = not self.current_task_mode
        self.manage_asset_tree()
        self.get_task_meta()


    def refresh_prod_combo(self):        
        for x, asset in enumerate(self._prod_paths):
            self.prod_combo.addItem(os.path.basename(asset))



    def refresh_win(self):
        print("Refresh")

        self.published_assets_table.setRowCount(0)
        # self.asset_info_table.setRowCount(0)

        self.asset_dir = []
        self.target_name = []

        self.asset_path = []


        if self.current_task_mode:
            target_task = "to_validate"
            
        else:
            target_task = "assembly" 


        for name in self.asset_name:
            asset_versions = sorted(asset_vars[name].keys())

            for version in reversed(asset_versions):
                tasks = asset_vars[name][version].keys()
                
                for task in tasks:

                    if target_task != task:
                        continue

                    print(task)
                    if name not in self.target_name:
                        self.target_name.append(name)
                        
                        path = asset_vars[name][version][target_task]['path']
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
            
            add_item(x, 0, self.target_name[x], table=self.published_assets_table)
            self.published_assets_table.setCellWidget(
                x, 1, self.get_preview(
                    asset_path=self.asset_path[x], name=self.target_name[x]
                )
            )

            self.published_assets_table.setRowHeight(x, 120)

            # add_item(0, 0, published_date, table=self.asset_info_table)



    def refresh_asset_info(self):
        # self.asset_info_table.setRowCount(0)

        print("###########")

        asset_sel = self.published_assets_table.currentRow()
        print(asset_sel)

        published_date = self.get_useful_data(
            self.asset_path[asset_sel]
        )

        print(published_date)
        self.manage_asset_tree()



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

        target_combo = self.version_tree.itemWidget(current_task, 2)
        
        target_version = target_combo.currentText()

        asset = asset_vars[name][target_version][task_name]
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


    #not used for the moment as the function "get current task versions" does 
    #the same and better now...
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

            current_task = ASSET_FINDER.find_current_task(target_dir=path)
            if current_task:
                print(current_task)
                print("current task: %s" %current_task + "\n %s" %path)
                

            path_object = pathlib.Path(path)

            task_var = path_object.parts[-2].rsplit('_', 1)[-1]

            print(task_var)

            name = path_object.stem
            target_local_var = asset_vars[name][task_var][current_task]
            print(target_local_var)
        
            self.asset_data.append(current_task)
            self.asset_data.append(task_var)
            self.current_tasks.append(current_task)


    
    def get_validate_path(self, asset_name:str, prod_path:str=None, get_assembly:bool=False) -> list[str]:
        """
        Return the to_validate, validate, and assembly paths in a list
        """

        target_prod_path = prod_path if prod_path else self.current_prod_path
        
        
        to_validate_dir = f"props\\asset_resolver\\to_validate\\"

        publish_dir = f"usd_published\\{asset_name}\\{asset_name}_001"
        usd_publish_dir = os.path.normpath(os.path.join(target_prod_path, to_validate_dir + publish_dir))

        to_validate_path = os.path.join(usd_publish_dir, f"{asset_name}.usd")
        print(to_validate_path)

        validate_dir = f"props\\asset_resolver\\validate\\"
        usd_publish_dir = os.path.normpath(os.path.join(target_prod_path, validate_dir + publish_dir))

        validate_path = os.path.join(usd_publish_dir, f"{asset_name}.usd")
        print(validate_path)

        out_paths = [to_validate_path, validate_path]

        if get_assembly:
            assembly_dir = f"props\\asset_resolver\\assembly\\"
            usd_publish_dir = os.path.normpath(os.path.join(target_prod_path, assembly_dir + publish_dir))

            assembly_path = os.path.join(usd_publish_dir, f"{asset_name}.usd")

            out_paths.append(assembly_path)

        return out_paths



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

        to_valid, valid_path, assembly_path = self.get_validate_path(current_name, self.current_prod_path, 
                                                                     get_assembly=True)

        validate_callbacks = manage_validate_callbacks(prod_path=self.current_prod_path)
        validate_callbacks.check_stages(stage_path)

        current_tasks = []

        if os.path.exists(stage_path):
            stage = Usd.Stage.Open(stage_path)
            root_layer = stage.GetRootLayer()


            for path in root_layer.subLayerPaths:
                target_task = ASSET_FINDER.find_current_task(target_dir=path)

                if target_task and target_task not in current_tasks:
                    current_tasks.append(target_task)

        print("\n ### TASKS IN TO_VALIDATE: {} ### \n".format(current_tasks))


        asset_item = QtWidgets.QTreeWidgetItem([current_name])
        self.version_tree.addTopLevelItem(asset_item)

        #had a weird bug were the dict wouldn't update so instead of getting the global var
        #we return the current dict and get it here
        current_asset_dict = self.get_asset_dict()

        print("\n ### debug test asset_vars: {} ### \n".format(self.current_prod_name))
        asset_versions = sorted(current_asset_dict[current_name].keys())


        """
        asset_tasks = []
        for version in asset_versions:
            for task in asset_vars[current_name][version].keys():
                print(task)
                if task in self.current_tasks and task not in asset_tasks:
                    # print("############ current_task: {} ############".format(task))
                    asset_tasks.append(task)
        """


        target_task_types = ["assembly"]
        if self.current_task_mode:
            target_task_types = ['to_validate']

            asset_infos = get_current_tasks_versions(valid_path)

        else: 
            asset_infos = get_current_tasks_versions(assembly_path)


        asset_tasks = []
        for version in asset_versions:
            target_versions = sorted(asset_vars[current_name].keys())

            for version in target_versions:
                tasks = asset_vars[current_name][version].keys()

                for task in tasks:
                    if any(target in task for target in target_task_types):
                        continue
                    
                    if task not in current_tasks:
                        continue

                    if task not in asset_tasks:
                        asset_tasks.append(task)
                        
        print("### ASSET TASKS: {} ###")

        if self.current_task_mode:
            for task in asset_tasks:
                target_tasks_version = [
                    version for version in asset_versions if task in asset_vars[current_name][version]
                ]

                out_idx = None
                for layer in asset_infos: 
                    valid_task = layer[1]
                    valid_version = layer[0]

                    if task == valid_task:
                        print(task)
                        out_idx = valid_version

                target_tasks_version = sorted(target_tasks_version)

                task_item = QtWidgets.QTreeWidgetItem([task])
                asset_item.addChild(task_item)

                self.task_combo = QtWidgets.QComboBox()
                self.task_combo.addItems(target_tasks_version)

                self.version_tree.setItemWidget(task_item, 2, self.task_combo)

                if out_idx:
                    out_idx = target_tasks_version.index(out_idx)
                    print(out_idx)
                    self.task_combo.setCurrentIndex(out_idx)

                self.active_check = QtWidgets.QCheckBox()
                self.active_check.setCheckState(QtCore.Qt.Checked)
                self.version_tree.setItemWidget(task_item, 1, self.active_check)

                self.task_combo.currentTextChanged.connect(self.get_task_meta)

        else: 
            for layer in asset_infos:
                task = layer[1]
                target_version = [layer[0]]

                task_item = QtWidgets.QTreeWidgetItem([task])
                asset_item.addChild(task_item)

                self.task_combo = QtWidgets.QComboBox()
                self.task_combo.addItems(target_version)

                self.version_tree.setItemWidget(task_item, 2, self.task_combo)

        asset_item.setExpanded(True)



    def update_local_layers(self):
        if not self.current_task_mode: 
            QtWidgets.QMessageBox.information(self, "Fireflies - Information", "Cannot update an assembly")
            return

        current_sel = self.published_assets_table.currentRow()

        asset_item = self.version_tree.topLevelItem(0)
        
        if not asset_item or current_sel:
            print("### Please select an asset to update ###")
            return


        asset_name = self.target_name[current_sel]

        to_validate_path, validate_path = self.get_validate_path(asset_name)

        if not os.path.exists(to_validate_path):
            QtWidgets.QMessageBox.information(self, "Fireflies - Information", "Please first create a validate asset")
            return

        if not os.path.exists(validate_path):
            os.makedirs(os.path.dirname(validate_path))
            
            validate_stage = Usd.Stage.CreateNew(validate_path)
            print(validate_stage)


        to_valid_layers_info = sorted(get_current_tasks_versions(to_validate_path))
        valid_layers_info = sorted(get_current_tasks_versions(validate_path))

        # print(to_valid_layers_info)

        in_vars = []
        childs = asset_item.childCount()

        for x in range(childs):
            task_item = asset_item.child(x)
            task_name = task_item.text(0)

            target_combo = self.version_tree.itemWidget(task_item, 2)

            target_check = self.version_tree.itemWidget(task_item, 1)

            is_active = True if target_check.isChecked() else False

            version_sel = target_combo.currentText()

            in_vars.append((version_sel, task_name, is_active))

        print(in_vars)


        asset_versions = ASSET_FINDER.find_asset_by_name(asset_name)

        kt_to_valid_data = {
            'to_valid_tasks': {
            },
        }

        out_task = []
        out_paths = []
        for x, layer in enumerate(to_valid_layers_info):
            to_version, to_task, _ = layer

            target_task_idx = next((j for j, k in enumerate(in_vars) if to_task in k), None)
            print(target_task_idx)

            if target_task_idx is None:
                print(Fore.YELLOW + "### Task disabled: {} - Skipping ###" + Fore.RESET)
                continue

            version, task, is_active = in_vars[target_task_idx]

            print(to_task)
            print(task)

            #if the version in the to_validate and in the resolver is 001
            #we assume that the user just added the task and wants to add 
            #it so we don't check wether it's already in the to_validate stage

            check_same = True if to_version == version and to_version and version != '001' else False
            print(check_same)

            if check_same:
                print(Fore.YELLOW + "### This version of {} is already set to be validated - Ignoring ###".format(task) + Fore.RESET)
                

            task_path = asset_versions[version][task]['path']

            print(self.current_prod_name)

            if is_active and not check_same:
                kt_infos, _ = CONTEXT.set_to_validate(self.current_prod_name, task_path, valid_state=False)
                print("### Query sent to kitsu ###")


            if os.path.isabs(task_path):
                task_path = os.path.relpath(task_path, os.path.dirname(to_validate_path)).replace('\\', '/')

            out_task.append((version, task, task_path))
            out_paths.append(task_path)

            kt_to_valid_data['to_valid_tasks'].setdefault(task, version)


        print(kt_to_valid_data)
        print(f"OUT TASKS {out_task}")
        print("### OUT PATHS: {} ###".format(out_paths))

        print(kt_infos['current_entity'])

        new_data = gazu.asset.update_asset_data(kt_infos['current_entity'], kt_to_valid_data)
        print(new_data)

        new_paths = set_new_sublayers(out_paths, to_validate_path)
        print(new_paths)

        self.preview_asset()
        


    def create_validate(self) -> QtWidgets.QDialog:
        prod_sel = self.prod_combo.currentText()
        print(prod_sel)

        if not prod_sel:
            print("Please select a production")
            return

        self.create_win = Create_Validate_Win(self, prod_sel)

        # self.create_win.current_prod = prod_sel
        
        if self.create_win.exec_() == QtWidgets.QDialog.Accepted:
            self.get_prod_data()


    def add_validate_task(self):
        current_sel = self.published_assets_table.selectedItems()[0]
        asset_name = current_sel.text()

        to_validate_path, validate_path = self.get_validate_path(asset_name)

        self.add_task_win = Add_Validate_Task_Win(
            self, asset_name=asset_name, to_validate_path=to_validate_path, 
            prod_name=self.current_prod_name
        )

        if self.add_task_win.exec_() == QtWidgets.QDialog.Accepted:
            QtWidgets.QMessageBox.information(self, "information", "New Task Added !")
            self.get_prod_data()


    def call_validate_task(self):
        asset_item_dict = self.get_asset_item()
        version = str(asset_item_dict['version'])
        task_name = asset_item_dict['task']

        keep_task = asset_item_dict['keep_task']

        print(version)
        print(task_name)

        asset_dict = ASSET_FINDER.find_asset_by_name(asset_item_dict['name'])


        target_task_path = asset_dict[version][task_name]['path']
        print(target_task_path)

        val_callbacks = manage_validate_callbacks(self.current_prod_path)

        if keep_task:
            val_callbacks.validate_task(target_task_path)
            val_callbacks.validate_task(target_task_path, update_assembly=True)

            QtWidgets.QMessageBox.information(self, 'information', "Validate and assembly updated")

        else:
            val_callbacks.validate_task(target_task_path, remove_task=True)
            QtWidgets.QMessageBox.information(self, 'information', "Task removed from validate")


        self.get_prod_data()
        


    def get_asset_item(self):
        """
        A method to get the asset item and widgets infos in the version tree main widget
        The user must be selecting an asset in the published asset table and a task in the 
        version tree widgets
        """

        current_name = self.target_name[0]

        if not current_name:
            QtWidgets.QMessageBox.warning(self, 'warning', 'Please select an asset')
            return
        
        try:
            task_sel = self.version_tree.selectedItems()[0]        
            task_name = task_sel.text(0)
            print(task_name)

        except:
            QtWidgets.QMessageBox.warning(self, 'warning', 'Please select a task')
            return

        target_check = self.version_tree.itemWidget(task_sel, 1)

        keep_task = False
        if target_check.isChecked():
            keep_task = True

        target_combo = self.version_tree.itemWidget(task_sel, 2)
        target_version = target_combo.currentText()

        asset_item_dict = {
            "name": current_name, 
            "task": task_name,
            "version": target_version, 
            "keep_task": keep_task
        }

        print(asset_item_dict)

        return asset_item_dict



class Create_Validate_Win(QtWidgets.QDialog):
    def __init__(self, parent=None, current_prod:str=None):
        super(Create_Validate_Win, self).__init__(parent)

        self.setWindowTitle("Create Validate")

        self.setMinimumSize(500, 100)

        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )

        self.current_prod = current_prod

        print(self.current_prod)

        self._prod_path = pathlib.Path(f"{prod_dir}\\{self.current_prod}".replace('/', '\\'))
        

        self.create_widgets()
        self.create_layout()
        self.create_connections()


    def create_widgets(self):
        self.create_btn = QtWidgets.QPushButton("Create")
        self.select_asset_btn = QtWidgets.QPushButton("Select Existing Asset")

        self.asset_name_txt = QtWidgets.QLineEdit()
        self.asset_name_txt.setReadOnly(True)
        
        # self.debug_btn = QtWidgets.QPushButton("Debug")


    def create_layout(self):
        self.info_layout = QtWidgets.QFormLayout()
        self.info_layout.addRow("Asset Name:", self.asset_name_txt)

        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout.addWidget(self.create_btn)
        self.bottom_layout.addWidget(self.select_asset_btn)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.info_layout)
        self.main_layout.addLayout(self.bottom_layout)



    def create_connections(self):
        self.select_asset_btn.clicked.connect(self.open_asset_importer)
        self.create_btn.clicked.connect(self.create_validate)


    def open_asset_importer(self):
        importer_window = usd_asset_importer_hou.importer_window(
            parent=self, import_classic=False, prod_path=self._prod_path
        )
        
        if importer_window.exec_() == QtWidgets.QDialog.Accepted:
            self.asset_name = importer_window.out_name
            print("### Target Asset {} ###".format(self.asset_name))
        
            self.asset_name_txt.setText(self.asset_name)


    def create_validate(self, asset_name:str=None, target_task:list=None) -> Usd.Stage:
        if not asset_name:
            asset_name = self.asset_name_txt.text()

        # if not asset_name:
        #     print("### Please select an asset before trying to create a validate ###")

        # validate_dir = asset_name + 'validate'
        # to_validate_dir = asset_name + 'to_validate'
        # print(validate_dir)

        validate_dir = rf"props\asset_resolver\validate\usd_published\{asset_name}"

        to_validate_dir = f"props\\asset_resolver\\to_validate\\usd_published\\{asset_name}\\{asset_name}_001"
        usd_publish_dir = os.path.normpath(os.path.join(self._prod_path, to_validate_dir))

        export_path = os.path.join(usd_publish_dir, f"{asset_name}.usd")

        if os.path.exists(export_path):
            print("### This to validate version already exists, you can still add tasks to it ###")
            return


        if not os.path.exists(usd_publish_dir):
            os.makedirs(usd_publish_dir)


        # export_dir, export_path = ABS_PUBLISH.get_last_version(asset_name, usd_publish_dir)

        print(export_path)

        if not os.path.exists(usd_publish_dir):
            os.makedirs(usd_publish_dir, exist_ok=True)


        if not target_task:
            target_task = ['model']

        if len(target_task) < 2 :
            target_task = target_task[0]

        last_version = None
        for version in reversed(asset_vars[self.asset_name].keys()):
            
            for task in asset_vars[self.asset_name][version].keys():
                if task == target_task:
                    last_version = version
                    print(last_version)
                    break

        if not last_version:
            print("Couldn't find the model task last version -- Exiting")
            return

        # print(asset_vars[self.asset_name][last_version]['model']['path'])

        if not os.path.exists(export_path):
            stage = Usd.Stage.CreateNew(export_path)
        
        stage = Usd.Stage.Open(export_path)
        root_layer = stage.GetRootLayer()

        out_sublayers = []
        changed_path = asset_vars[self.asset_name][last_version][target_task]['path']
        changed_dir = os.path.dirname(changed_path)

        if os.path.isabs(changed_path):
            relative_path = os.path.relpath(changed_path, usd_publish_dir)
            out_relative = relative_path.replace("\\", "/")

            out_sublayers.append(out_relative)
            print("### relative path generated: {} ###".format(out_relative))


        root_layer.subLayerPaths = out_sublayers
        print(out_sublayers)

        root_layer.Save()

        #to get the asset preview in the assembly resolver
        #FIXME: minor change to the path 
        # shutil.copytree(f"{changed_dir}\\metadata", f"{export_path}\\metadata")

        # CONTEXT.set_to_validate(self.current_prod, changed_path, valid_state=False)

        self.accept()



class Add_Validate_Task_Win(QtWidgets.QDialog):
    def __init__(self, parent=None, asset_name:str=None, 
                to_validate_path:str=None, prod_name:str=None):
        super(Add_Validate_Task_Win, self).__init__(parent)

        self.setWindowTitle("Add Task To Validate Asset")
        self.setMinimumSize(400, 600)

        if not asset_name:
            print("No asset selected")

        self.asset_name = asset_name
        self.to_validate_path = to_validate_path
        self.prod_name = prod_name

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.manage_tree()


    def create_widgets(self):
        self.asset_name_txt = QtWidgets.QLineEdit()
        self.asset_name_txt.setReadOnly(True)

        self.asset_name_txt.setText(self.asset_name)

        self.task_table = QtWidgets.QTableWidget()
        self.task_table.setColumnCount(1)
        self.task_table.setHorizontalHeaderLabels(['Task Name'])

        header_view = self.task_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        self.add_task_btn = QtWidgets.QPushButton('Add Task')


    def create_layout(self):
        self.top_layout = QtWidgets.QFormLayout()
        self.top_layout.addRow("Asset Name:", self.asset_name_txt)
        self.top_layout.addWidget(self.task_table)
        

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.add_task_btn)
    

    def create_connections(self):
        self.add_task_btn.clicked.connect(self.add_tasks)


    def manage_tree(self):
        target_tasks = []

        layers_info = get_current_tasks_versions(self.to_validate_path)

        exclude_list = ['assembly', 'validate', 'anim', 'comp']

        for layer in layers_info:
            current_task = layer[1]
            exclude_list.append(current_task)


        print("### TASK EXCLUDE LIST: {} ###".format(exclude_list))


        for version in asset_vars[self.asset_name].keys():
            
            for task in asset_vars[self.asset_name][version].keys():
            
                if task not in target_tasks:
                    if not any(target in task for target in exclude_list):
                        target_tasks.append(task)


        print(target_tasks)

        for x, task in enumerate(target_tasks):
            self.task_table.insertRow(x)
            add_item(x, 0, task, self.task_table)


    def add_tasks(self):
        out_tasks = []
        for sel_task in self.task_table.selectedItems():
            print(sel_task.text())
            out_tasks.append(sel_task.text())

        #asset_vars is a global var so we can't use it here
        asset_dict = ASSET_FINDER.find_asset_by_name(self.asset_name)
        print(asset_dict)

        stage = Usd.Stage.Open(self.to_validate_path)
        root_layer = stage.GetRootLayer()

        current_sublayers = root_layer.subLayerPaths
        print(current_sublayers)

        mat_check = False
        for task in out_tasks:
            print("### TARGET TASK: {} ###".format(task))

            target_path = asset_dict['001'][task]['path']
            print(target_path)

            if os.path.isabs(target_path):
                target_path = relative_subpath(target_path, self.to_validate_path)
            
            current_sublayers.append(target_path)

            if task == "lookdev":
                mat_check = True

            # CONTEXT.set_to_validate(self.prod_name, target_path, valid_state=False)

        stage.Save()

        # if mat_check:
        #     PUBLISH_CHECKS.resolve_relative_paths(self.to_validate_path)


        self.accept()



#we are scanning the current usd sublayers to find
#the used version in a validate or an assembly
def get_current_tasks_versions(stage_path:str) -> list[tuple]:
    stage = Usd.Stage.Open(stage_path)
    root_layer = stage.GetRootLayer()
    print(root_layer)

    current_layers = root_layer.subLayerPaths
    
    layers_info = []
    for layer in current_layers: 
        CT_PATH = prod_tracker.manage_paths(layer, is_asset=True)
        version = CT_PATH.ct_version[-3:]
        task = CT_PATH.ct_task

        layers_info.append((version, task, layer))

    print(layers_info)

    return layers_info



#with this function we only keep the paths passed as in_paths
def set_new_sublayers(in_paths:list | str, out_stage_path:str) -> Usd.Stage:
    """
    Args: 
        in_paths: A list of the paths (layers) that will replace the older paths in the 
                given usd file
        
        out_stage_path: the usd stage that will recieve the new paths (in_paths) as sublayers

    Returns: 
        A list of the paths that have been writen in the usd stage (relative paths)
    """

    stage = Usd.Stage.Open(out_stage_path)
    root_layer = stage.GetRootLayer()

    target_rel = os.path.dirname(out_stage_path)

    out_sublayers = []
    for path in in_paths:
        print(path)

        if os.path.isabs(path):
            relative_path = os.path.relpath(path, target_rel)
            path = relative_path.replace("\\", "/")

        out_sublayers.append(path)
        print("### Path added to the stage: {} ###".format(path))

    root_layer.subLayerPaths = out_sublayers

    root_layer.Save()

    print("#### Asset modified ####")

    return out_sublayers



#subclass for the checks and callbacks within the resolver 
#and in other dcc
class manage_validate_callbacks(Resolver_window):
    def __init__(self, prod_path:str=None):
        super(manage_validate_callbacks, self).__init__()
        self.prod_path = prod_path

    def check_stages(self, asset_path:str) -> list[str]:
        """
        Checks the validate and assembly directories and usd stages

        Returns:
            file_check: The boolean returned by os exists
        """
        
        CT_PATH = prod_tracker.manage_paths(asset_path, is_asset=True)

        self.asset_name = CT_PATH.ct_name
        self.task_version = CT_PATH.ct_version[-3:]

        if self.prod_path is None:
            print("### No production path given ###")
            return


        to_valid_path, valid_path, assembly_path = self.get_validate_path(self.asset_name, self.prod_path, get_assembly=True)
        check_list = [valid_path, assembly_path]

        for target_path in check_list:
            target_dir = os.path.dirname(target_path)
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                print("### Path: {} ###".format(target_path))

            if not os.path.exists(target_path):
                stage = Usd.Stage.CreateNew(target_path)

        check_list.insert(0, to_valid_path)

        return check_list


    def validate_task(self, task_path:str, remove_task:bool=False, update_assembly:bool=False) -> dict:
        """
        Validate the task on kitsu and replace it in the sublayerPaths of the 
        validate usd stage for this asset

        Args:
            task_path:  The asset task usd path that will be validated,
                        in the version folder so that everything is handled 
                        by the context class

            remove_task: If set to True, the given path / task will be removed 
                         from the validate stage (and not from the assembly)

            update_assembly: Will change the assembly file instead of the validate

            
        Returns:
            out_dict: The new task dict
        """
        
        to_valid_path, valid_path, assembly_path = self.check_stages(task_path)

        to_valid_layers = get_current_tasks_versions(to_valid_path)

        #we want to get the path in the to_validate stage just to be safe
        #so that we're sure we keep the good path

        CT_PATH = prod_tracker.manage_paths(path=task_path, is_asset=True)

        task = CT_PATH.ct_task
        prod = CT_PATH.ct_prod
        version = CT_PATH.ct_version[-3:]


        kt_infos = CONTEXT.get_full_ct(task_path, asset=True)

        kt_asset = kt_infos['current_entity']

        kt_asset_data = kt_asset['data']
        kt_to_valid_data = kt_asset_data['to_valid_tasks']


        task_data = kt_to_valid_data[task]

        # if not task_data == version and task_data != 'valid':
        #     QtWidgets.QMessageBox.warning(self, 'warning', "Wrong version detected")
        #     return


        for layer in to_valid_layers:
            layer_path = layer[2]
            layer_dir = os.path.dirname(layer_path)

            current_task = ASSET_FINDER.find_current_task(layer_dir)

            if current_task == task:
                target_path = layer_path
                break
        
        if not target_path:
            print("### Couldn't find the targeted task in the to validate given path ###")
            return
        

        stage_path = valid_path if not update_assembly else assembly_path

        stage = Usd.Stage.Open(stage_path)
        root_layer = stage.GetRootLayer()


        current_layers = list(root_layer.subLayerPaths)
        print("### BEGIN LAYERS: {} ###".format(current_layers))

        found_tasks = []
        for x, layer in enumerate(current_layers):
            layer = layer.strip('@')

            layer_dir = os.path.dirname(layer)
            current_task = ASSET_FINDER.find_current_task(layer_dir)
            
            if current_task:
                found_tasks.append(current_task)

            if current_task == task:
                if not remove_task:
                    current_layers[x] = target_path
                    print("### TARGET TASK: {} ###".format(target_path))
                    break

                else:
                    current_layers.pop(x)
                    CONTEXT.set_to_validate(prod_name=prod, asset_path=task_path,
                                            valid_state=False, task_removed=True)

        if task not in found_tasks:
            print("### TARGET TASK: {} ###".format(target_path))
            current_layers.append(target_path)

        print("### OUT VALIDATED LAYERS: {} ###".format(current_layers))

        root_layer.subLayerPaths = current_layers

        stage.Save()

        new_data, _ = CONTEXT.set_to_validate(prod_name=prod, asset_path=task_path, valid_state=True)

        kt_to_valid_data[task] = "valid"

        print(kt_asset)

        print(kt_to_valid_data)

        new_data = gazu.asset.update_asset_data(kt_asset, kt_asset['data'])

        print(new_data)

        return new_data




def main():
    window = Resolver_window()
    window.show()
    app.exec_()



if __name__ == "__main__":
    main()