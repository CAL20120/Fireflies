try: 
    import hou
except:
    pass

import os
import sys
import subprocess

import argparse

print(sys.executable)
print(sys.path)

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

from pxr import Usd, UsdGeom, Sdf, UsdUtils, UsdLux
from pxr.Usdviewq.stageView import StageView
from pxr.UsdAppUtils.complexityArgs import RefinementComplexities

app = QtWidgets.QApplication.instance()

if app is None:
    app = QtWidgets.QApplication(sys.argv)

class Usd_Viewer_hou(QtWidgets.QWidget):
    def __init__(self, stage=None, asset_path=None):

        super(Usd_Viewer_hou, self).__init__()
        self.setWindowTitle("Usd Viewer Fireflies")
        self.setMinimumSize(256, 256)
        
        self.model = StageView.DefaultDataModel()
        self.view = StageView(dataModel=self.model)

        self.create_layout()

        if stage:
            self.set_stage(stage)


    def set_stage(self, stage):
        self.model.stage = stage
        self.view.updateView(resetCam=True, forceComputeBBox=True)

        f_start = stage.GetStartTimeCode()
        self.model.currentFrame = Usd.TimeCode(f_start)

        data_model = self.view._dataModel.viewSettings
        data_model.rendererPlugin = "HdStormRendererPlugin"

        data_model.ambientOcclusion = True
        data_model.enableShadows = True

        data_model.colorCorrectionMode = 'sRGB'

        data_model.complexity = RefinementComplexities.VERY_HIGH

        data_model.renderPurpose = True
        data_model.proxyPurpose = False


        view_settings = self.view._dataModel.viewSettings.freeCamera

        view_settings.overrideNear = 0.1
        view_settings.overrideFar = 1000.0


        #adding a simple hdri from nas lib
        hdri_path = r"Z:\\VFX_LIB\\04_LIGHTING\\HDRI\\brown_photostudio_06_4k_LIGHT.exr"
        try:
            target_layer = stage.GetSessionLayer()
            with Usd.EditContext(stage, target_layer):
                hdri_prim = UsdLux.DomeLight.Define(stage, '/hdri')

                if os.path.exists(hdri_path):
                    hdri_prim.CreateTextureFileAttr(hdri_path)
                    hdri_prim.CreateTextureFormatAttr(UsdLux.Tokens.latlong)

        except:
            print("Couldn't reach NAS")
            pass



    def create_layout(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.view)
        self.setLayout(self.main_layout)


# x.view.updateView(resetCam=True, forceComputeBBox=True)
# x.show()

    def load_stage(self, asset_path):
        if os.path.exists(asset_path):
            with Usd.StageCacheContext(UsdUtils.StageCache.Get()):
                stage = Usd.Stage.Open(asset_path)
            
            self.set_stage(stage)


def launch_app(asset_path):
    if os.path.exists(asset_path):
        with Usd.StageCacheContext(UsdUtils.StageCache.Get()):
            stage = Usd.Stage.Open(asset_path)

    else:
        print("path does not exist")
    x = Usd_Viewer_hou(stage)

    if not os.path.exists(asset_path):
        print("Invalid path")
        return


    window = Usd_Viewer_hou(stage=stage, asset_path=asset_path)
    window.show()
    window.view.updateView(resetCam=True, forceComputeBBox=True)

    app.exec_()

# script_path = "C:\\Fireflies\\Fireflies_BIN\\fireflies\\fireflies_utils\\usd\\fireflies_usd_viewer.py"
# asset_path = "R:\\Christopher_LUCAS\\PRODS\\test_dev\\001\\01\\model\\usd_published\\test_ASSET.usd"
# subprocess.Popen([script_path, asset_path])

# launch_app(asset_path="R:\\Christopher_LUCAS\\PRODS\\test_dev\\001\\01\\model\\usd_published\\test_ASSET.usd")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-asset_path')
    args = parser.parse_args()

    launch_app(args.asset_path)


if __name__ == "__main__": 
    main()