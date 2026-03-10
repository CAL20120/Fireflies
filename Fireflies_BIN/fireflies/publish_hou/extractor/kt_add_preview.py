import pyblish.api 
import os

class Kt_Integrate_Preview(pyblish.api.InstancePlugin):
    """Add a video the the related asset on kitsu"""

    order = 3.1
    optional = True
    active = False
    label = "Kitsu - Add Video Preview"

    def process(self, instance):
        pass