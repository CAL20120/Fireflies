import os
import sys

import webbrowser

import nuke
import nukescripts

toolbar = nuke.menu('Nodes')

fireflies_menu = toolbar.addMenu('Fireflies', icon="C:/Fireflies/Fireflies_BIN/fireflies/logos/assembly_maker.png")

ctx_menu = fireflies_menu.addMenu('Context')
tools_menu = fireflies_menu.addMenu('Tools')

ctx_menu.addCommand('Set Context', 'launch_context()', icon="C:/Fireflies/Fireflies_BIN/fireflies/logos/set_context.png")

def launch_context():
    from fireflies.context import context_window
    global x
    x = context_window.context_window()
    x.show()