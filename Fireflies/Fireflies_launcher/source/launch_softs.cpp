#include <iostream>
#include <cstdlib> // usefull to interact with the os and launch softs
#include <filesystem>

namespace fs = std::filesystem;

#include "launch_softs.h"

#ifdef WIN32
#include <windows.h>
#endif


int check_local_file(const char* input_path) {
    if (!fs::exists(input_path)) {
        std::cout << "Targeted software executable not found" << std::endl;

        return 1;
    }
    
    return 0;
}


void launch_softs::main::maya() {
    const char* exe = "C:/Fireflies/Common/Maya_vars/Maya2024/Maya2024/bin/maya.exe"; 

    check_local_file(exe);

    SetEnvironmentVariable(
        "PYTHONPATH", "C:\\Fireflies\\Common\\Maya_vars\\Maya2024\\Maya2024\\Python\\Lib\\site-packages;C:\\Fireflies\\Fireflies_BIN\\"
    );
    SetEnvironmentVariable("MAYA_APP_DIR", "C:/Fireflies/Fireflies_BIN/Autodesk/env");
    SetEnvironmentVariable("MAYA_SCRIPT_PATH", "C:/Fireflies/Fireflies_BIN/Autodesk/env/scripts");
    SetEnvironmentVariable("MAYA_SHELF_PATH", "C:\\Fireflies\\Fireflies_BIN\\Autodesk\\env\\shelfs");
    // SetEnvironmentVariable("PYBLISH_QML_PYTHON_EXECUTABLE", "C:\\Fireflies\\Fireflies_BIN\\python_bin\\python_37\\python.exe");

    ShellExecute(NULL, "open", exe, NULL, NULL, SW_SHOW);
}



int launch_softs::main::houdini() {
    std::cout << "Houdini launched";
    #ifdef __linux__
    system("/opt/hfs20.5.445/bin/houdini-bin");
    #endif

    #ifdef WIN32
    //env vars
    // const wchar_t* houdini_205_path = L"C:\\Fireflies\\Common\\Houdini_vars\\houdini_205445\\Houdini20.5.445\\bin\\houdini.exe";
    // _putenv("HOUDINI_USER_PREF_DIR=C:/Fireflies/Fireflies_BIN/Sidefx/env");
    // ShellExecute(NULL, "open", "C:\\Fireflies\\Common\\Houdini_vars\\houdini_205447\\Houdini20.5.487\\bin\\houdini.exe", NULL, NULL, SW_SHOW);
    // SetEnvironmentVariable("HOUDINI_USER_PREF_DIR", "C:/Fireflies/Fireflies_BIN/Sidefx/env");
    SetEnvironmentVariable("PYTHONPATH", "C:\\Fireflies\\Common\\Houdini_vars\\houdini_205445\\Houdini20.5.445\\python310\\lib\\site-packages;C:\\Fireflies\\Fireflies_BIN\\");
    ShellExecute(NULL, "open", "C:/Fireflies/Fireflies_BIN/Sidefx/env/launch_houdini_205_rm27.bat", NULL, NULL, SW_SHOW);
    

    // STARTUPINFO si;
    // PROCESS_INFORMATION pi;
    // ZeroMemory(&si, sizeof(si));
    // si.cb = sizeof(si);
    // ZeroMemory(&pi, sizeof(pi));

    // const wchar_t env[] = L"HOUDINI_USER_PREF_DIR=C:/Fireflies_Pipeline/Fireflies_BIN/Sidefx/env\0" L"\0";
    // BOOL test = CreateProcess(
    //     houdini_205_path,
    //     NULL, //args
    //     NULL, //security
    //     NULL, //thread security
    //     FALSE, //thread legacy
    //     CREATE_UNICODE_ENVIRONMENT, //flag
    //     (LPVOID)env, 
    //     NULL,
    //     &si,
    //     &pi
    // );
    // if (!test) {
    //     std::cerr << "Process cannot be created :" << GetLastError(); 
    // }
    // WaitForSingleObject(pi.hProcess, INFINITE);
    
    // CloseHandle(pi.hProcess);
    // CloseHandle(pi.hThread);

    // const wchar_t env[]= L"HOUDINI_USER_PREF_DIR=C:\\Fireflies\\Fireflies_BIN\\Sidefx\\env\0" L"\0";

    return 0;
    #endif

}


int launch_softs::main::houdini_rm27() {

    const char* houdini_path = "C:\\Fireflies\\Common\\Houdini_vars\\houdini_205445\\Houdini20.5.445\\bin";

    check_local_file(houdini_path);

    // std::string farm_path = "C:\\afanasy_test\\cgru";

    // if (!fs::exists(farm_path)) {
    //     std::cout << "Couldn't find the farm path on C" << std::endl;
    //     return 0;
    // }


    

    std::cout << "launching houdini 205_684" << std::endl; 

    #ifdef WIN32
    SetEnvironmentVariable("PYTHONPATH", "C:\\Fireflies\\Common\\Houdini_vars\\houdini_205684\\python310\\lib\\site-packages;C:\\Fireflies\\Fireflies_BIN\\");
    ShellExecute(NULL, "open", "C:/Fireflies/Fireflies_BIN/Sidefx/env/launch_houdini_205684_rm27.bat", NULL, NULL, SW_SHOW);
    return 0;    
    
    #endif

}


void launch_softs::main::usdviewer() {
    const char* viewer_ex = "C:\\Fireflies\\Common\\usd_viewer\\usdview_win32\\scripts\\usdview_gui.bat";


    #ifdef WIN32
    // system(
    //     "C:/Fireflies/Common/usd_viewer/usdview_win32/scripts/usdviewer_gui.bat"
    // );
    // ShellExecute(NULL, "open", "C:\\Fireflies\\Fireflies_BIN\\scripts_py_installs\\launch_usdviewer.bat", NULL, NULL, SW_SHOW);
    ShellExecute(NULL, "open", viewer_ex, NULL, NULL, SW_SHOW);

    #endif
}

void launch_softs::main::rv() {
    ShellExecute(NULL, "open", "C:\\Fireflies\\Common\\rv_200\\bin\\rv.exe", NULL, NULL, SW_SHOW);
}

void launch_softs::main::marmoset() {
    ShellExecute(NULL, "open", "C:\\Fireflies\\Common\\Marmoset\\Toolbag 5\\toolbag.exe", NULL, NULL, SW_SHOW);
}

void launch_softs::main::mari() {
    const char* exe = "C:\\Fireflies\\Common\\mari_701\\Bundle\\bin\\Mari7.1v1.exe";
    
    check_local_file(exe);

    ShellExecute(NULL, "open", exe, NULL, NULL, SW_SHOW);
}


void launch_softs::main::assembly_resolve() {
    const char* resolve_bat = "C:\\Fireflies\\Fireflies_BIN\\fireflies\\asset_resolver\\launch_resolver_main.bat";

    check_local_file(resolve_bat);

    ShellExecute(NULL, "open", resolve_bat, NULL, NULL, SW_SHOW);

}


void launch_softs::main::dl_monitor() {
    const char* exe = "C:\\Fireflies\\Deadline\\bin\\deadlinemonitor.exe";
    ShellExecute(NULL, "open", exe, NULL, NULL, SW_SHOW);

}


void launch_softs::main::nuke_152() {    
    const char* exe = "C:\\Fireflies\\Common\\Nuke_vars\\nuke_152\\Nuke15.2.exe";

    // check_local_file(exe);

    SetEnvironmentVariable("NUKE_PATH", "C:\\Fireflies\\Fireflies_BIN\\Foundry\\Nuke\\env");

    ShellExecute(NULL, "open", exe, NULL, NULL, SW_SHOW);
}


void launch_softs::main::mrv2() {
    const char * exe = "C:\\Fireflies\\Common\\mrv2\\bin\\mrv2.exe";
    check_local_file(exe);

    ShellExecute(NULL, "open", exe, NULL, NULL, SW_SHOW);

}


void launch_softs::main::kitsu() {
    ShellExecute(NULL, NULL, "http://192.168.1.176:4875/", NULL, NULL, SW_SHOW);

}



// env setup 

int launch_softs::init_fireflies_env::init_main_env() {
    std::cout << "coucou" << std::endl; 

    return 0; 
}
