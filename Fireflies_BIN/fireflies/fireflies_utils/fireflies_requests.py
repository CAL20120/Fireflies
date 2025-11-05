from synology_api.filestation import FileStation
from synology_api.exceptions import FileStationError

from fireflies.houdini import hou_utils

import datetime
import time

import os
import sys

class nas_requests():
    def __init__(self):
        # self.local_path = build_local_path()
        self.username = None
        self.password = None
        
        self.username, self.password =self.read_login_prefs()

        print("logged as {}".format(self.username))
        
        self.fs = FileStation(
            'chrisnasmacro.synology.me',
            '3485',
            self.username,
            self.password,
            secure=True, 
            dsm_version=7.1,
            debug=True,
        )

        # self.fs_info = self.fs.get_info()
        # self.files = self.fs.get_list_share()

        self.hou_utils = hou_utils.hou_usd()

    def read_login_prefs(self):
        with open("C:\\Fireflies\\Common\\fmk_user_prefs\\login_prefs.txt", "r") as f:
            result = f.readlines()
        
        username = result[0].strip()
        password = result[1].strip()

        return username, password
        


    def find_assets(self):
        result_assets = []
        assets_path = []
        result_layout = []
        result_lights = []
        lights_path = []

        target_path = "/VFX_LIB/06_USD_DEV/test01"
        files_asset = self.fs.get_file_list(folder_path=target_path, pattern="usd")

        for file in files_asset['data']['files']:
            path = file['path']

            asset_name = path.rsplit("/", 1)[-1].split(".", 1)[0]
            result_assets.append(asset_name)
            assets_path.append(path)
        
        print(result_assets)
        print(len(result_assets))

        target_path = "/VFX_LIB/04_LIGHTING/HDRI"
        files_lights = self.fs.get_file_list(folder_path=target_path)

        for file in files_lights['data']['files']:
            path = file['path']
            asset_name = path.rsplit("/", 1)[-1].split(".", 1)[0]
            
            result_lights.append(asset_name)
            lights_path.append(path)

        return result_assets, result_layout, result_lights, assets_path, lights_path


    def check_local_instance(self, prod_path, asset_name):
        prod_path = prod_path.replace("\\", "/")

        asset_type = None

        if "ASSET" in asset_name:
            asset_type = "ASSET"
        
        elif "LAYOUT" in asset_name:
            asset_type = "LAYOUT"
        
        elif "LIGHT" in asset_name:
            asset_type = "LIGHT"


        lib_path = f"{prod_path}/_lib_sync/{asset_type}"
        prod_asset_path = f"{lib_path}/{asset_name}"
        print(prod_asset_path)


        if os.path.exists(prod_asset_path):
            print("local instance found")
            return True, asset_type, prod_asset_path
       
        else: 
            print("No local instance for this asset")
        
        return False, asset_type, prod_asset_path


    def download_asset(self, nas_path, asset_name, prod_path):
        validate, asset_type, asset_path = self.check_local_instance(prod_path=prod_path, asset_name=asset_name)

        lib_local_path = f"{prod_path}/_lib_sync/{asset_type}"

        if not os.path.exists(lib_local_path):
            os.makedirs(lib_local_path)

        if validate == False:
            self.fs.get_file(path=nas_path, dest_path=lib_local_path, mode='download')
        
        if validate == True:
            if asset_type == "ASSET":
                self.hou_utils.import_prod_usd_asset(asset_path=asset_path)
            
            if asset_type == "LIGHT":
                asset_name = asset_name.rsplit('.', 1)[0]
                self.hou_utils.import_light(asset_path=asset_path, asset_name=asset_name)



if __name__ == "__main__":
    x = nas_requests()
    x.check_local_instance(prod_path="R:/Christopher_LUCAS/PRODS/test_dev", asset_name="test_ASSET.usd")
