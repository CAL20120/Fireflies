import pyblish.api 
import maya.cmds as cmds 


class validate(pyblish.api.Validator):
    """test"""
    label = "test"
    hosts=["maya"]

    def process(self, context):
        scene_name = cmds.file(query=True, sceneName=True, shortName=True)