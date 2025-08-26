#include <iostream>
#include <cstdlib> // usefull to interact with the os and launch softs
#include "launch_softs.h"

void launch_softs::main::maya() {
    #ifdef __linux__
    system("gnome-calculator");
    #endif
    
    #ifdef WIN32
    system(calc)
    #endif

    #ifdef __APPLE__
    system("calculator");
    #endif
}

void launch_softs::main::houdini() {
    std::cout << "Houdini launched";
    #ifdef __linux__
    /* setenv(); */ // TODO: ajouter la var d'env houdini
    system("/opt/hfs20.5.445/bin/houdini-bin");
    #endif

    #ifdef WIN32
    //env vars
    _putenv("HFS=C:\\"); //indiquer var houdini
    _putenv("PATH=C::\\Program Files\\Side Effects Software\\Houdinivar\\bin;%PATH%"); 
    system("houdini");
    #endif

    #ifdef __APPLE__ 
    system("houdini");
    #endif
}

void launch_softs::main::mari() {
    
}

void launch_softs::main::zbrush() {
    #ifdef __linux__
    system("zbrush");
    #endif
}

void launch_softs::main::openrv() {
    #ifdef __linux__
    system("openrv");
    #endif

    #ifdef __APPLE__
    #endif

    #ifdef WIN32
    #endif
}

//usd related 

void launch_softs::main::usdviewer() {
    #ifdef __linux__
    system(
        "chmod +x 'softs_tp3/usd_viewer/usd.py311.manylinux_2_35_x86_64.usdview.release@0.25.05-25f3d3d8/scripts/usdview_gui.sh'"
    );
    #endif

    #ifdef WIN32
    #endif
}