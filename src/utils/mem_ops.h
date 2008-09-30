/*************************************************
* Memory Operations Header File                  *
* (C) 1999-2007 Jack Lloyd                       *
*************************************************/

#ifndef BOTAN_MEMORY_OPS_H__
#define BOTAN_MEMORY_OPS_H__

#include <botan/types.h>
#include <cstring>

namespace Botan {

/*************************************************
* Memory Manipulation Functions                  *
*************************************************/
template<typename T> inline void copy_mem(T* out, const T* in, length_type n)
   { std::memmove(out, in, sizeof(T)*n); }

template<typename T> inline void clear_mem(T* ptr, length_type n)
   { std::memset(ptr, 0, sizeof(T)*n); }

template<typename T> inline void set_mem(T* ptr, length_type n, byte val)
   { std::memset(ptr, val, sizeof(T)*n); }

template<typename T> inline bool same_mem(const T* p1, const T* p2, length_type n)
   { return (std::memcmp(p1, p2, sizeof(T)*n) == 0); }

}

#endif
