import maya.cmds as cmds 
import maya.mel as mel 

def create_fireflies_menu():
    if cmds.menu("Fireflies", exists=True):
        cmds.deleteUI("Fireflies")

    parent_win = mel.eval("$tmpVar=$gMainWindow")

    fireflies_menu = cmds.menu("Fireflies", label="Fireflies Utils", parent=parent_win)
    cmds.menuItem(label="Test", parent=fireflies_menu)

if __name__ == "__main__":
    create_fireflies_menu()