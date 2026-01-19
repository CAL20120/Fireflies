import os 
import sys 

from datetime import date
from functools import partial

from PySide2 import QtCore, QtWidgets, QtGui

import hou
from fireflies.houdini import hou_utils


# print(sys.argv)
# app = QtWidgets.QApplication(sys.argv)

class snapshots_window(QtWidgets.QDialog):
    def __init__(self):
        self.utils = hou_utils.hou_usd()

        parent = None
        try:
            parent = hou.qt.mainWindow()
        
        except:
            pass

        super(snapshots_window, self).__init__(parent)

        self.setWindowTitle("Fireflies Snapshots")
        self.setMinimumSize(800, 550)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.checks()
        self.load_history()



    def checks(self):
        self.scene_path = hou.hipFile.path()
        scene_dir = os.path.dirname(self.scene_path)

        self.images_dir = os.path.join(scene_dir, "fireflies_snapshots")

        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)

        
    
    def check_version(self) -> str:
        version_id = 1
        version_check = True

        while version_check:
            output_path = os.path.join(
                self.images_dir, f"preview_{version_id:03}.jpg"
            ).replace(os.sep, '/')

            current_version = output_path
            exists = os.path.exists(output_path)
            if not exists:
                self.utils.create_playblast(output_path)
                break
            version_id += 1

        return output_path, current_version


    def write_snapshot(self):
        output_path, current_version = self.check_version()

        print("Snapshot saved")

        self.load_snapshot(output_path)


    def load_snapshot(self, target_file:str) -> QtWidgets.QLabel:
        try:
            if self.view:
                self.view.deleteLater()
        except:
            pass
        target_file = os.path.normpath(target_file)

        print(target_file)

        self.scene = QtWidgets.QGraphicsScene()
        test = QtGui.QPixmap(target_file)
        # self.scene.addText("coucou")
        self.scene.addPixmap(test)

        self.view = QtWidgets.QGraphicsView(self.scene)

        self.view.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

        def zoom_func(event):
            scale = 1.25 if event.angleDelta().y() > 0 else 0.8
            self.view.scale(scale, scale)

        self.view.wheelEvent = zoom_func

        self.preview_layout.addWidget(self.view)
        self.load_history()



    def load_history(self):
        for x in reversed(range(self.history_layout.count())):
            self.history_layout.itemAt(x).widget().deleteLater()

        for image in os.listdir(self.images_dir):
            # print(image)
            image_path = os.path.join(self.images_dir, image)

            self.history_btn = QtWidgets.QPushButton()
            pixmap = QtGui.QIcon(image_path)
            self.history_btn.setIcon(pixmap)
            self.history_btn.setIconSize(QtCore.QSize(100, 50))

            self.history_layout.addWidget(self.history_btn)
            
            self.history_btn.clicked.connect(
                partial(self.load_snapshot, target_file=image_path)
            )



    def debug(self):
        path = "C:/Fireflies/Fireflies_BIN/fireflies/logos/asset_importer.png"
        self.load_snapshot(path)


    def create_widgets(self):
        self.history_widget = QtWidgets.QWidget()
        self.history_scroll = QtWidgets.QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFixedHeight(100)

        self.snap_btn = QtWidgets.QPushButton("Take Snapshot")
        # self.debug_btn = QtWidgets.QPushButton("Debug")
        # self.clear_btn = QtWidgets.QPushButton("Clear")

    def create_layout(self):
        self.preview_layout = QtWidgets.QHBoxLayout()

        self.history_layout = QtWidgets.QHBoxLayout(self.history_widget)
        self.history_scroll.setWidget(self.history_widget)

        self.btn_layout = QtWidgets.QHBoxLayout()
        self.btn_layout.addWidget(self.snap_btn)
        # self.btn_layout.addWidget(self.clear_btn)
        # self.btn_layout.addWidget(self.debug_btn)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.preview_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.history_scroll)
        self.main_layout.addLayout(self.btn_layout)


    def create_connections(self):
        self.snap_btn.clicked.connect(self.write_snapshot)
        # self.debug_btn.clicked.connect(self.load_history)
        # self.clear_btn.clicked.connect(self.clear_images)



if __name__ == "__main__":
    x = snapshots_window()
    x.show()
