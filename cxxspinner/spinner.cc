#include <locale>
#include <iostream>
#include <string>
#include <memory>
#include <mutex>
#include <thread>
#include <chrono>
#include <codecvt>

#include "spinner.h"

static unsigned char spin_chrs[] = {
    0b10111001,
    0b11111000,
    0b11110100,
    0b11100110,
    0b11000111,
    0b01001111,
    0b00011111,
    0b00111011,
};

static std::string GetSpinChr(size_t state) {
    char16_t chr = 0x2800 + spin_chrs[state % sizeof(spin_chrs)];
    std::u16string wstr(1, chr);
    std::wstring_convert<std::codecvt_utf8_utf16<char16_t>,char16_t> converter;
    return converter.to_bytes(wstr);
}


void Spinner::SpinnerThread() {
    while (!this->stop) {
        std::cerr << "\33[2K\r" << GetSpinChr(this->state) << " " << this->message;
        if (!this->mutex.try_lock_for(std::chrono::milliseconds(this->spin_ms))) {
            this->state++;
        }
    }
}

Spinner::Spinner(int spin_ms) {
    this->spin_ms = spin_ms;
    this->stop = false;
    this->mutex.lock();
    this->message = "";
    this->thread = std::make_unique<std::thread>([this]{this->SpinnerThread();});
}

void Spinner::SetMessage(std::string message) {
    this->message = message;
    this->mutex.unlock();
}

Spinner::~Spinner() {
    this->stop = true;
    this->mutex.unlock();
    this->thread->join();
}
