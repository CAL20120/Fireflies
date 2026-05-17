import os 
import maya.cmds as cmds 

import pyblish

from fireflies.maya import abstract_maya_publish
PUBLISH = abstract_maya_publish.maya_regular_publish()
USD_PUBLISH = abstract_maya_publish.maya_usd_publish()

scene_path = cmds.file(q=True, sn=True).replace('/', '\\')

class ExtractMayaRig(pyblish.api.InstancePlugin): 

    """ Publish a maya rig """

    order = 2.0

    optional = True
    active = False

    current_task = os.environ.get('FIREFLIES_CURRENT_TASK')
    if current_task == 'rig':
        active=True


    label = "Publish RIG"

    def process(self, instance):
        asset_name = instance.name
        
        PUBLISH.extract_rig(scene_path, asset_name)
