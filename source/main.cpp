// Global libraries
#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "ImGuiFileDialog.h"
#include <stdio.h>
#include <cstdlib>
#include <filesystem> //usefull to fetch folder and paths
#include <string>
#include <cstring> 

#include <iostream>

//custom headers
#include "launch_softs.h"

// OPENGL 
#include <GLFW/glfw3.h>
#include <imgui_impl_opengl3.h>
#define GL_SILENCE_DEPRECATION

// if glfw dependancies 
#if defined(IMGUI_IMPL_OPENGL_ES32)
#include <GLES2/gl2.h>
#endif

//main windows implementations
#ifdef _WIN32
#include <windows.h>
#endif

//namespaces
using namespace std; 
namespace fs = std::filesystem; 

// glfw error callback using stderr
static void glfw_callback_error(int error, const char* description) {
    fprintf(stderr, "error glfw %d: %s\n", error, description);
}

//test git

//TODO Create window for user login with tasks implementation based on user. 
static char username[12] = ""; 
static char password_input[64] = "";
struct isValid_Login {
    bool login_Valid = false; 
    bool login_Failed = false; 
};
void draw_LoginWin() {
    ImGui::Begin("Login");

    ImGui::InputText("Username", username, IM_ARRAYSIZE(username));

    ImGui::End();
}


//bool init for subwindows
struct sh_windows {
    bool test = false;
};
bool show_window = false;
bool show_softs = false; // show software list, to launch specific software whith custom env variables. 
bool show_shots_main = false;
bool show_tasks = false;
bool show_settings = false; 

//explorer dynamic var setup
const char* explorerWinName = "Project Explorer";
char lastPath[512] = "";
char pathInit[512] = "";
bool path_changing = false;


//function to call explorer okay
void call_explorerDialog(const IGFD::FileDialogConfig& config) {
    ImGuiFileDialog::Instance()->OpenDialog(explorerWinName, "Project File Explorer", ".cpp", config);
}

// fetch work folders 
int fetch_folders(char* projectPath) {
    std::string pjPath = projectPath; 
    std::string pathTest = "/Users";
    int fd_dirs_int = 0; 
    std::string fd_dirs_str;
    char foundL[512]; 
    for (const auto& DEntry : fs::directory_iterator(projectPath)) {
        fd_dirs_str = DEntry.path();
        for (const auto& lign : fd_dirs_str) {
            if (lign.find("tasks") != string::npos) {
                *foundL = lign; 
            }
        }
        ++fd_dirs_int;
        
    }
    return fd_dirs_int;
}


int main() {
    glfwSetErrorCallback(glfw_callback_error);
    if (!glfwInit()) {
        cout << "erreur glfw, vérifiez l'installation de opengl3" << endl;
        return 1; 
    }
    //SETUP glfw
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    
    //def window
    float mscale = ImGui_ImplGlfw_GetContentScaleForMonitor(glfwGetPrimaryMonitor());
    GLFWwindow* window = glfwCreateWindow((int)(1280 * mscale), (int)(720 * mscale), "MothFly FMK", nullptr, nullptr);
    if (window == nullptr) {
        return 1; 
    }
    
     //CONTEXT
    IMGUI_CHECKVERSION();
    ImGuiContext* ctx = ImGui::CreateContext();
    ImGui::SetCurrentContext(ctx);
    ImGui::StyleColorsDark();

    // Main controls 
    ImGuiIO& io = ImGui::GetIO();
    // | prend le bit affecté à une variable et l'affecte à l'autre, c'est du bit à bit. 
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableSetMousePos;

    glfwMakeContextCurrent(window); 

    //control vsync from checkbox in settings tab
    bool vsync_active; 
    const char* vsync_name = "VSync"; 
    glfwSwapInterval(vsync_active); 


    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init();


//MAIN WINDOW
    while(!glfwWindowShouldClose(window)) {
        
        glfwPollEvents();
        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();
        ImGui::SetNextItemAllowOverlap();

        ImGui::Begin("MothFly FMK");

        ImGui::Text("BIENVENUE !");
        ImGui::Text(
            "Ceci est une première version du framerwork, \n elle peut donc comporter des bugs, \n merci de les faire parvenir si besoin ;)"
        );
        ImGui::Separator();

        ImGui::Text("PROJECT PATH :");
        ImGui::Text("Attention pas de chemins longs !");
        ImGui::InputText("##cpathDyn", pathInit, IM_ARRAYSIZE(pathInit));
        ImGui::Separator();
        
        
        //buttons to launch subwindows 
        if (ImGui::Button("SOFTS")) {
            show_softs = true;
        }

        //shot and tasks
        if (ImGui::Button("Shot et tâches")) {
            show_shots_main = true;
        }
        if (ImGui::Button("Settings")) {
            show_settings = true; 
        }

    // EXPLORER begin
        IGFD::FileDialogConfig config; 
        config.path = lastPath;
        if (ImGui::Button("Explorer")) {
            call_explorerDialog(config);
            // ImGuiFileDialog::Instance()->OpenDialog(explorerWinName, "Project File Explorer", pathTest);
        }
        ImGui::End();

        // explorer main window when ->OpenDIalog() is called 
        //checking is path changed and copying new data 
        if (strcmp(lastPath, pathInit) != 0) {
            //avoid program crashing when this tab is open
            if (show_shots_main) {
                show_shots_main = false;
            }
            ImGuiFileDialog::Instance()->Close();
            IGFD::FileDialogConfig config;
            strcpy(lastPath, pathInit);
            config.path = lastPath;
            call_explorerDialog(config);
            
        }


        if (ImGuiFileDialog::Instance()->Display(explorerWinName)) {
            if (ImGuiFileDialog::Instance()->IsOk()) {
                std::string filePathName = ImGuiFileDialog::Instance()->GetFilePathName();
            }
            ImGuiFileDialog::Instance()->Close();
        }


        if (show_softs) {
            // LAUNCH SOFTS
            ImGui::Begin("Softs");
            ImGui::SeparatorText("Lancer un logiciel :");

            //buttons
            ImGui::Text("MAIN");
            if (ImGui::Button("Houdini")) {
                launch_softs::main::houdini();
            }
            if (ImGui::Button("Maya")) {
                cout << "lancer maya";
            }
            if (ImGui::Button("Mari")) {
                //launch mari
            }
            if (ImGui::Button("ZBrush")) {
                //launch zbrush
            }

            ImGui::SeparatorText("OTHERS :");

            if (ImGui::Button("USD VIEWER")) {
                launch_softs::main::usdviewer();
            }

            if (ImGui::Button("calc")) {
                launch_softs::main::maya();
            }
            
            ImGui::Separator();
            if (ImGui::Button("Close")) {
                show_softs = false;
            }

            //SOFTS
            ImGui::End();
        }
        
        static int scaned_bars = {0};
        if (show_shots_main) {

            /*
            ImGui::Begin("DRAW_COLUMNS"); 

            ImGui::Columns(fetch_folders(lastPath));
            ImGui::SetColumnOffset(0, 5);
            ImGui::Separator();
            if (ImGui::Button("Close")) {
                show_shots_main = false;
            }
            ImGui::End();
            */

            ImGui::Begin("Shots et tâches");
            if (ImGui::BeginTabBar("Test")) {
                for (int i = 0; i < fetch_folders(lastPath); i++) {
                    std::string name = "task_" + std::to_string(i);
                    if (ImGui::BeginTabItem(name.c_str())) {
                        ImGui::Text("test %d", i);
                        ImGui::EndTabItem();
                    }
                }
                ImGui::EndTabBar();
            }
            if (ImGui::Button("close")) {
                show_shots_main = false;
            }
            ImGui::End();
           
            /*
            ImGui::Begin("DRAW_TABS");
            if (ImGui::BeginTabBar("test")) {
                if (ImGui::BeginTabItem("testItem")) {
                    ImGui::Text("coucou");
                    ImGui::EndTabItem();
                }
                ImGui::EndTabBar();
            }
            ImGui::End();
            */
        }
        

        if (show_settings) {
            ImGui::Begin("Settings");
            ImGui::Checkbox(vsync_name, &vsync_active);
            ImGui::Separator();
            if (ImGui::Button("Close")) {
                show_settings = false;
            }
            ImGui::End();
        }

        //debug tab
        ImGui::Begin("Debug");
        const char* check_n = "Test";
        bool test_bl = true; 
        ImGui::Checkbox(check_n, &test_bl);
        
        if (ImGui::Button("Show")) {
            show_window = true;
        }
        

        if (show_window) {
            ImGui::Begin("test"); 
            if (ImGui::Button("close")) {
                show_window = false;
            }
            ImGui::End();
        }

        ImGui::End();

        const auto color = ImVec4(0.3f, 0.3f, 0.3f, 1.0f);
        glClearColor(0.2f, 0.2f, 0.2f, 1.0f); // gives the color to the buffer bit
        glClear(GL_COLOR_BUFFER_BIT);
        
        // SETUP RENDER
        ImGui::Render();
        int display_h, display_w; //unused for the moment
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
        glfwSwapBuffers(window);
    }
    //Destroying context and window
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(window);
    glfwTerminate();
    //END 
    return 0; 
}