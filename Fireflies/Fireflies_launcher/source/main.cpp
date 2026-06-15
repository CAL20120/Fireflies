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
#include <fstream>

//custom headers
#include "launch_softs.h"

// OPENGL 
#include <GLFW/glfw3.h>
#include <imgui_impl_opengl3.h>
#define GL_SILENCE_DEPRECATION

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

// if glfw dependancies 
#if defined(IMGUI_IMPL_OPENGL_ES32)
#include <GLES2/gl2.h>
#endif
// #include "stb_image.h"

//main windows implementations
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#endif

//namespaces
using namespace std; 
namespace fs = std::filesystem; 

// glfw error callback using stderr
static void glfw_callback_error(int error, const char* description) {
    fprintf(stderr, "error glfw %d: %s\n", error, description);
}


GLuint LoadTextureFile(const char* filename) {
    int width, height, channel;
    unsigned char* data = stbi_load(filename, &width, &height, &channel, 4);
    if (!data) {
        return 0;
    }
    GLuint texture; 
    glGenTextures(1, &texture);
    glBindTexture(GL_TEXTURE_2D, texture);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data);

    stbi_image_free(data);
    return texture;
}


// void login_callback() {
//     static char username[12] = ""; 
//     static char password[64] = ""; 

//     static bool login_success = false;
//     static bool login_failed = false;

//     ImGui::InputText("Username", username, IM_ARRAYSIZE(username));
//     ImGui::InputText("Password", password, IM_ARRAYSIZE(password), ImGuiInputTextFlags_Password);

//     if (ImGui::Button("Login")) {
//        cout << "Gathering login information";
//         ShellExecute(NULL, "open", "PATH", NULL, NULL, SW_SHOW);
//     }

//     if (login_success == true) {
//         cout << "logged as " << username; 
//     }
// }


static char username[16] = ""; 
static char password[64] = ""; 
static char user_email[64] = "";

void write_login_prefs() {
    
    std::string login_prefs_dir = "C:\\Fireflies\\Common\\fmk_user_prefs";
    std::string login_prefs = "C:\\Fireflies\\Common\\fmk_user_prefs\\login_prefs.txt";

    if (!fs::exists(login_prefs_dir)) {
        fs::create_directories(login_prefs_dir);
    }


    bool username_input = ImGui::InputText("Username", username, IM_ARRAYSIZE(username));
    bool password_input = ImGui::InputText("Password", password, IM_ARRAYSIZE(password), ImGuiInputTextFlags_Password);
    bool email_input = ImGui::InputText("Email (for kitsu)", user_email, IM_ARRAYSIZE(user_email));

    if (username_input or password_input or email_input) {
        std::ofstream file(login_prefs, std::ios::trunc);

        if (file.is_open()) {
            file << username << "\n";
            file << password << "\n";
            file << user_email << "\n";

            file.close();
        }
    }

}


std::string file_prefs = "C:\\Fireflies\\Common\\fmk_user_prefs\\user_prefs_dir.txt";
char prefs_buffer[512] = "";

void save_prefs() {
    if (!fs::exists(file_prefs)) {
        fs::create_directories(file_prefs);
    }

    std::ofstream file(file_prefs, std::ios::trunc);
    
    if (file.is_open()) {
        file << prefs_buffer; 
        
        file.close();   
    }
}

std::string load_prefs() {
    std::ifstream(file_prefs);

    if (file_prefs.is_open()) {
        std::string prefs_line; 
        std::getline(file_prefs, prefs_line);
        file_prefs.close();
        strncpy(prefs_buffer, prefs_line.c_str(), sizeof(prefs_buffer));
    }
    return prefs_buffer;
}



//bool init for subwindows
class wins_appear {
    public: 
    bool show_window = false;
    bool show_softs = false; // show software list, to launch specific software whith custom env variables. 
    bool show_prods = false;
    bool show_tasks = false;
    bool show_settings = false; 
};
wins_appear winToggle; 

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
        // fd_dirs_str = DEntry.path();
        /*
        for (const auto& lign : fd_dirs_str) {
            if (lign.find("tasks") != string::npos) {
                *foundL = lign; 
            }
        }
        ++fd_dirs_int;
        */
    }
    return fd_dirs_int;
}


std::vector<std::string> find_mari_scenes() {
    std::string test_path = "R:\\Christopher_LUCAS\\PRODS\\test_dev\\001\\01\\texturing\\output_mari_udims";

    if (!fs::exists(test_path)) {
        cout << "path not valid";
        return {};
    }

    std::vector<std::string> target_files; 

    for (const auto& file : fs::directory_iterator(test_path)) {
        if (file.path().extension() == ".exr") {
            target_files.push_back(file.path().filename().string());
        }
    }

    // for (const auto& file: target_files) {
    //     cout << file << "\n";
    // }

    return target_files;
}

bool show_mari_win = false;
void show_mari_files() {
    std::vector target_files = find_mari_scenes();

    ImGui::Begin("Mari scenes"); 

    if (ImGui::BeginTable("scenes", 1, ImGuiTableFlags_Borders | ImGuiTableFlags_RowBg)) {
        ImGui::TableSetupColumn("file name:");
        ImGui::TableHeadersRow();

        for (const auto& file : target_files) {
            ImGui::TableNextRow();
            ImGui::TableSetColumnIndex(0);

            if (ImGui::Selectable(file.c_str(), ImGuiSelectableFlags_SpanAllColumns)) {
                cout << file.c_str();
            }

            // ImGui::TextUnformatted(file.c_str());

        }


        ImGui::EndTable();
    }

    ImGui::End();

}

int main() {
    
    cout << " /$$$$$$$$ /$$                      /$$$$$$  /$$ /$$                    " << endl;
    cout << "" << endl;
    cout << "| $$_____/|__/                     /$$__  $$| $$|__/ " << endl;
    cout << "| $$       /$$  /$$$$$$   /$$$$$$ | $$  \__/| $$ /$$  /$$$$$$   /$$$$$$$" << endl;
    cout << "| $$$$$   | $$ /$$__  $$ /$$__  $$| $$$$    | $$| $$ /$$__  $$ /$$_____/" << endl;
    cout << "| $$__/   | $$| $$  \__/| $$$$$$$$| $$_/    | $$| $$| $$$$$$$$|  $$$$$$" << endl;
    cout << "| $$      | $$| $$      | $$_____/| $$      | $$| $$| $$_____/ \____  $$" << endl;
    cout << "| $$      | $$| $$      |  $$$$$$$| $$      | $$| $$|  $$$$$$$ /$$$$$$$/" << endl;
    cout << "|__/      |__/|__/       \_______/|__/      |__/|__/ \_______/|_______/" << endl;

    // load user prefs 
    load_prefs();

    glfwSetErrorCallback(glfw_callback_error);
    if (!glfwInit()) {
        cout << "glfw error" << endl;
        return 1; 
    }
    //SETUP glfw
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    
    //def window
    float mscale = ImGui_ImplGlfw_GetContentScaleForMonitor(glfwGetPrimaryMonitor());
    const char* winName = "Fireflies";
    GLFWwindow* window = glfwCreateWindow((int)(726 * mscale), (int)(1024 * mscale), winName, nullptr, nullptr);
    if (window == nullptr) {
        return 1; 
    }
    
     //CONTEXT
    IMGUI_CHECKVERSION();
    ImGuiContext* ctx = ImGui::CreateContext();
    ImGui::SetCurrentContext(ctx);
    ImGui::StyleColorsDark();

    //Window color and style

    auto main_color = ImVec4(0.220, 0.220, 0.220, 1.0);

    ImGuiStyle& window_style = ImGui::GetStyle();
    window_style.Colors[ImGuiCol_TitleBgActive] = ImVec4(0.3f, 0.0f, 0.0f, 1.0f);
    window_style.Colors[ImGuiCol_TitleBg] = ImVec4(0.2f, 0.0f, 0.0f, 1.0f);

    window_style.Colors[ImGuiCol_Button] = main_color;
    window_style.Colors[ImGuiCol_ButtonHovered] = ImVec4(0.2f, 0.0f, 0.0f, 1.0f);

    window_style.Colors[ImGuiCol_InputTextCursor] = main_color;
    window_style.Colors[ImGuiCol_FrameBg] = main_color;

    
    // window_style.Colors[ImGuiCol_Header] = ImVec4

    // Main controls 
    ImGuiIO& io = ImGui::GetIO();
    // | prend le bit affecté à une variable et l'affecte à l'autre, c'est du bit à bit. 
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableSetMousePos;
    io.ConfigFlags |= ImGuiConfigFlags_DockingEnable;
    io.ConfigFlags |= ImGuiConfigFlags_ViewportsEnable;

    glfwMakeContextCurrent(window); 

    glfwSwapInterval(1); 


    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init();

    GLuint houdini_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\houdini_logo.png");
    GLuint houdini_rm27_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\houdini_logo_rm27.png");
    
    GLuint nuke_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\nuke_logo.png");

    GLuint maya_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\maya_logo.png");
    
    GLuint rv_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\rv_logo.png");
    
    GLuint usd_viewer_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\usd_viewer_logo.png");
    GLuint marmoset_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\marmoset_toolbag.png");
    GLuint mari_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\mari_logo.png");
    GLuint assembly_tex = LoadTextureFile("C:\\Fireflies\\Fireflies_BIN\\fireflies\\logos\\assembly_maker.png");
    GLuint kitsu_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\kitsu.png");
    
    GLuint dl_monitor_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\dl_worker.png");
    
    GLuint check_debug_tex = LoadTextureFile("C:\\Fireflies\\Fireflies\\softs_logo\\checkbox_debug.jpg");


//MAIN WINDOW
    while(!glfwWindowShouldClose(window)) {
        
        glfwPollEvents();
        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();
        ImGui::SetNextItemAllowOverlap();

        ImGui::Begin("Fireflies");

        ImGui::Text("BIENVENUE !");
        
        ImGui::Text(
            "Fireflies pipeline \nEn cas de bug merci de me contacter par discord @cal1348"
        );
        ImGui::Separator();

        ImGui::Text("PRODS PATH :");
        
        ImGui::Text("Attention pas de chemins longs !");
        if (ImGui::InputText("##cpathDyn", prefs_buffer, IM_ARRAYSIZE(prefs_buffer))) {
            save_prefs();
        }
        ImGui::Separator();
        
        ImGui::Text("Login:");  
        write_login_prefs();

        ImGui::Separator();
        
        //buttons to launch subwindows 
        if (ImGui::Button("SOFTS")) {
            winToggle.show_softs = true;
        }

        //shot and tasks
        // if (ImGui::Button("Prods")) {
        //     winToggle.show_prods = true;
        // }

    // EXPLORER begin
        IGFD::FileDialogConfig config; 
        config.path = lastPath;
        if (ImGui::Button("Explorer")) {
            call_explorerDialog(config);
            // ImGuiFileDialog::Instance()->OpenDialog(explorerWinName, "Project File Explorer", pathTest);
        }

        // if (ImGui::Button("test_mari")) {
        //     show_mari_win = true;
        //     cout << "showing mari files in prod";
        // }

        if (show_mari_win) {
            // cout << "showing mari files in prod";
            show_mari_files();
        }


        if (ImGui::Button("DOC")) {
    ShellExecute(NULL, "open", "C:\\Fireflies\\Fireflies_BIN\\fireflies\\fireflies_utils\\doc\\launch_doc.bat", NULL, NULL, SW_SHOW);
    // system("C:\\Fireflies\\Fireflies_BIN\\fireflies\\fireflies_utils\\doc\\launch_doc.bat");

}

        ImGui::End();


        // explorer main window when ->OpenDIalog() is called 
        //checking is path changed and copying new data 
        if (strcmp(lastPath, pathInit) != 0) {
            //avoid program crashing when this tab is open
            if (winToggle.show_prods) {
                winToggle.show_prods = false;
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


        if (winToggle.show_softs) {
            // LAUNCH SOFTS
            ImGui::Begin("Softs");
            ImGui::SeparatorText("Launch a software:");

            //buttons
            ImGui::Text("MAIN");
            int ic_height = 500;
            int ic_width = 500;

            // GLuint houdini_icon = LoadTexture("frontend/ressources/icons/houdini_ic.png", &ic_height, &ic_width);
            // if (ImGui::ImageButton((void*)(intptr_t)houdini_icon, ImVec2(32, 32))) {
            // if (ImGui::Button("Houdini")) {
            //     launch_softs::main::houdini();
            // }

            if (houdini_tex!=0 && ImGui::ImageButton("##h", (ImTextureID)(intptr_t)houdini_tex, ImVec2(64, 64))) {
                std::cout << "launching houdini" << "\n";
                launch_softs::main::houdini();
            }

            
            ImGui::SameLine();
            if (houdini_rm27_tex!=0 && ImGui::ImageButton("##hrm27", (ImTextureID)(intptr_t)houdini_rm27_tex, ImVec2(64, 64))) {
                std::cout << "launching houdini" << "\n";
                launch_softs::main::houdini_rm27();
            }



            ImGui::SameLine();
            if (assembly_tex!=0 && ImGui::ImageButton("##am", (ImTextureID)(intptr_t)assembly_tex, ImVec2(64, 64))) {
                std::cout << "launching assembly resolver" << "\n";
                launch_softs::main::assembly_resolve();
            }


            // ImGui::SameLine();
            if (maya_tex!=0 && ImGui::ImageButton("##m", (ImTextureID)(intptr_t)maya_tex, ImVec2(64, 64))) {
                std::cout << "launching maya" << "\n";
                launch_softs::main::maya();
            }

            
            ImGui::SameLine();
            if (rv_tex!=0 && ImGui::ImageButton("##v", (ImTextureID)(intptr_t)rv_tex, ImVec2(64, 64))) {
                std::cout << "launching maya" << "\n";
                launch_softs::main::rv();
            }


            ImGui::SameLine();
            if (nuke_tex!=0 && ImGui::ImageButton("##nuke", (ImTextureID)(intptr_t)nuke_tex, ImVec2(64, 64))) {
                std::cout << "launching nuke 152" << "\n";
                launch_softs::main::nuke_152();
            }           


            // ImGui::SameLine();
            if (marmoset_tex!=0 && ImGui::ImageButton("##mt", (ImTextureID)(intptr_t)marmoset_tex, ImVec2(64, 64))) {
                std::cout << "launching marmoset toolbag" << "\n";
                launch_softs::main::marmoset();
            }

            ImGui::SameLine();
            if (mari_tex!=0 && ImGui::ImageButton("##mi", (ImTextureID)(intptr_t)mari_tex, ImVec2(64, 64))) {
                std::cout << "launching mari" << "\n";
                launch_softs::main::mari();
            }

            // ImGui::SameLine();
            // if (check_debug_tex!=0 && ImGui::ImageButton("##mrv", (ImTextureID)(intptr_t)check_debug_tex, ImVec2(64, 64))) {
            //     std::cout << "launching mrv2" << "\n";
            //     launch_softs::main::mrv2();
            // }
            

            ImGui::SeparatorText("UTILS :");

            if (usd_viewer_tex!=0 && ImGui::ImageButton("##u", (ImTextureID)(intptr_t)usd_viewer_tex, ImVec2(64, 64))) {
                std::cout << "launching usd viewer" << "\n";
                launch_softs::main::usdviewer();
            }

            ImGui::SameLine();
            if (dl_monitor_tex!=0 && ImGui::ImageButton("##dl_m", (ImTextureID)(intptr_t)dl_monitor_tex, ImVec2(64, 64))) {
                std::cout << "launching deadline monitor" << "\n";
                launch_softs::main::dl_monitor();
            }


            ImGui::SameLine();
            if (kitsu_tex!=0 && ImGui::ImageButton("##kitsu", (ImTextureID)(intptr_t)kitsu_tex, ImVec2(64, 64))) {
                std::cout << "opening kitsu" << "\n";
                launch_softs::main::kitsu();
            }


            
            ImGui::Separator();
            if (ImGui::Button("Close")) {
                winToggle.show_softs = false;
            }

            //SOFTS
            ImGui::End();
        }
        
        static int scaned_bars = {0};
        if (winToggle.show_prods) {

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
                winToggle.show_prods = false;
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
        
        const auto color = ImVec4(0.3f, 0.3f, 0.3f, 1.0f);
        glClearColor(0.15f, 0.15f, 0.15f, 1.0f); // gives the color to the buffer bit
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        
        // SETUP RENDER
        ImGui::Render();
        int display_h, display_w; //unused for the moment
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

        if (io.ConfigFlags & ImGuiConfigFlags_ViewportsEnable) {
            GLFWwindow* current_context = glfwGetCurrentContext();
            ImGui::UpdatePlatformWindows();
            ImGui::RenderPlatformWindowsDefault();
            glfwMakeContextCurrent(current_context);
        }

        glfwSwapBuffers(window);
    }

    //Destroying context and window
    glDeleteTextures(1, &houdini_tex);
    glDeleteTextures(1, &houdini_rm27_tex);

    glDeleteTextures(1, &maya_tex);

    glDeleteTextures(1, &rv_tex);

    glDeleteTextures(1, &usd_viewer_tex);
    glDeleteTextures(1, &marmoset_tex);
    glDeleteTextures(1, &mari_tex);

    glDeleteTextures(1, &assembly_tex);
    glDeleteTextures(1, &dl_monitor_tex);
    glDeleteTextures(1, &kitsu_tex);

    glDeleteTextures(1, &nuke_tex);

    glDeleteTextures(1, &check_debug_tex);


    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(window);
    glfwTerminate();
    
    //END 
    return 0; 
}