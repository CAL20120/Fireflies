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

class Usd_Viewer_hou(QtWidgets.QDialog):
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

    def create_layout(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.view)
        self.setLayout(self.main_layout)

    def find_usd_target(self):
        pass

# x.view.updateView(resetCam=True, forceComputeBBox=True)
# x.show()


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

def test():
    parser = argparse.ArgumentParser()
    parser.add_argument('-asset_path')
    args = parser.parse_args()

    launch_app(args.asset_path)
    
test()