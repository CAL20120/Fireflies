echo Setting up fireflies requirements

echo installing maya
"C:\Fireflies\Fireflies_BIN\python_bin\python_310\python.exe" "C:\Fireflies\Fireflies_BIN\scripts_py_installs\maya\install_maya_fireflies.py"

echo installing publish requirements 
"C:\Fireflies\Common\Maya_vars\Maya2024\Maya2024\bin\mayapy.exe" -m pip install git+https://github.com/pyblish/pyblish-base.git
"C:\Fireflies\Common\Maya_vars\Maya2024\Maya2024\bin\mayapy.exe" -m pip install git+https://github.com/pyblish/pyblish-maya.git
"C:\Fireflies\Common\Maya_vars\Maya2024\Maya2024\bin\mayapy.exe" -m pip install git+https://github.com/pyblish/pyblish-rpc.git
"C:\Fireflies\Common\Maya_vars\Maya2024\Maya2024\bin\mayapy.exe" -m pip install git+https://github.com/pyblish/pyblish-lite.git
