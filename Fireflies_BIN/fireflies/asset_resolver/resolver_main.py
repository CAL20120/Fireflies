import os
import sys
import re
from datetime import datetime
import logging

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pathlib
import shutil

import subprocess

from colorama import Fore

import ctypes

#wanted to get the screen resolution but used ctypes user32 instead
# from win32api import GetSystemMetrics as gsm


import json

import gazu

from fireflies.context import prod_tracker
CONTEXT = prod_tracker.manage_context()

from fireflies.houdini import abstract_hou_publish

ABS_PUBLISH = abstract_hou_publish.hou_publish
PUBLISH_CHECKS = abstract_hou_publish.Publish_checks()


from PySide2 import (QtCore, QtWidgets, QtGui, 
                     QtMultimedia, QtMultimediaWidgets)


from PySide2.QtGui import QColor, QPalette


#to get the asset vars dict
try:
    from fireflies.fireflies_utils.usd import usd_asset_importer_hou, fireflies_usd_viewer

except:
    pass


try:
    from pxr import Usd, UsdGeom, Vt, Ar, Sdf

except:
    pass



#quick setup for the logging
#TODO: add a complete logging systeme for the pipeline
#just to test the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

tmp_env = os.environ.get('TMP')
error_dir = os.path.join(tmp_env, 'fireflies_resolver_logs')

if not os.path.exists(error_dir):
    os.makedirs(error_dir)

error_file = f"resolver_error.log"

error_output = os.path.join(error_dir, error_file)

file_handler = logging.FileHandler(error_output)
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter('%(message)s - %(asctime)s'))

logger.addHandler(file_handler)


ASSET_FINDER = usd_asset_importer_hou.import_usd_asset()



if __name__ == "__main__":
    resolver_app_id = 'fireflies.asset_resolver.main.1_0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(resolver_app_id)

    # import qdarktheme

    app = QtWidgets.QApplication.instance()

    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    #Style tests

    app.setStyle('Fusion')

    palette = QPalette()
    
    palette.setColor(QPalette.Window, QColor(26, 26, 30))
    palette.setColor(QPalette.Base, QColor(20, 20, 23))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 35))

    palette.setColor(QPalette.Button, QtGui.QColor(35, 35, 40))
    palette.setColor(QPalette.Mid, QColor(42, 42, 48))
    palette.setColor(QPalette.Dark, QColor(15, 15, 18))
    
    palette.setColor(QPalette.WindowText, QColor(208, 208, 216))
    palette.setColor(QPalette.ButtonText, QColor(208, 208, 216))
    palette.setColor(QPalette.Text, QColor(208, 208, 216))

    palette.setColor(QPalette.PlaceholderText, QColor(90, 90, 100))
    palette.setColor(QPalette.Highlight, QColor(120, 30, 30))
    palette.setColor(QPalette.HighlightedText, QColor(230, 220, 220))

    palette.setColor(QPalette.Light, QColor(50, 50, 55))
    palette.setColor(QPalette.Shadow, QColor(10, 10, 12))

    app.setPalette(palette)

    # qdarktheme.setup_theme(
    #     theme='dark', 
    #     corner_shape='rounded',
    #     custom_colors= {
    #         "primary": "#C00000FF"
    #     } 

    # )


relative_subpath = lambda first_stage_path, target_rel: os.path.relpath(first_stage_path, os.path.dirname(target_rel)).replace('\\', '/')


def add_item(row, column, text, table:QtWidgets.QTableWidget) -> QtWidgets:
    item = QtWidgets.QTableWidgetItem(str(text))
    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
    
    table.setItem(row, column, item)



@dataclass
class Resolver_Main_Context:
    prod_name:str = ""
    prod_path:str = ""
    
    is_entity_task:bool = False
    
    kt_current_entity:dict = None
    kt_shot_entities:dict = None


@dataclass
class Shot_Scheme_Context:
    versions_properties:dict = None
    current_task_path:str = None

    kt_entity_sel:dict = None
    current_validate_path:str = None
    kt_entities_hierarchy:dict = None


    seq_elements:tuple[list, list] = ([], [])

@dataclass
class Asset_Scheme_Context:
    current_asset_name:str = None
    current_task_name:str = None




class Resolver_Mode_Methods(ABC):

    @abstractmethod
    def load_entity(self):
        pass


    @abstractmethod
    def get_current_widget(self):
        pass



class Validation_Methods(ABC):
    @abstractmethod
    def create_validate():
        pass






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




class Resolver_init_window(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Resolver_init_window, self).__init__(parent)
        self.setWindowTitle("Resolver - Choose Mode (Shot / Asset)")
        self.setMinimumSize(400, 200)

        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )

        self.select_prod_btn = QtWidgets.QPushButton("Shot")
        self.select_asset_btn = QtWidgets.QPushButton("Asset")

        self.select_prod_btn.setIcon(
            QtGui.QIcon(
                QtGui.QPixmap("C:\\Fireflies\\Fireflies\\softs_logo\\quick_previz.png")
            )
        )
        self.select_prod_btn.setIconSize(QtCore.QSize(100, 100))
        self.select_prod_btn.setCheckable(True)

        self.select_asset_btn.setIcon(
            QtGui.QIcon(
                QtGui.QPixmap("C:\\Fireflies\\Fireflies_BIN\\fireflies\\logos\\asset_creator.png")
            )
        )
        self.select_asset_btn.setIconSize(QtCore.QSize(100, 100))
        self.select_prod_btn.setCheckable(True)

        self.select_prod_btn.clicked.connect(self.update_sel)
        self.select_asset_btn.clicked.connect(self.update_sel)

        self.btn_layout = QtWidgets.QHBoxLayout()
        self.btn_layout.addWidget(self.select_prod_btn)
        self.btn_layout.addWidget(self.select_asset_btn)

        self.select_btn = QtWidgets.QPushButton('Select')
        self.select_btn.clicked.connect(self.apply_sel)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.btn_layout)
        self.main_layout.addWidget(self.select_btn)

        self.out_sel = None


    def update_sel(self):
        self.out_sel = self.sender().text()
        print(self.out_sel)


    def apply_sel(self):
        if self.out_sel is None:
            print("### Please select a mode ###")
            QtWidgets.QMessageBox.warning(self, 'warning', 'Please select a mode')
            return
    
        self.accept()



class Resolver_window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Resolver_window, self).__init__()

        app_icon = QtGui.QIcon("C:\\Fireflies\\Fireflies_BIN\\fireflies\\logos\\assembly_maker.png")
        self.setWindowIcon(app_icon)

        self.setWindowTitle("Fireflies - Resolver")

        user32 = ctypes.windll.user32
        screen_size = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

        self.setMinimumSize(screen_size[0] / 2, screen_size[1] / 2)


        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowMinimizeButtonHint | 
            QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )

        self.current_mode = None

        self.resolver_main_context = Resolver_Main_Context()

        self.create_widgets()
        self.create_layout()

        self.resolver_init_window = Resolver_init_window(self)
        
        if self.resolver_init_window.exec_() == QtWidgets.QDialog.Accepted:
            self.out_type = self.resolver_init_window.out_sel
            print("### Active Mode: {} ###".format(self.out_type))
            self.set_active_mode(self.out_type)

        self.get_prod_data()

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

        # self.get_asset_dict()
        
        self.refresh_prod_combo()

        self.current_prod_path = self._prod_paths[self.prod_combo.currentIndex()]
        self.current_prod_name = self.prod_combo.currentText()            

        self.resolver_main_context.prod_name = self.current_prod_name
        self.resolver_main_context.prod_path = self.current_prod_path


        if hasattr(self, 'current_mode') and self.current_mode is not None:
            try:
                print(self.resolver_main_context)
                self.current_mode.load_entity()

            except ValueError as e:
                logger.error(f"{self.current_prod_name} + {e}")



    def set_active_mode(self, target_mode:str):
        if target_mode == 'Asset':
            self.current_mode = MAIN_Asset_Mode_Scheme(resolver_context=self.resolver_main_context, 
                                                       parent=self)

        elif target_mode == 'Shot':
            self.current_mode = MAIN_Shot_Mode_Scheme(resolver_context=self.resolver_main_context, 
                                                      parent=self)

        target_mode_ui = self.current_mode.get_current_widget()

        self.main_stack.addWidget(target_mode_ui)
        self.main_stack.setCurrentWidget(target_mode_ui)



    def update_context(self):
        target_index = self.prod_combo.currentIndex()

        self.current_prod_path = self._prod_paths[target_index]
        self.current_prod_name = self.prod_combo.currentText()

        self.resolver_main_context.prod_path = self.current_prod_path
        self.resolver_main_context.prod_name = self.current_prod_name



    def create_widgets(self):
        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)

        self.test_btn = QtWidgets.QPushButton("debug")

        self.prod_label = QtWidgets.QLabel('PRODS: ')
        self.prod_combo = QtWidgets.QComboBox()

        # self.update_btn = QtWidgets.QPushButton("Update Entity")


        self.main_stack = QtWidgets.QStackedWidget()

        # self.shot_stack_widget = MAIN_Shot_Mode_Widgets(self)
        # self.asset_stack_widget = MAIN_Asset_Mode_Widgets(self)

        # self.main_stack.addWidget(self.shot_stack_widget)
        # self.main_stack.addWidget(self.asset_stack_widget)


        self.top_menu_bar = QtWidgets.QMenuBar()
        main_menu = self.top_menu_bar.addMenu('Options')
        validate_menu = self.top_menu_bar.addMenu('Validates')
        dev_menu = self.top_menu_bar.addMenu('Dev / Debug')



        self.toggle_asset_mode = QtWidgets.QAction("Switch to Validate", self)
        self.toggle_asset_mode.setCheckable(True)
        main_menu.addAction(self.toggle_asset_mode)

        self.open_task_dir_action = QtWidgets.QAction("Open task directory", self)
        main_menu.addAction(self.open_task_dir_action)

        self.create_validate_btn = QtWidgets.QAction(
            "Create Validate", self
        )
        validate_menu.addAction(self.create_validate_btn)
        
        self.add_validate_task_btn = QtWidgets.QAction("Add task", self)
        validate_menu.addAction(self.add_validate_task_btn)

        self.validate_target_task = QtWidgets.QAction("Validate selected task", self)
        validate_menu.addAction(self.validate_target_task)

        self.debug_asset_finder = QtWidgets.QAction("Get Asset Vars", self)
        dev_menu.addAction(self.debug_asset_finder)

        # info_header = self.asset_info_table.verticalHeader()
        # info_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)


    def create_layout(self):
        self.top_layout = QtWidgets.QVBoxLayout()
        self.top_layout.addWidget(self.top_menu_bar)

        self.prod_layout = QtWidgets.QFormLayout()
        self.prod_layout.addRow('PRODS: ', self.prod_combo)
        self.prod_combo.setFixedSize(100, 30)
        self.prod_combo.setIconSize(QtCore.QSize(50, 50))
        # self.top_layout.addWidget(self.test_btn)
    

        self.btn_layout = QtWidgets.QHBoxLayout()
        # self.btn_layout.addWidget(self.update_btn)


        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.prod_layout)
        self.main_layout.addWidget(self.main_stack)

        self.main_layout.addLayout(self.btn_layout)



    def create_connections(self):
        self.prod_combo.currentIndexChanged.connect(self.update_context)
        self.prod_combo.currentIndexChanged.connect(self.current_mode.load_entity)

        """
        self.test_btn.clicked.connect(self.debug_func)
        
        self.prod_combo.currentIndexChanged.connect(self.get_prod_data)
        self.prod_combo.currentIndexChanged.connect(self.get_task_meta)


        self.version_tree.selectionModel().selectionChanged.connect(self.get_task_meta)

        self.update_btn.clicked.connect(self.update_local_layers)

        self.toggle_asset_mode.triggered.connect(self.check_current_mode)
        """
        self.create_validate_btn.triggered.connect(self.current_mode.create_validate)
        self.add_validate_task_btn.triggered.connect(self.current_mode.add_to_valid_task)
        self.validate_target_task.triggered.connect(self.current_mode.validate_task)

        self.debug_asset_finder.triggered.connect(self.current_mode.debug_func)

        # self.render_task_action.triggered.connect(self.current_mode.submit_task_render)


    def refresh_prod_combo(self):
        for x, asset in enumerate(self._prod_paths):
            self.prod_combo.addItem(os.path.basename(asset))



    def get_useful_data(self, asset_path:str):
        time_map = os.path.getmtime(asset_path)
        modified_time = datetime.fromtimestamp(time_map)

        return str(modified_time)

    

    # def debug_func(self):
    #     self.update_local_layers()


    #not used for the moment as the function "get current task versions" does 
    #the same and better now...






class Create_Validate_Win(QtWidgets.QDialog):
    def __init__(self, asset_vars:dict, parent=None, current_prod:str=None):
        super(Create_Validate_Win, self).__init__(parent)
        self.asset_vars = asset_vars

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
        for version in reversed(self.asset_vars[self.asset_name].keys()):
            
            for task in self.asset_vars[self.asset_name][version].keys():
                if task == target_task:
                    print(version)
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
        changed_path = self.asset_vars[self.asset_name][last_version][target_task]['path']
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

        kt_infos = CONTEXT.get_full_ct(changed_path, asset=True)
        kt_entity = kt_infos['task_entity']


        new_data, _ = CONTEXT.set_to_validate(prod_name=self.current_prod, asset_path=changed_path,
                                              valid_state=True, kt_task_entity=kt_entity)


        self.accept()



class Add_Validate_Task_Win(QtWidgets.QDialog):
    def __init__(self, parent, asset_name:str,
                 to_validate_path:str, prod_name:str, 
                 asset_vars:dict):
        
        super(Add_Validate_Task_Win, self).__init__(parent)

        self.setWindowTitle("Add Task To Validate Asset")
        self.setMinimumSize(400, 600)

        if not asset_name:
            print("No asset selected")


        self.asset_name = asset_name
        self.to_validate_path = to_validate_path
        self.prod_name = prod_name
        self.asset_vars = asset_vars

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


        for version in self.asset_vars[self.asset_name].keys():
            
            for task in self.asset_vars[self.asset_name][version].keys():
            
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
class manage_validate_callbacks():
    def __init__(self, asset_scheme, prod_path:str=None):
        super(manage_validate_callbacks, self).__init__()
        self.prod_path = prod_path
        self.asset_scheme = asset_scheme

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


        to_valid_path, valid_path, assembly_path = self.asset_scheme.get_validate_path(self.asset_name, self.prod_path, get_assembly=True)
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
        kt_entity = kt_infos['task_entity']

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
                                            valid_state=False, task_removed=True,
                                            kt_task_entity=kt_entity)

        if task not in found_tasks:
            print("### TARGET TASK: {} ###".format(target_path))
            current_layers.append(target_path)

        print("### OUT VALIDATED LAYERS: {} ###".format(current_layers))

        root_layer.subLayerPaths = current_layers

        stage.Save()

        new_data, _ = CONTEXT.set_to_validate(prod_name=prod, asset_path=task_path,
                                              valid_state=True, kt_task_entity=kt_entity)

        kt_to_valid_data[task] = "valid"

        print(kt_asset)

        print(kt_to_valid_data)

        new_data = gazu.asset.update_asset_data(kt_asset, kt_asset['data'])

        print(new_data)

        return new_data



class MAIN_Asset_Mode_Scheme(Resolver_Mode_Methods):
    def __init__(self, resolver_context:Resolver_Main_Context, parent=None):
        self.resolver_asset_ui = MAIN_Asset_Mode_Widgets(parent)
        self.resolver_context = resolver_context

        self.scheme_context = Asset_Scheme_Context()

        self.current_task_mode = False
        self.usd_viewer = None
        self.task_preview = None
        self.task_comment = self.resolver_asset_ui.task_comment


        self.resolver_asset_ui.request_mode_change.connect(lambda: self.check_current_mode())
        self.resolver_asset_ui.request_asset_meta.connect(lambda: self.update_meta())

        self.resolver_asset_ui.request_task_meta.connect(lambda: self.get_task_meta())
        self.resolver_asset_ui.request_update_sinal.connect(self.update_local_layers)

        self.published_entity_widget = self.resolver_asset_ui.published_entity_widget

        # self.init_windows()



    def init_windows(self):
        """
        Just for the startup, loads all the additionnal widgets
        """

        preview_path = "C:/Fireflies/Fireflies/softs_logo/resolver/resolver_bg.jpg"
        stage_path = "C:/Fireflies/Common/usd_viewer/usdview_win32/share/usd/tutorials/traversingStage/HelloWorld.usda"

        self.preview_asset(stage_path)

        # self.get_task_meta(preview_path, 'Undefined', stage_path)


    def load_entity(self):
        self.refresh_win()


    def get_current_widget(self):
        return self.resolver_asset_ui
    


    def get_asset_dict(self):
        ASSET_FINDER.prod_path = self.resolver_context.prod_path
        self.asset_name, self.asset_vars = ASSET_FINDER.find_asset(shot_filter=False)

        return self.asset_vars


    def update_meta(self):
        self.manage_asset_tree()


    def check_current_mode(self):
        self.current_task_mode = not self.current_task_mode
        self.refresh_win()
        self.manage_asset_tree()
        self.get_task_meta()



    def refresh_win(self):
        self.get_asset_dict()

        print("Refresh")

        self.published_entity_widget.setRowCount(0)
        # self.asset_info_table.setRowCount(0)

        self.asset_dir = []
        self.target_name = []

        self.asset_path = []


        if self.current_task_mode:
            target_task = "to_validate"
            
        else:
            target_task = "assembly" 


        for name in self.asset_name:
            asset_versions = sorted(self.asset_vars[name].keys())

            for version in reversed(asset_versions):
                tasks = self.asset_vars[name][version].keys()
                
                for task in tasks:

                    if target_task != task:
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
                self.asset_path[self.published_entity_widget.currentRow()]
            )

            print(published_date)

            self.published_entity_widget.insertRow(x)

            current_name = self.target_name[x]
            last_version = sorted(self.asset_vars[current_name].keys())[-1]

            exclude_list = ['to_valite', 'validate', 'assembly']
            
            tasks_list = set()
            for version in self.asset_vars[current_name].values():
                for task in version.keys():
                    if task not in exclude_list:
                        tasks_list.add(task)

            task_count = len(tasks_list)

            asset_widget = self.get_asset_display_widget(current_name, task_count, last_version)

            self.published_entity_widget.setCellWidget(x, 0, asset_widget)

            self.published_entity_widget.setRowHeight(x, 66)

            # add_item(0, 0, published_date, table=self.asset_info_table)


    def get_useful_data(self, asset_path:str):
        time_map = os.path.getmtime(asset_path)
        modified_time = datetime.fromtimestamp(time_map)

        return str(modified_time)



    def get_asset_display_widget(self, asset_name:str, task_count:str,
                           last_version:int) -> QtWidgets.QWidget:
        
        out_widget = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout(out_widget)
        layout.setSpacing(10)

        icon_tex = QtGui.QPixmap("C:/Fireflies/Fireflies/softs_logo/resolver/tasks/model_icon.png")

        icon = QtWidgets.QLabel()
        icon.setFixedSize(24, 24)
        icon.setPixmap(
            icon_tex.scaled(24, 24, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        )
        icon.setAlignment(QtCore.Qt.AlignCenter)

        txt_widget = QtWidgets.QWidget()
        txt_layout = QtWidgets.QVBoxLayout(txt_widget)
        txt_layout.setContentsMargins(0, 0, 0, 0)

        label_name = QtWidgets.QLabel(asset_name)
        # label_name.setStyleSheet(
        #     f"font-weight:500; font-size:12px;"
        # )

        add_info = QtWidgets.QLabel(f"Task Count: {task_count}")
        # add_info.setStyleSheet(
        #     f"font-size:10px;"
        # )

        txt_layout.addWidget(label_name)
        txt_layout.addWidget(add_info)

        layout.addWidget(icon)
        layout.addWidget(txt_widget)
        layout.addStretch()

        return out_widget
    
    

    def refresh_asset_info(self):
        # self.asset_info_table.setRowCount(0)

        print("###########")

        asset_sel = self.published_entity_widget.currentRow()
        print(asset_sel)

        published_date = self.get_useful_data(
            self.asset_path[asset_sel]
        )

        print(published_date)
        self.manage_asset_tree()



    def preview_asset(self, asset_path:str=None):
        if not asset_path:
            if not self.asset_path:
                return
            
            asset_sel = self.published_entity_widget.currentRow()
            if asset_sel < 0:
                return

            asset_path = self.asset_path[asset_sel]

        self.resolver_asset_ui.usd_viewer.load_stage(asset_path)

        sys.stdout.flush()



    def get_task_meta(self):
        version_tree = self.resolver_asset_ui.version_tree

        try: 
            if self.task_preview or self.task_comment:
                self.task_preview.deleteLater()
        
        except: 
            self.task_preview = None


        sel = version_tree.selectedItems()

        if not sel:
            print("You may select a task")
            return

        current_task = sel[0]

        if current_task.parent() == None:
            print("You may select a task")
            return

        task_name = current_task.text(0)

        current_asset_sel = self.published_entity_widget.currentRow()
        if current_asset_sel < 0:
            return

        name = self.target_name[current_asset_sel]

        target_combo = version_tree.itemWidget(current_task, 2)
        
        target_version = target_combo.currentText()

        asset = self.asset_vars[name][target_version][task_name]
        asset_path = asset['path'] if asset.get('type') == "asset" else None


        if not os.path.exists(asset_path):
            print("Stage file does not exists")
            return


        asset_dir = os.path.dirname(asset_path)

        target_dir = f"{asset_dir}/metadata/"

        preview_path = f"{target_dir}/preview/{name}_preview.jpg"
        target_comment = f"{target_dir}/commentary/{name}_comment.txt"

        
        exist_test = [preview_path, target_comment]

        for path in exist_test:
            if not os.path.exists(path):
                print("Couldn't find the related task metadata")
                return


        with open(target_comment, "r") as f:
            comment = f.read()


        texture = QtGui.QPixmap(preview_path)

        self.resolver_asset_ui.task_preview.setPixmap(
            texture.scaled(852, 480, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        )
        
        self.resolver_asset_ui.task_comment.setPlainText(comment)

        self.preview_asset(asset_path)

        self.scheme_context.current_asset_name = name
        self.scheme_context.current_task_name = task_name



    def get_validate_path(self, asset_name:str, prod_path:str=None, get_assembly:bool=False) -> list[str]:
        """
        Return the to_validate, validate, and assembly paths in a list
        """

        target_prod_path = prod_path if prod_path else self.resolver_context.prod_path
        
        
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



    def get_current_layers(self) -> Sdf:
        self.asset_data = []

        target_stage = self.asset_path[self.published_entity_widget.currentRow()]

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
            target_local_var = self.asset_vars[name][task_var][current_task]
            print(target_local_var)
        
            self.asset_data.append(current_task)
            self.asset_data.append(task_var)
            self.current_tasks.append(current_task)



    def validate_task(self):
        return self.call_validate_task()


    def add_to_valid_task(self):
        return self.add_validate_task()


    def debug_func(self):
        pass


    def manage_asset_tree(self):        
        print("#### Refreshing asset tree ####")
        version_tree = self.resolver_asset_ui.version_tree
        task_icons = prod_tracker.ASSET_TASKS_ICONS

        version_tree.clear()

        asset_row = self.published_entity_widget.currentRow()
        
        # if asset_row <= 0:
        #     print("No asset selected")
        #     return
        
        try:
            current_name = self.target_name[asset_row]
            print(self.asset_name)
            print(current_name)

        except:
            return

        stage_path = self.asset_path[asset_row]

        to_valid, valid_path, assembly_path = self.get_validate_path(current_name, self.resolver_context.prod_path, 
                                                                     get_assembly=True)

        validate_callbacks = manage_validate_callbacks(prod_path=self.resolver_context.prod_path, asset_scheme=self)
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
        version_tree.addTopLevelItem(asset_item)

        #had a weird bug were the dict wouldn't update so instead of getting the global var
        #we return the current dict and get it here
        current_asset_dict = self.get_asset_dict()

        print("\n ### debug test asset_vars: {} ### \n".format(self.resolver_context.prod_name))
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

            asset_infos = get_current_tasks_versions(to_valid)

        else: 
            asset_infos = get_current_tasks_versions(assembly_path)


        asset_tasks = []
        for version in asset_versions:
            target_versions = sorted(self.asset_vars[current_name].keys())

            for version in target_versions:
                tasks = self.asset_vars[current_name][version].keys()

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
                    version for version in asset_versions if task in self.asset_vars[current_name][version]
                ]

                out_idx = None
                for layer in asset_infos: 
                    valid_task = layer[1]
                    valid_version = layer[0]

                    if task == valid_task:
                        print(task)
                        out_idx = valid_version

                target_tasks_version = sorted(target_tasks_version)

                task_icon = QtGui.QIcon(task_icons[task])

                task_item = QtWidgets.QTreeWidgetItem([task])
                task_item.setIcon(0, task_icon)

                asset_item.addChild(task_item)

                self.task_combo = QtWidgets.QComboBox()
                self.task_combo.addItems(target_tasks_version)

                version_tree.setItemWidget(task_item, 2, self.task_combo)

                if out_idx:
                    out_idx = target_tasks_version.index(out_idx)
                    print(out_idx)
                    self.task_combo.setCurrentIndex(out_idx)
                                    
                # self.status_pixmap.setPixmap(
                #     status_pix.scaled(24, 24, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                # )


                published_path = self.asset_vars[current_name]['001'][task]['path']

                if not published_path:
                    logger.error("Couldn't find the published_path for: {}".format(task))
                    return
                
                kt_context = CONTEXT.get_full_ct(path=published_path, asset=True)
                kt_status = kt_context['status']

                self.status_label = QtWidgets.QLabel(kt_status)

                version_tree.setItemWidget(task_item, 1, self.status_label)

                self.task_combo.currentTextChanged.connect(lambda: self.get_task_meta())

        else: 
            for layer in asset_infos:
                task = layer[1]
                target_version = [layer[0]]

                task_item = QtWidgets.QTreeWidgetItem([task])
                asset_item.addChild(task_item)

                self.task_combo = QtWidgets.QComboBox()
                self.task_combo.addItems(target_version)

                version_tree.setItemWidget(task_item, 2, self.task_combo)

        asset_item.setExpanded(True)



    def update_local_layers(self):
        if not self.current_task_mode: 
            QtWidgets.QMessageBox.information(self, "Fireflies - Information", "Cannot update an assembly")
            return

        version_tree = self.resolver_asset_ui.version_tree
        published_entity_widget = self.resolver_asset_ui.published_entity_widget

        current_sel = published_entity_widget.currentRow()

        asset_item = version_tree.topLevelItem(0)
        
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

            target_combo = version_tree.itemWidget(task_item, 2)

            version_sel = target_combo.currentText()

            in_vars.append((version_sel, task_name))

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

            version, task = in_vars[target_task_idx]

            print(to_task)
            print(task)

            #if the version in the to_validate and in the resolver is 001
            #we assume that the user just added the task and wants to add 
            #it so we don't check wether it's already in the to_validate stage

            check_same = True if to_version == version and to_version and version != '001' else False
            print(check_same)

            if check_same:
                print(Fore.YELLOW + "### This version of {} is already set to be validated - Ignoring ###".format(task) + Fore.RESET)
                return

            task_path = asset_versions[version][task]['path']

            kt_infos = CONTEXT.get_full_ct(task_path, asset=True)

            kt_task = kt_infos['task_entity']
            

            if os.path.isabs(task_path):
                task_path = os.path.relpath(
                    task_path, os.path.dirname(to_validate_path)
                ).replace('\\', '/')

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

        if not check_same:
            kt_infos, _ = CONTEXT.set_to_validate(prod_name=self.resolver_context.prod_name, asset_path=task_path,
                                                    valid_state=False, kt_task_entity=kt_task)
            print("### Query sent to kitsu ###")


        self.refresh_win()
        

    def create_validate(self) -> QtWidgets.QDialog:
        prod_sel = self.resolver_context.prod_name
        print(prod_sel)

        if not prod_sel:
            print("Please select a production")
            return

        self.create_win = Create_Validate_Win(self.asset_vars, self.resolver_asset_ui, prod_sel)

        # self.create_win.current_prod = prod_sel
        
        if self.create_win.exec_() == QtWidgets.QDialog.Accepted:
            self.refresh_win()


    def add_validate_task(self):
        asset_name = self.scheme_context.current_asset_name

        to_validate_path, validate_path = self.get_validate_path(asset_name)

        self.add_task_win = Add_Validate_Task_Win(self.resolver_asset_ui, asset_name=asset_name,
                                                  to_validate_path=to_validate_path, prod_name=self.resolver_context.prod_name,
                                                  asset_vars=self.asset_vars)

        if self.add_task_win.exec_() == QtWidgets.QDialog.Accepted:
            QtWidgets.QMessageBox.information(self.resolver_asset_ui, "information", "New Task Added !")
            self.refresh_win()



    def call_validate_task(self):
        asset_item_dict = self.get_asset_item()
        version = str(asset_item_dict['version'])
        task_name = asset_item_dict['task']

        print(version)
        print(task_name)

        asset_dict = ASSET_FINDER.find_asset_by_name(asset_item_dict['name'])


        target_task_path = asset_dict[version][task_name]['path']
        print(target_task_path)

        val_callbacks = manage_validate_callbacks(prod_path=self.resolver_context.prod_path, asset_scheme=self)

        val_callbacks.validate_task(target_task_path)
        val_callbacks.validate_task(target_task_path, update_assembly=True)

        QtWidgets.QMessageBox.information(self.resolver_asset_ui, 'information', "Validate and assembly updated")

        # else:
        #     val_callbacks.validate_task(target_task_path, remove_task=True)
        #     QtWidgets.QMessageBox.information(self, 'information', "Task removed from validate")

        self.refresh_win()        



    def get_asset_item(self):
        """
        A method to get the asset item and widgets infos in the version tree main widget
        The user must be selecting an asset in the published asset table and a task in the 
        version tree widgets
        """

        current_name = self.target_name[0]

        if not current_name:
            QtWidgets.QMessageBox.warning(self.resolver_asset_ui, 'warning', 'Please select an asset')
            return
        
        try:
            task_sel = self.resolver_asset_ui.version_tree.selectedItems()[0]
            task_name = task_sel.text(0)
            print(task_name)

        except:
            QtWidgets.QMessageBox.warning(self.resolver_asset_ui, 'warning', 'Please select a task')
            return

        target_check = self.resolver_asset_ui.version_tree.itemWidget(task_sel, 1)

        # keep_task = False
        # if target_check.isChecked():
        #     keep_task = True

        target_combo = self.resolver_asset_ui.version_tree.itemWidget(task_sel, 2)
        target_version = target_combo.currentText()

        asset_item_dict = {
            "name": current_name, 
            "task": task_name,
            "version": target_version, 
            "keep_task": True
        }

        print(asset_item_dict)

        return asset_item_dict




class MAIN_Asset_Mode_Widgets(QtWidgets.QWidget):
    request_update_sinal = QtCore.Signal()
    request_asset_meta = QtCore.Signal()
    request_task_meta = QtCore.Signal()

    request_mode_change = QtCore.Signal()


    def __init__(self, parent=None):
        super(MAIN_Asset_Mode_Widgets, self).__init__(parent)
        self.resolver_main_ui = parent

        self.create_widgets()
        self.create_layout()
        self.create_connections()


    def create_widgets(self):
        self.published_entity_widget = QtWidgets.QTableWidget()
        self.published_entity_widget.setColumnCount(1)
        self.published_entity_widget.setHorizontalHeaderLabels(['Target Asset'])
        
        self.published_entity_widget.verticalHeader().setVisible(False)
        self.published_entity_widget.setShowGrid(False)

        self.published_entity_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.published_entity_widget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        # published_headerview = self.published_entity_widget.horizontalHeader()
        # published_headerview.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        self.version_tree = QtWidgets.QTreeWidget()
        self.version_tree.setColumnCount(3)

        self.version_tree.setHeaderLabels(['Task', 'Kitsu Status', 'Changed Version'])
        self.version_tree.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.version_tree.setIconSize(QtCore.QSize(24, 24))

        self.usd_viewer = fireflies_usd_viewer.Usd_Viewer_hou()

        self.task_comment = QtWidgets.QTextEdit()
        self.task_comment.setReadOnly(True)
        self.task_comment.setPlainText('Undefined')

        self.task_preview = QtWidgets.QLabel()
 
        self.update_btn = QtWidgets.QPushButton("Update Validate")
        self.update_btn.setStyleSheet("font-size: 15px; color: #0b5e00;")


    def create_layout(self):
        boxes_style = """
            QGroupBox {
                font-size: 10px;
                font-weight: 500;
                color: #cfcfcf;
                border: 1px solid #2a2a2e;
                border-radius: 4px; 
                padding: 8px 4px 4px 4px; 
            }

            QGroupBox::title {
                subcontrol-origin: margin; 
                subcontrol-position: top left; 
                left: 1px; 
                top: 1px;
            }
            """


        self.asset_widget = QtWidgets.QGroupBox("ASSETS")
        self.asset_widget.setStyleSheet(boxes_style)

        self.asset_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.asset_splitter.addWidget(self.asset_widget)
        self.asset_splitter.addWidget(self.version_tree)
        self.asset_splitter.addWidget(self.update_btn)

        self.asset_layout = QtWidgets.QHBoxLayout(self.asset_widget)
        self.asset_layout.addWidget(self.published_entity_widget)

        self.media_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self.media_widget = QtWidgets.QGroupBox("METADATA")
        self.media_widget.setStyleSheet(boxes_style)

        self.media_layout = QtWidgets.QHBoxLayout(self.media_widget)
        self.media_layout.addWidget(self.task_comment)
        self.media_layout.addWidget(self.task_preview)

        self.media_splitter.addWidget(self.media_widget)

        self.preview_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.preview_splitter.addWidget(self.usd_viewer)
        self.preview_splitter.addWidget(self.media_splitter)

        self.preview_splitter.setStretchFactor(1, 1)

        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.main_splitter.addWidget(self.asset_splitter)
        self.main_splitter.addWidget(self.preview_splitter)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.main_splitter)


    def create_connections(self):
        self.published_entity_widget.itemSelectionChanged.connect(self.request_asset_meta.emit)
        self.version_tree.itemSelectionChanged.connect(self.request_task_meta.emit)

        self.resolver_main_ui.toggle_asset_mode.triggered.connect(self.request_mode_change.emit)

        self.update_btn.clicked.connect(self.request_update_sinal.emit)
        # self.published_entity_widget.selectionModel().selectionChanged.connect(self.preview_asset)



def get_shot_asset_name(sequence_name, shot_name):
    return f"_{sequence_name}_{shot_name}_SHOT"


class MAIN_Shot_Mode_Scheme(Resolver_Mode_Methods):
    request_update_sinal = QtCore.Signal()
    # request_create_valid = QtCore.Signal()

    def __init__(self, resolver_context:Resolver_Main_Context, parent=None):
        self.resolver_shot_ui = MAIN_Shot_Mode_Widgets(parent)

        self.resolver_context = resolver_context
        self.scheme_context = Shot_Scheme_Context()

        self.validation_process = Shot_Validation(self.scheme_context, self.resolver_context,
                                                  self.resolver_shot_ui)

        self.resolver_shot_ui.request_shot_meta.connect(self.update_metadata)
        self.resolver_shot_ui.request_context_update.connect(self.update_scheme_context)
        # self.resolver_shot_ui.request_video_update.connect(self.load_meta_preview)


        self.load_meta_preview(
            self.resolver_shot_ui.media_player, 
            "Z:\\VFX_LIB\\06_USD_DEV\\resolver_intro.mp4"
        )


    def load_entity(self):
        logger.info('### LOADING NEW ENTITY ###')
        self.shot_dict_to_tree(self.resolver_shot_ui.published_entity_widget)
    

    def get_current_widget(self):
        return self.resolver_shot_ui
    

    def request_update(self):
        pass



    def update_scheme_context(self):
        tree_widget = self.resolver_shot_ui.published_entity_widget

        try:
            current_sel = tree_widget.selectedItems()[0]
        except:
            return


        if current_sel.text(0) not in prod_tracker.SHOT_TASKS:
            print('### Please select a task ###')

        target_combo = tree_widget.itemWidget(current_sel, 1)
        print(f"### PROPERTY: {target_combo.property('kt_data')} ###")

        kt_task_data = target_combo.property('kt_data')
        asset_finder_data = target_combo.property('asset_finder_data')

        self.scheme_context.kt_entity_sel = kt_task_data
        self.scheme_context.versions_properties = asset_finder_data

        target_items:tuple = self.get_tree_seq_elements(self.resolver_shot_ui.published_entity_widget)
        self.scheme_context.seq_elements = target_items



    def get_asset_dict(self):
        ASSET_FINDER.prod_path = self.resolver_context.prod_path
        self.asset_name, self.asset_vars = ASSET_FINDER.find_asset(shot_filter=True)
        # print(self.asset_vars)


    def shot_dict_to_tree(self, tree_widget:QtWidgets.QTreeWidget):
        """
        Converts the sequence / shot dict from the prod_tracker
        to the correct widget for the resolver
        """

        tree_widget.clear()

        self.get_asset_dict()

        self.prod_name = self.resolver_context.prod_name

        target_hierarchy = CONTEXT.get_shots_hierarchy(self.prod_name)

        self.scheme_context.kt_entities_hierarchy = target_hierarchy

        print("### HIERARCHY: {} ###".format(target_hierarchy))

        seq_icon = QtGui.QIcon("C:\\Fireflies\\Fireflies\\softs_logo\\quick_previz.png")
        shot_icon = QtGui.QIcon("C:\\Fireflies\\Fireflies\\softs_logo\\resolver_shot.png")

        for seq in target_hierarchy.keys():
            seq_item = QtWidgets.QTreeWidgetItem([seq])
            seq_item.setIcon(0, seq_icon)
            tree_widget.addTopLevelItem(seq_item)

            # shots = target_hierarchy[seq]

            for shot in target_hierarchy[seq]:
                child = QtWidgets.QTreeWidgetItem([shot])
                child.setIcon(0, shot_icon)

                seq_item.addChild(child)
                child.setExpanded(True)

                for kt_task in target_hierarchy[seq][shot]:
                    task_name = kt_task['task_type_name']

                    if task_name == 'Storyboard':
                        continue

                    task_child = QtWidgets.QTreeWidgetItem([task_name])
                    child.addChild(task_child)

                    icon_path = prod_tracker.SHOT_TASKS_ICONS[task_name]
                    task_icon = QtGui.QIcon(icon_path)
                    
                    task_child.setIcon(0, task_icon)

                    version_combo = QtWidgets.QComboBox()
                    all_versions = []
                    
                    asset_name = f"_{seq}_{shot}_SHOT"

                    asset_versions = self.asset_vars[asset_name]

                    for version, task in asset_versions.items():

                        if task_name in task:
                            all_versions.append(version)
                            version_combo.addItem(version)
                            
                            version_combo.setProperty('asset_finder_data', task)
                            version_combo.setProperty(
                                'kt_data', kt_task
                            )

                    version_combo.setCurrentIndex(len(all_versions) - 1)
                    
                    version_combo.currentIndexChanged.connect(self.update_metadata)

                    tree_widget.setItemWidget(task_child, 1, version_combo)

                    self.validation_process.check_validate_files(seq_names=[seq, shot, task_name])

            seq_item.setExpanded(True)

        self.resolver_context.kt_shot_entities = target_hierarchy


    def get_kt_shot(self):
        try:
            asset_path = self.get_asset_path()

            info_dict = CONTEXT.get_full_ct(path=asset_path, asset=True)
        
        except Exception as e:
            # QtWidgets.QMessageBox.information(
            #     self.resolver_shot_ui, 'Entity not found', "Couldn't find any published work for this task"
            # )
            logger.error(f"Couldn't find entity: {repr(e)}")


        print(info_dict)

        return info_dict


    def update_metadata(self):
        self.get_asset_dict()

        print("Updating metadata")
        info_dict = self.get_kt_shot()
        
        
        self.update_kt_table(info_dict)
        self.import_metadata()
        self.update_version_tree()


    def build_tree_validates(self, layers_info:list[tuple], shot_item, version_tree):
        for info in layers_info:
            version, task, path = info
            task_item = QtWidgets.QTreeWidgetItem([task])

            icon_path = prod_tracker.SHOT_TASKS_ICONS[task]
            task_icon = QtGui.QIcon(icon_path)
            
            task_item.setIcon(0, task_icon)

            shot_item.addChild(task_item)

            version_combo = QtWidgets.QComboBox()
            version_combo.addItem(version)

            version_tree.setItemWidget(task_item, 1, version_combo)

            shot_item.setExpanded(True)



    def update_version_tree(self):
        """
        Updates the version tree for the to_validate and validate versions
        """

        print("### UPDATING VERSION TREE ###")

        version_tree = self.resolver_shot_ui.validates_info_tree
        version_tree.clear()

        seq_items, seq_txt = self.get_tree_seq_elements(self.resolver_shot_ui.published_entity_widget)
        
        if not seq_txt:
            return

        seq_name, shot_name, task_name = seq_txt

        to_valid_path, valid_path = self.validation_process.check_validate_files(seq_names=seq_txt)

        if os.path.exists(to_valid_path):
            layers_info = get_current_tasks_versions(to_valid_path)

            shot_item = QtWidgets.QTreeWidgetItem([f"{shot_name}_TO_VALID"])
            version_tree.addTopLevelItem(shot_item)

            icon_path = prod_tracker.SHOT_TASKS_ICONS["to_validate"]
            shot_icon = QtGui.QIcon(icon_path)
            shot_item.setIcon(0, shot_icon)

            self.build_tree_validates(layers_info, shot_item, version_tree)

        
        if os.path.exists(valid_path):
            layers_info = get_current_tasks_versions(valid_path)

            shot_item = QtWidgets.QTreeWidgetItem([f"{shot_name}_VALID"])
            version_tree.addTopLevelItem(shot_item)

            icon_path = prod_tracker.SHOT_TASKS_ICONS["validate"]
            shot_icon = QtGui.QIcon(icon_path)
            shot_item.setIcon(0, shot_icon)


            self.build_tree_validates(layers_info, shot_item, version_tree)


    def update_kt_table(self, kt_infos:dict):
        kt_info_table = self.resolver_shot_ui.kt_info_table

        self.kt_status = kt_infos['status']
        self.kt_start = kt_infos['start_date']
        self.kt_end = kt_infos['end_date']

        kt_user_list = kt_infos['assigned_users']
        map_users = map(str, kt_user_list)
        self.kt_assigned_user = ', '.join(map_users)


        # except:
        #     QtWidgets.QMessageBox.information(
        #         'Entity not found', "Couldn't find any published work for this task", self.resolver_shot_ui
        #     )

        #     self.kt_status = "Undefined"
        #     self.kt_start = "Undefined"
        #     self.kt_end = "Undefined"

        #     self.kt_assigned_user = "Undefined"


        kt_info_table.setItem(0, 0, QtWidgets.QTableWidgetItem(self.kt_status))
        kt_info_table.setItem(1, 0, QtWidgets.QTableWidgetItem(self.kt_start))
        kt_info_table.setItem(2, 0, QtWidgets.QTableWidgetItem(self.kt_end))
        kt_info_table.setItem(3, 0, QtWidgets.QTableWidgetItem(self.kt_assigned_user))



    def load_meta_preview(self, media_player:QtMultimedia.QMediaPlayer, video_source:str):
        qt_video = QtCore.QUrl.fromLocalFile(video_source)
        qt_content = QtMultimedia.QMediaContent(qt_video)

        media_player.setMedia(qt_content)
        media_player.play()



    def import_metadata(self):
        """
        Imports the comment and the image preview
        """

        asset_path = self.get_asset_path()
        
        if not os.path.exists(asset_path):
            print("Stage file does not exists")
            return

        asset_dir = os.path.dirname(asset_path)

        name = os.path.basename(asset_dir)[:-4]

        target_dir = f"{asset_dir}/metadata/"

        print(target_dir)

        preview_file = os.path.normpath(f"{target_dir}/preview/{name}_preview.jpg")
        target_comment = os.path.normpath(f"{target_dir}/commentary/{name}_comment.txt")

        print("### COMMENT PATH: {} ###".format(target_comment))

        if os.path.exists(target_comment):
            with open(target_comment, 'r') as f:
                out_comment = f.read()

        else: 
            out_comment = 'Undefined'

        if not os.path.exists(preview_file):
            preview_file = "Z:\\VFX_LIB\\06_USD_DEV\\debug_tex.png"


        self.resolver_shot_ui.task_comment.setPlainText(out_comment)

        video_preview_file = f"{target_dir}/video_preview/video_preview.mp4"

        if not os.path.exists(video_preview_file):
            video_preview_file = os.path.splitext(video_preview_file)[0] + '.mkv'

        if os.path.exists(video_preview_file):
            self.load_meta_preview(self.resolver_shot_ui.media_player,
                                        video_preview_file)




    def submit_task_render(self):
        print("ca paaaart")
        pass



    def get_tree_seq_elements(self, tree_widget:QtWidgets.QTreeWidget) -> tuple[list, list]:
        current_task_item = tree_widget.selectedItems()[0]
        current_shot_item = current_task_item.parent()

        current_seq_item = current_shot_item.parent()

        current_task = current_task_item.text(0)
        current_shot = current_shot_item.text(0)
        current_seq = current_seq_item.text(0)

        out_data = (
            [current_seq_item, current_shot_item, current_task_item], 
            [current_seq, current_shot, current_task]
        )

        return out_data



    def get_asset_path(self, target_version:str=None):
        tree_widget = self.resolver_shot_ui.published_entity_widget

        seq_items, seq_txt = self.get_tree_seq_elements(tree_widget)

        current_seq_item, current_shot_item, current_task_item = seq_items
        
        current_seq, current_shot, current_task = seq_txt

        if not target_version:
            target_combo = tree_widget.itemWidget(current_task_item, 1)
            target_version = target_combo.currentText()


        asset_name = get_shot_asset_name(current_seq, current_shot)

        task_dict = self.asset_vars.get(asset_name, {}).get(target_version, {}).get(current_task, {})

        if task_dict.get('type') == 'sequence':
            asset_path = task_dict['frames'][0]['path']

        else: 
            asset_path = task_dict.get('path')

        asset_dir = os.path.dirname(asset_path)

        for file in os.listdir(asset_dir):
            if file == 'master_anim.usd':
                asset_path = os.path.join(asset_dir, file)
                break

        self.scheme_context.current_task_path = asset_path

        return asset_path


    def create_validate(self):
        tree_widget = self.resolver_shot_ui.published_entity_widget
        seq_items, seq_names = self.get_tree_seq_elements(tree_widget)

        self.validation_process.create_validate()

        self.update_metadata()


    def validate_task(self):
        valid_info_tree = self.resolver_shot_ui.validates_info_tree
        
        try:
            current_task = valid_info_tree.selectedItems()[0]

            if current_task not in prod_tracker.SHOT_TASKS:
               print("### Please select a task ###") 
               raise ValueError

        except ValueError:
            QtWidgets.QMessageBox(
                self.resolver_shot_ui, 'Information', 'Please select a task'
            )


        self.validation_process.validate_task(current_task.text(0))

        self.update_metadata()


    def add_to_valid_task(self):
        to_valid_path, _ = self.validation_process.check_validate_files()

        target_task = self.scheme_context.versions_properties

        self.validation_process.add_task_to_validate(validate_stage_path=to_valid_path, is_validate=False)

        self.update_metadata()


    def debug_func(self):
        print('\n' * 10)
        print(self.scheme_context)
        pass



class Shot_Validation(Validation_Methods):

    def __init__(self, context:Shot_Scheme_Context, resolver_context:Resolver_Main_Context,
                 ui:QtWidgets.QDialog=None):

        self.scheme_context = context
        self.resolver_context = resolver_context

        self.ui = ui

    def check_validate_files(self, create_stage:bool=False, seq_names:list=None) -> list[str, str]:
        # local_prod_path = prod_tracker.get_local_prod_path()
        local_prod_path = self.resolver_context.prod_path

        if not seq_names:
            seq_items, seq_names = self.scheme_context.seq_elements
        sequence_name, shot_name, task = seq_names


        shot_asset_name = get_shot_asset_name(sequence_name, shot_name)

        task_dir = os.path.join(local_prod_path, sequence_name, shot_name, task)
        print(task_dir)

        if not os.path.exists(task_dir):
            print(
                f"### Task directory doesn't exists for {sequence_name}-{shot_name}-{task} ###"
            )

        validate_task = 'validate'
        to_validate_task = 'to_validate'

        shot_dir = os.path.dirname(task_dir)

        validate_task_path = os.path.join(shot_dir, validate_task)
        to_validate_task_path = os.path.join(shot_dir, to_validate_task)

        valid_publish_dir = os.path.join(validate_task_path, 'usd_published', shot_asset_name)
        to_valid_publish_dir = os.path.join(to_validate_task_path, 'usd_published', shot_asset_name)
        

        for path in [to_valid_publish_dir, valid_publish_dir]:
            if not os.path.exists(path):
                print("### Creating validate folder ###")
                print(path)
                os.makedirs(path)


        
        valid_version_path = os.path.join(
            valid_publish_dir, f"{shot_asset_name}_001", f"{shot_asset_name}.usd"
        )

        to_valid_version_path = os.path.join(
            to_valid_publish_dir, f"{shot_asset_name}_001", f"{shot_asset_name}.usd"

        )

        for path in [to_valid_version_path, valid_version_path]: 
            target_dir = os.path.dirname(path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)


        if create_stage:
            valid_stage = Usd.Stage.CreateNew(valid_version_path)
            to_valid_stage = Usd.Stage.CreateNew(to_valid_version_path)

        
        return [to_valid_version_path, valid_version_path]


    def get_layer_order_key(self, path):
        CT_PATH = prod_tracker.manage_paths(path, is_asset=True)

        tracker_position = prod_tracker.shot_layers_order

        try:
            index = tracker_position.index(CT_PATH.ct_task)
            return index
        
        except ValueError:
            return 


    def create_validate(self):
        print("Creating validate")
        seq_items, seq_names = self.scheme_context.seq_elements
        seq_name, shot_name, task_name = seq_names

        # if os.path.exists(validate_stage_path):
        #     logger.error('Validate stage already exists for {}'.format(seq_names))
        #     return

        if self.ui:
            valid_task_box = QtWidgets.QMessageBox(self.ui)
            valid_task_box.setText(f"Add {task_name} task as to validate ?")
            
            valid_task_box.setStandardButtons(
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.StandardButton.Cancel
            )
            valid_task_box.setDefaultButton(QtWidgets.QMessageBox.Ok)


            ret = valid_task_box.exec_()

            match ret: 
                case QtWidgets.QMessageBox.Ok:
                    pass

                case QtWidgets.QMessageBox.Cancel: 
                    logger.debug("Create validate process canceled")
                    return


        self.create_validate_callback()



    def check_task_valid_process(self):
        """
        The purpose is to set validation steps for each tasks (ex: render a few frames) \n
        for the light task. TODO
        """
        pass



    def create_validate_callback(self):
        """
        Method used as a callback for the QAction Add_Task
        Used to prepare data to then use it in the add_task_to_validate method
        """

        seq_items, seq_names = self.scheme_context.seq_elements
        seq_name, shot_name, task_name = seq_names


        to_valid_stage_path, validate_stage_path = self.check_validate_files(create_stage=True)
        
        asset_finder_task = self.scheme_context.versions_properties

        
        self.check_task_valid_process()


        out_code = self.add_task_to_validate(validate_stage_path=to_valid_stage_path,
                                            is_validate=False)

        match out_code:
            case -1: 
                QtWidgets.QMessageBox.warning(
                    self.resolver_shot_ui, 'Error', "Error, please see log file for more informations"
                )
                return 
            
            case -2: 
                QtWidgets.QMessageBox.warning(
                    self.resolver_shot_ui, 'Warning', "This version of the taks is already in the validation process"
                )
            


    def add_task_to_validate(self, validate_stage_path:str, is_validate:bool):
        """
        Adds / updates a task to a pipeline validate usd stage 
        
        Args:
            validate_stage_path(str): The targeted validate usd file

            finder_task(dict): The dict given with the ASSET_FINDER class
        """

        validate_stage_path = validate_stage_path.replace('\\', '/')

        kt_entity = self.scheme_context.kt_entity_sel

        stage = Usd.Stage.Open(validate_stage_path)
        
        root_layer = stage.GetRootLayer()
        sublayers = list(root_layer.subLayerPaths)

        kt_current_task = self.scheme_context.kt_entity_sel
        task_name = kt_current_task['task_type_name']

        task_path = self.scheme_context.current_task_path
        task_dir = os.path.dirname(task_path)


        CT_PATH = prod_tracker.manage_paths(task_path, is_asset=True)
        current_version = CT_PATH.ct_version[-3:]


        master_anim_basename = 'master_anim.usd'
        master_anim = master_anim_basename if master_anim_basename in os.listdir(task_dir) else None

        if master_anim:
            task_path = os.path.join(task_dir, master_anim_basename)
            print("### Master anim found: {} ###".format(task_path))


        # layers_info = get_current_tasks_versions(validate_stage_path)

        # for layer in layers_info: 
        #     version, task, path = layer

        #     if task == task_name:
        #         if version == current_version:
        #             print("### This version is already in the validation process ###")            
        #             return


        if os.path.isabs(task_path):
            task_path = os.path.relpath(
                task_path, os.path.dirname(validate_stage_path)
            ).replace('\\', '/')


        out_idx = -1
        for x, path in enumerate(sublayers):
            CT_PATH = prod_tracker.manage_paths(path, is_asset=True)

            if task_name == CT_PATH.ct_task:
                if current_version == CT_PATH.ct_version[-3:]:
                    return ValueError("### This version is already in the validation process ###")
                
                out_idx = x
                break


        if out_idx != -1: 
            sublayers[out_idx] = task_path

        else: 
            sublayers.append(task_path)


        sorted_sublayers = sorted(sublayers, key=self.get_layer_order_key)


        print("### Adding {} to validate stage ###".format(task_path))

        print(sublayers)

        root_layer.subLayerPaths = sorted_sublayers

        stage.Save()

        CONTEXT.set_to_validate(prod_name=self.resolver_context.prod_name, asset_path=task_path,
                                valid_state=is_validate, kt_task_entity=kt_entity)




    def validate_task(self, task_name:str):
        to_valid_path, validate_path = self.check_validate_files()

        layers_info = get_current_tasks_versions(validate_path)
        to_valid_info = get_current_tasks_versions(to_valid_path)

        out_target = None
        for info in layers_info:
            version, task, path = info

            if task_name == task:
                out_target = (version, task, path)


        for info in to_valid_info:
            version, task, path = info

            if task_name == task:
                out_to_valid = (version, task, path)            
                  

        stage = Usd.Stage.Open(validate_path)
        root_layer = stage.GetRootLayer()

        sublayers = list(root_layer.subLayerPaths)

        print(sublayers)

        _, seq_names = self.scheme_context.seq_elements
        seq_name, shot_name, _ = seq_names

        kt_entities = self.scheme_context.kt_entities_hierarchy

        kt_shot = kt_entities[seq_name][shot_name]
        kt_entity = next((x for x in kt_shot if x['task_type_name'] == task_name), None)

        if not kt_entity:
            return
        
        print(kt_entity)

        if out_target:
            if out_target[0] == out_to_valid[0]:
                print("### This version is already in the validation process ###")  
                return

            for index, path in enumerate(sublayers):
                current_task = next((task for task in prod_tracker.SHOT_TASKS if task in path), None) 

                if current_task == out_target[1]:
                    sublayers[index] = out_to_valid[-1]
                    break

        else:
            sublayers.append(out_to_valid[-1])

        sorted_layers = sorted(sublayers, key=self.get_layer_order_key)

        root_layer.subLayerPaths = sorted_layers
        root_layer.Save()


        CONTEXT.set_to_validate(prod_name=self.resolver_context.prod_name, asset_path=out_to_valid[1],
                                valid_state=True, kt_task_entity=kt_entity, version=out_to_valid[0])



class MAIN_Shot_Mode_Widgets(QtWidgets.QWidget):
    request_shot_meta = QtCore.Signal()
    request_shot_asset_meta = QtCore.Signal()

    request_context_update = QtCore.Signal(QtWidgets)

    def __init__(self, parent=None):
        super(MAIN_Shot_Mode_Widgets, self).__init__(parent)

        self.resolver_window = parent

        self.create_widgets()
        self.create_layout()
        self.create_connections()



    def create_widgets(self):
        self.published_entity_widget = QtWidgets.QTreeWidget()
        self.published_entity_widget.setColumnCount(2)
        self.published_entity_widget.setHeaderLabels(['Task', 'Version'])
        self.published_entity_widget.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.published_entity_widget.setIconSize(QtCore.QSize(24, 24))

        self.kt_info_table = QtWidgets.QTableWidget()
        self.kt_info_table.setColumnCount(1)
        self.kt_info_table.setRowCount(4)
        self.kt_info_table.setVerticalHeaderLabels(['Status', 'Start Date', 'Due Date', 'Assigned Artists'])
        self.kt_info_table.horizontalHeader().hide()
        kt_header_view = self.kt_info_table.verticalHeader()
        self.kt_info_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.kt_info_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        for x in range(5):
            self.kt_info_table.setItem(0, x, QtWidgets.QTableWidgetItem('Waiting'))


        self.media_player = QtMultimedia.QMediaPlayer(self)
        self.media_player_widget = QtMultimediaWidgets.QVideoWidget(self)
        self.media_player.setVideoOutput(self.media_player_widget)

        play_btn_icon = QtGui.QIcon("C:\\Fireflies\\Fireflies\\softs_logo\\resolver\\play_btn.png")
        pause_btn_icon = QtGui.QIcon("C:\\Fireflies\\Fireflies\\softs_logo\\resolver\\pause_btn.png")

        self.media_pause_btn = QtWidgets.QPushButton()
        self.media_play_btn = QtWidgets.QPushButton()
        self.media_timeline_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        self.media_play_btn.setIcon(play_btn_icon)
        self.media_play_btn.setIconSize(QtCore.QSize(24, 24))

        self.media_pause_btn.setIcon(pause_btn_icon)
        self.media_pause_btn.setIconSize(QtCore.QSize(24, 24))


        self.task_comment = QtWidgets.QTextEdit()
        self.task_comment.setReadOnly(True)
        self.task_comment.setFontPointSize(15)
        self.task_comment.setPlainText("Undefined")


        self.validates_tab = QtWidgets.QTabWidget()
        self.validates_tab.setMovable(True)

        validates_tab_main = QtWidgets.QWidget()
        self.validates_main_layout = QtWidgets.QVBoxLayout(validates_tab_main)

        self.validates_info_tree = QtWidgets.QTreeWidget()
        self.validates_info_tree.setColumnCount(2)
        self.validates_info_tree.setHeaderLabels(['Task', 'Current Version'])
        self.validates_info_tree.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.validates_info_tree.setIconSize(QtCore.QSize(24, 24))

        self.validates_main_layout.addWidget(self.validates_info_tree)

        # self.validates_main_layout.addWidget(self.update_btn)

        self.validates_tab.addTab(validates_tab_main, 'Manage Validate')
        
        render_menu = self.resolver_window.top_menu_bar.addMenu('Render')

        self.render_task_action = QtWidgets.QAction("Render selected task", self)
        render_menu.addAction(self.render_task_action)

        self.render_delivery_action = QtWidgets.QAction("Render delivery", self)
        render_menu.addAction(self.render_delivery_action)



    def create_layout(self):
        self.info_layout = QtWidgets.QVBoxLayout()
        self.info_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.info_splitter.addWidget(self.published_entity_widget)
        self.info_splitter.addWidget(self.kt_info_table)

        self.info_splitter.setStretchFactor(0, 2)

        self.media_widget = QtWidgets.QGroupBox('METADATA')

        self.media_layout = QtWidgets.QVBoxLayout(self.media_widget)
        self.media_layout.setContentsMargins(0, 0, 0, 0)

        self.media_utils_layout = QtWidgets.QHBoxLayout()
        self.media_utils_layout.addWidget(self.media_pause_btn)
        self.media_utils_layout.addWidget(self.media_play_btn)
        self.media_utils_layout.addWidget(self.media_timeline_slider) 

        self.media_layout.addWidget(self.media_player_widget)
        self.media_layout.addLayout(self.media_utils_layout)
        # self.media_layout.addWidget(self.task_comment)

        self.media_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        # self.media_splitter.addWidget(self.media_player_widget)
        self.media_splitter.addWidget(self.media_widget)
        self.media_splitter.addWidget(self.task_comment)

        self.media_splitter.setStretchFactor(0, 3)

        self.validates_widget = QtWidgets.QGroupBox('VALIDATES')
        self.validates_layout = QtWidgets.QVBoxLayout(self.validates_widget)
        self.validates_layout.addWidget(self.validates_tab)

        self.validates_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.validates_splitter.addWidget(self.validates_widget)


        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.main_splitter.addWidget(self.info_splitter)
        self.main_splitter.addWidget(self.media_splitter)
        self.main_splitter.addWidget(self.validates_splitter)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.main_splitter)


        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setStretchFactor(2, 1)



    def create_connections(self):
        self.media_play_btn.clicked.connect(self.media_player.play)
        self.media_pause_btn.clicked.connect(self.media_player.pause)

        self.media_player.positionChanged.connect(self.media_timeline_slider.setValue)
        self.media_timeline_slider.sliderMoved.connect(self.media_player.setPosition)

        self.media_player.durationChanged.connect(self.update_slider)

        self.published_entity_widget.itemSelectionChanged.connect(self.request_shot_meta.emit)
        self.published_entity_widget.itemSelectionChanged.connect(self.request_context_update.emit)



    def update_slider(self, f_end):
        self.media_timeline_slider.setRange(0, f_end)



def main():
    window = Resolver_window()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()

