#ifndef _XSH_MACROS_H
#define _XSH_MACROS_H

#if __has_attribute(__fallthrough__)
#define FALLTHROUGH __attribute__((__fallthrough__))
#else
#define FALLTHROUGH do {} while (0)
#endif

#endif /* _XSH_MACROS_H */
