from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui


import sys 
import os

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
        self.explorer_button.setIcon(QtGui.QIcon("hicon:/SVGIcons.index?BUTTONS_chooser_folder.svg"))

        self.import_btn = QtWidgets.QPushButton("Import textures")
        self.close_button = QtWidgets.QPushButton("Close")
        self.debug = QtWidgets.QPushButton("debug")

    
    def create_layout(self):
        self.explorer_layout = QtWidgets.QHBoxLayout()
        # self.explorer_layout.addWidget(self.file_path_edit)
        self.explorer_layout.addWidget(self.files_sel)
        self.explorer_layout.addWidget(self.explorer_button)

        self.radio_layout = QtWidgets.QVBoxLayout()
        self.radio_layout.addWidget(self.rman_opt)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.import_btn)
        self.button_layout.addWidget(self.close_button)
        self.button_layout.addWidget(self.debug)

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

    def link_textures(self, tex_name:str, tex_path:str, input_value:str):
        output_collect = hou.node(f"{self.pxr_node.path()}/output_collect")
        print(self.pxr_surface.path())
        output_collect.setInput(0, self.pxr_surface)

        tex_node = self.pxr_node.createNode('pxrtexture', tex_name)
        tex_node.parm('filename').set(tex_path)

        tex_outputs = tex_node.outputNames()
        tex_target_output = tex_outputs.index('resultRGB')

        if not "OPACITY" in tex_path:
            target_input = self.layer_inputs.index(input_value)
            self.pxr_layer.setInput(target_input, tex_node, tex_target_output)

        else:
            target_input = self.surface_inputs.index(input_value)
            self.pxr_surface.setInput(target_input, tex_node, tex_target_output)


        if any(name in tex_path for name in ['ROUGHNESS', 'NORMAL', 'Metalness']):
            if tex_node:
                tex_node.parm("filename_colorspace").set('data')

        if any(name in tex_path for name in ['COLOR', 'OPACITY', 'SSS']):
            if tex_node:
                tex_node.parm("filename_colorspace").set('srgb_texture')



    def create_hou_tree(self, current_items:list):
        
        # print(current_items)
        for tex in current_items:

            if "COLOR" in tex:
                self.link_textures(tex_name="color", tex_path=tex, input_value="diffuseColor")

            
            if "Metalness" in tex:
                self.link_textures(tex_name='metalness', tex_path=tex, input_value="specularFaceColor")


            if "ROUGHNESS" in tex:
                self.link_textures(tex_name="roughness", tex_path=tex, input_value="diffuseRoughness")

            if "SSS" in tex:
                self.link_textures(tex_name="sss", tex_path=tex, input_value="subsurfaceColor")
                self.pxr_layer.parm('enableSubsurface').set(1)

            if "OPACITY" in tex:
                self.link_textures(tex_name="opacity", tex_path=tex, input_value="presence")


            #the normal map requires extra nodes to work, so we create the ndoes manually
            if "NORMAL" in tex:
                bump_layer = self.pxr_node.createNode('pxrbumpmixer', 'bump_mixer')
                
                bump_layer_outputs = bump_layer.outputNames()
                target_output = bump_layer_outputs.index('resultN')
                target_input = self.layer_inputs.index('bumpNormal')

                self.pxr_layer.setInput(target_input, bump_layer, target_output)
                
                tex_node = self.pxr_node.createNode('pxrtexture', 'normal')
                tex_node.parm('filename').set(tex)
                tex_node.parm("filename_colorspace").set('data')


                tex_outputs = tex_node.outputNames()
                tex_target_output = tex_outputs.index('resultRGB')

                bump_layer_inputs = bump_layer.inputNames()
                target_input = bump_layer_inputs.index('surfaceGradient1')

                bump_layer.setInput(target_input, tex_node, tex_target_output)
                




if __name__ == "__main__":
    x = texture_linker_window()
    x.show()