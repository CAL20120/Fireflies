import pyblish.api 
import os

from fireflies.context import prod_tracker

class SB_Integrate_Task(pyblish.api.InstancePlugin):
    """Add a task to all the dependencies layerStacks"""

    order = 3.0
    label = "Shot Builder - Integrate Task"

    def process(self, instance):
        shot_builder = prod_tracker.Shot_Builder()

        stage_path = instance.data.get('stage_local_path')
        print("### {} ###".format(stage_path))

        shot_builder.build_dependencies_stack(stage_path)