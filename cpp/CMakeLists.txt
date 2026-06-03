cmake_minimum_required(VERSION 3.18)
project(panda_ai_training_arena_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(arena_native SHARED path_score.cpp)

target_compile_definitions(arena_native PRIVATE ARENA_NATIVE_EXPORTS)
