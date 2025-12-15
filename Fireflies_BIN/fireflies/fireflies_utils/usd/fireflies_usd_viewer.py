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

from pxr import Usd, UsdGeom, Sdf, UsdUtils
from pxr.Usdviewq.stageView import StageView


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
        self.view.updateView(resetCam=True)

        data_model = self.view._dataModel.viewSettings

        data_model.renderPurpose = True
        data_model.proxyPurpose = False


        view_settings = self.view._dataModel.viewSettings.freeCamera

        view_settings.overrideNear = 0.001
        view_settings.overrideFar = 10000.0


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
        return
    
    x = Usd_Viewer_hou(stage)


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