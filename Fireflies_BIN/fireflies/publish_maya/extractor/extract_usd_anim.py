import pyblish.api
import os

from fireflies.maya import abstract_maya_publish
PUBLISHER = abstract_maya_publish.maya_usd_publish()

import maya.cmds as cmds 

class Usd_Extractor_Anim(pyblish.api.InstancePlugin):
    """Publish usd animation from maya"""

    order = 2.1
    optional=True
    active=False

    current_task = os.environ.get('FIREFLIES_CURRENT_TASK')
    if current_task == 'anim': 
        active = True

    label="Extract Usd Animation"
    


    def process(self, instance):
        context = instance.context
        
        current_namespace = instance.data.get('maya_namespace')
        asset_name = instance.data.get('asset_name')

        target_namespace = current_namespace.split(asset_name)[0].rstrip(':')

        if context.data.get('is_shot'):
            shot_name = context.data.get('shot_publish_name')

            print("### CURRENT NAMESPACE: {} ###".format(target_namespace))
            print("### CURRENT SHOT: {} ###".format(shot_name))

            try:
                cmds.select(current_namespace)
                PUBLISHER.extract_usd_animation(asset_name=shot_name, namespace=target_namespace)


            except pyblish.api.ExtractionError as e:
                print("### Error while trying to export the animation: {} ###".format(e))


        else: 
            raise pyblish.api.ExtractionError( 
                "### Cannot publish an animation outside of a shot context ###"
            )