#include <chrono>
#include <thread>

#include "spinner.h"

int main(int argc, char *argv[]) {
    Spinner spinner(100);

    spinner.SetMessage("Initiating startup sequence...");
    std::this_thread::sleep_for(std::chrono::seconds(5));

    spinner.SetMessage("Waiting for connection...");
    std::this_thread::sleep_for(std::chrono::seconds(5));

    spinner.SetMessage("Connection acquired.  Booting system...");
    std::this_thread::sleep_for(std::chrono::seconds(5));

    return 0;
}
