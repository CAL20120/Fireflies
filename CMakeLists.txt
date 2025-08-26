cmake_minimum_required(VERSION 3.26.5)
project(VFX_FRAMEWORK VERSION 0.0.1 LANGUAGES CXX)

include(CTest)
enable_testing()

set(CMAKE_CXX_STANDARD 17)
add_executable(MothFLy_FMK source/main.cpp source/launch_softs.cpp)

## libraries pour IMGUI 

add_library(
    ImGui STATIC
    include/third_party/imgui/imgui.cpp
    include/third_party/imgui/imgui_draw.cpp
    include/third_party/imgui/imgui_tables.cpp
    include/third_party/imgui/imgui_widgets.cpp
    include/third_party/imgui/backends/imgui_impl_glfw.cpp
    include/third_party/imgui/backends/imgui_impl_opengl3.cpp
    include/third_party/ImGuiFileDialog/ImGuiFileDialog.cpp
)

## OpenGL et glfw3 dependencies
find_package(glfw3 REQUIRED)
find_package(OpenGL REQUIRED)

## correction erreur de compilation pour glfw3
find_package(PkgConfig REQUIRED)
pkg_search_module(GLFW REQUIRED glfw3)


target_include_directories(
    MothFLy_FMK 
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include/third_party/imgui
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include/third_party/imgui/backends
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include/headers
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include/ImGuiFileDialog
    )
target_include_directories(
    ImGui 
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include/third_party/imgui
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include/third_party/imgui/backends
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include/third_party/ImGuiFileDialog
    PUBLIC ${GLFW_INCLUDE_DIRS}
)

target_link_libraries(
    MothFLy_FMK PRIVATE ImGui
    glfw ${OPENGL_LIBRARIES}
    )
