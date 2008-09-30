/*************************************************
* EME/EMSA Base Class Source File                *
* (C) 1999-2008 Jack Lloyd                       *
*************************************************/

#include <botan/pk_pad.h>

namespace Botan {

/*************************************************
* Encode a message                               *
*************************************************/
SecureVector<byte> EME::encode(const byte msg[], length_type msg_len,
                               u32bit key_bits,
                               RandomNumberGenerator& rng) const
   {
   return pad(msg, msg_len, key_bits, rng);
   }

/*************************************************
* Encode a message                               *
*************************************************/
SecureVector<byte> EME::encode(const MemoryRegion<byte>& msg,
                               length_type key_bits,
                               RandomNumberGenerator& rng) const
   {
   return pad(msg, msg.size(), key_bits, rng);
   }

/*************************************************
* Decode a message                               *
*************************************************/
SecureVector<byte> EME::decode(const byte msg[], length_type msg_len,
                               length_type key_bits) const
   {
   return unpad(msg, msg_len, key_bits);
   }

/*************************************************
* Decode a message                               *
*************************************************/
SecureVector<byte> EME::decode(const MemoryRegion<byte>& msg,
                               length_type key_bits) const
   {
   return unpad(msg, msg.size(), key_bits);
   }

}
