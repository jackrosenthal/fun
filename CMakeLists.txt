cmake_minimum_required(VERSION 3.13.1)

set(ZEPHYR_TOOLCHAIN_VARIANT espressif)
set(BOARD esp32)

find_package(Zephyr REQUIRED)
project(esptest)
target_sources(app PRIVATE main.c)
