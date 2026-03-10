import pyblish.api 
import os

class Extractor_surprise(pyblish.api.InstancePlugin):
    """little surprise for you"""

    order = 3.0
    optional = True
    active = False
    label = "Surprise"

    def process(self, instance):
        path = 'Z:\\VFX_LIB\\06_USD_DEV\\fireworks.mp4'

        if not os.path.exists(path):
            return
        
        os.startfile(path)