#ifndef _SPINNER_H
#define _SPINNER_H

#include <string>
#include <mutex>
#include <memory>
#include <thread>

class Spinner {
public:
    Spinner(int spin_ms);
    ~Spinner();
    void SetMessage(std::string message);

private:
    void SpinnerThread();
    size_t state;
    int spin_ms;
    bool stop;
    std::timed_mutex mutex;
    std::string message;
    std::unique_ptr<std::thread> thread;
};

#endif /* _SPINNER_H */
