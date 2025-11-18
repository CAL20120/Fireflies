from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

import sys 
import os

import subprocess
import glob
import re

import random

from fireflies.houdini import hou_utils

import hou

class texture_linker_window(QtWidgets.QDialog):
    def __init__(self, parent=hou.qt.mainWindow()):
        super(texture_linker_window, self).__init__(parent)

        self.file_filters = "All textures (*.exr *.tif *.jpeg *.png *.raw);; All Files (*.*)"

        self.setWindowTitle("Texture linker")
        self.setMinimumSize(300, 100)

        self.create_widgets()
        self.create_layout()
        self.create_connections()
    
    
    def create_widgets(self):
        # self.file_path_edit = QtWidgets.QLineEdit()
        self.files_sel = QtWidgets.QListWidget()
        
        self.rman_opt = QtWidgets.QRadioButton("PrxLayer")
        self.rman_opt.setChecked(True)
    
        self.explorer_button = QtWidgets.QPushButton()
        self.explorer_button.setIcon(hou.ui.createQtIcon("BUTTONS_chooser_folder"))

        self.import_btn = QtWidgets.QPushButton("Import textures")
        self.close_button = QtWidgets.QPushButton("Close")
        # self.debug = QtWidgets.QPushButton("debug")

    
    def create_layout(self):
        self.explorer_layout = QtWidgets.QHBoxLayout()
        # self.explorer_layout.addWidget(self.file_path_edit)
        self.explorer_layout.addWidget(self.files_sel)

        self.explorer_layout.addWidget(self.explorer_button)
        self.explorer_button.setToolTip("Explore files")

        self.radio_layout = QtWidgets.QVBoxLayout()
        self.radio_layout.addWidget(self.rman_opt)
        # self.radio_layout.addWidget(udim_check)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.import_btn)
        self.button_layout.addWidget(self.close_button)
        # self.button_layout.addWidget(self.debug)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.explorer_layout)
        self.main_layout.addLayout(self.radio_layout)
        self.main_layout.addLayout(self.button_layout)

    
    def create_connections(self):
        self.explorer_button.clicked.connect(self.open_file_dialog)

        self.import_btn.clicked.connect(self.link_tex)
        self.close_button.clicked.connect(self.close)

        # self.debug.clicked.connect(self.create_hou_tree)
        pass


    def open_file_dialog(self):
        self.files_sel.clear()

        import_dialog = QtWidgets.QFileDialog(self)
        import_dialog.setWindowTitle("Select textures")
        import_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        import_dialog.setNameFilter(self.file_filters)

        if import_dialog.exec_():
            sel = import_dialog.selectedFiles()
            self.files_sel.addItems(sel)
            pass

    def link_tex(self):
        current_items = [self.files_sel.item(i).text() for i in range(self.files_sel.count())]

        linker = create_hou_matlib().create_hou_tree(current_items=current_items)



class create_hou_matlib():
    def __init__(self):
        self.curr_context = hou_utils.hou_usd().get_current_context()

        mat_lib_name = 'linker_import_{}'.format(random.randint(111, 999))
        mat_lib = self.curr_context.createNode('materiallibrary', mat_lib_name)
        
        mat_path = mat_lib.path()
        mat_node = hou.node(mat_path)

        self.pxr_node = mat_node.createNode('pxrmaterialbuilder', 'test')
        pxr_shader = hou.node(self.pxr_node.path())

        self.pxr_surface = pxr_shader.createNode('pxrsurface', 'shader')

        surface_inputs = self.pxr_surface.inputNames()

        self.pxr_layer = self.pxr_node.createNode('pxrlayer', 'layer01')
        input_mat_surface = surface_inputs.index('inputMaterial')
        self.pxr_surface.setInput(input_mat_surface, self.pxr_layer)

        self.layer_inputs = self.pxr_layer.inputNames()
        self.surface_inputs = self.pxr_surface.inputNames()


    def check_udim_presence(self, texture_path:str, tex_name:str):
        udim_check = False

        dir_path = os.path.dirname(texture_path)        
        target_pattern = f"{tex_name}.[1-9][0-9][0-9][0-9].exr"
        udim_file_pattern = os.path.join(dir_path, target_pattern)

        tex_udim_files = []
        udim_index = []
        pattern_search = glob.glob(udim_file_pattern, recursive=True)

        for file in pattern_search:
            udim_num = file.split('.')[-2]
            print(udim_num)
            udim_index.append(udim_num)

            tex_udim_files.append(file)

            if len(tex_udim_files) >= 1:
                udim_check = True

        return udim_check, udim_index



    def link_textures(self, tex_name:str, texture_path:str, input_value:str):

        udim_check, udim_index = self.check_udim_presence(texture_path=texture_path, tex_name=tex_name)

        if not os.path.exists(texture_path):
            print("Cannot find file")
            return



        if udim_check == False:
            print('using single file')
            texture_path = rman_generate_tx().make_tx(input_file=texture_path)
        

        else:
            print('using udim files')

            base_path = rman_generate_tx().make_udim_tx(input_file=texture_path)

            print(type(base_path))

            if udim_index:
                texture_path = re.sub(udim_index[0], "<UDIM>", base_path)

                    

        output_collect = hou.node(f"{self.pxr_node.path()}/output_collect")
        print(self.pxr_surface.path())
        output_collect.setInput(0, self.pxr_surface)

        tex_node = self.pxr_node.createNode('pxrtexture', tex_name)


        tex_node.parm('filename').set(texture_path)


        tex_outputs = tex_node.outputNames()
        tex_target_output = tex_outputs.index('resultRGB')


        if not "OPACITY" in texture_path:
            target_input = self.layer_inputs.index(input_value)
            self.pxr_layer.setInput(target_input, tex_node, tex_target_output)

        else:
            target_input = self.surface_inputs.index(input_value)
            self.pxr_surface.setInput(target_input, tex_node, tex_target_output)


        if any(name in texture_path for name in ['ROUGHNESS', 'NORMAL', 'Metalness']):
            if tex_node:
                tex_node.parm("filename_colorspace").set('data')

        if any(name in texture_path for name in ['COLOR', 'OPACITY', 'SSS']):
            if tex_node:
                tex_node.parm("filename_colorspace").set('srgb_texture')



    def create_hou_tree(self, current_items:list) -> hou:
        
        # print(current_items)
        for tex in current_items:

            if "COLOR" in tex:
                if not hasattr(self, 'color_node'):
                    self.link_textures(tex_name="color", texture_path=tex, input_value="diffuseColor")
                    setattr(self, 'color_node', tex)            

            if "Metalness" in tex:
                if not hasattr(self, 'metal_node'):
                    self.link_textures(tex_name='metalness', texture_path=tex, input_value="specularFaceColor")
                    setattr(self, 'metal_node', tex)            


            if "ROUGHNESS" in tex:
                if not hasattr(self, 'rough_node'):
                    self.link_textures(tex_name="Roughness", texture_path=tex, input_value="diffuseRoughness")
                    setattr(self, 'rough_node', tex)            


            if "SSS_GAIN" in tex:
                if not hasattr(self, 'sss_node'):
                    self.link_textures(tex_name="sss_gain", texture_path=tex, input_value="subsurfaceGain")
                    self.pxr_layer.parm('enableSubsurface').set(1)
                    setattr(self, 'sss_node')            


            if "SPECULAR" in tex:
                if not hasattr(self, 'spec_node'):
                    self.link_textures(tex_name="specular", texture_path=tex, input_value="specularRoughness")
                    setattr(self, 'spec_node')

            if "OPACITY" in tex:
                if not hasattr(self, 'presence_node'):
                    self.link_textures(tex_name="opacity", texture_path=tex, input_value="presence")
                    setattr(self, 'presence_node', tex)            


            #the normal map requires extra nodes to work, so we create the ndoes manually
            if "NORMAL" in tex:
                if not os.path.exists(tex):
                    return

                if not hasattr(self, 'normal_node'):
                    udim_check, udim_index = self.check_udim_presence(texture_path=tex, tex_name="normal")


                    bump_layer = self.pxr_node.createNode('pxrbumpmixer', 'bump_mixer')
                    
                    bump_layer_outputs = bump_layer.outputNames()
                    target_output = bump_layer_outputs.index('resultN')
                    target_input = self.layer_inputs.index('bumpNormal')

                    self.pxr_layer.setInput(target_input, bump_layer, target_output)
                    
                    tex_node = self.pxr_node.createNode('pxrtexture', 'normal')

                    if not udim_check:    
                        tex_node.parm('filename').set(tex)
                    else:
                        texture_path = tex
                        base_path = rman_generate_tx().make_udim_tx(input_file=texture_path)

                        texture_path = re.sub(udim_index[0], "<UDIM>", base_path)

                        tex_val_input = texture_path

                        tex_node.parm('filename').set(tex_val_input)
                    
                    
                    tex_node.parm("filename_colorspace").set('data')


                    tex_outputs = tex_node.outputNames()
                    tex_target_output = tex_outputs.index('resultRGB')

                    bump_layer_inputs = bump_layer.inputNames()
                    target_input = bump_layer_inputs.index('surfaceGradient1')

                    bump_layer.setInput(target_input, tex_node, tex_target_output)

                    setattr(self, 'normal_node', tex)            
                    
                if "MSK" in tex:
                    pass


class rman_generate_tx():
    def __init__(self):
        self.tx_make = "C:\\Program Files\\Pixar\\RenderManProServer-26.3\\bin\\txmake.exe"


    def make_tx(self, input_file:str):

        file_dir = os.path.dirname(input_file.replace("\\", "\\"))
        # path_tex = "{}.tex".format(file_dir)
        path_tex = f"{input_file.rsplit('.', 1)[0]}.tex"

        # if os.path.exists(path_tex):
        #     return

        subprocess.Popen(
            [
                self.tx_make, 
                input_file,
                path_tex
            ],
            shell=True, stdout=subprocess.PIPE
        )

        print("tx file generated at {}".format(path_tex))

        return path_tex
    
    def make_udim_tx(self, input_file:str):

        print("### CREATING UDIM TEX ###")
        # file_dir = os.path.dirname(input_file.replace("\\", "/"))

        # file_dir = os.path.dirname()

        dir_path = os.path.dirname(input_file)

        tex_name = input_file.rsplit('.', 2)[0]

        target_pattern = f"{tex_name}.[1-9][0-9][0-9][0-9].exr"

        udim_file_pattern = os.path.join(dir_path, target_pattern)


        tex_udim_files = []
        pattern_search = glob.glob(udim_file_pattern, recursive=True)

        print("### {}".format(input_file))

        for file in pattern_search:
            print("### {}".format(file.replace('\\', '/')))

            if not file:
                continue


            tex_udim_files.append(file.replace('\\', '/'))
        

        if not tex_udim_files:
            raise RuntimeError("No udim files detected")
            return
        
        sorted(tex_udim_files)
        
        tex_udim_output = []
        for index, tex in enumerate(tex_udim_files):
            tex_name = tex.rsplit(".", 1)[0]

            tex_udim_output.append(f"{tex_name}.tex")

            subprocess.Popen(
                [
                    self.tx_make,
                    tex,
                    tex_udim_output[index]
                ],
                shell=True, stdout=subprocess.PIPE
            )

            print(tex_udim_output[index])


        print(len(tex_udim_files))

        return tex_udim_output[0]


if __name__ == "__main__":
    x = texture_linker_window()
    x.show()

