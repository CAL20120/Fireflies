#pragma once

namespace launch_softs {
    class main {
        public: 
            static void maya();
            static int houdini();
            static int houdini_rm27();
            static void mari();
            static void nuke_152();

            // static void zbrush();
            static void openrv();
            static void usdviewer();
            static void rv();
            static void marmoset();
            static void unreal_engine();
            static void assembly_resolve();
            
            static void dl_monitor();
            static void mrv2();
            static void kitsu();
    };

    class init_fireflies_env {
        public:
        static int init_main_env();
    };
}
