import os 
import subprocess

maya_installer = os.path.normpath(r"C:\Fireflies\Fireflies_BIN\scripts_py_installs\maya\Maya_2025_installer_fireflies.exe")
print(maya_installer)

install_path = os.path.normpath(r"C:\Fireflies\Common\Maya_vars")
print(install_path)

subprocess.run([
    maya_installer,
    # f"--install_path={install_path}",
])