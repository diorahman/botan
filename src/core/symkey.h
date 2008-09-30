/*************************************************
* OctetString Header File                        *
* (C) 1999-2007 Jack Lloyd                       *
*************************************************/

#ifndef BOTAN_SYMKEY_H__
#define BOTAN_SYMKEY_H__

#include <botan/secmem.h>
#include <string>

namespace Botan {

/*************************************************
* Octet String                                   *
*************************************************/
class BOTAN_DLL OctetString
   {
   public:
      length_type length() const { return bits.size(); }
      SecureVector<byte> bits_of() const { return bits; }

      const byte* begin() const { return bits.begin(); }
      const byte* end() const   { return bits.end(); }

      std::string as_string() const;

      OctetString& operator^=(const OctetString&);

      void set_odd_parity();

      void change(length_type);
      void change(const std::string&);
      void change(const byte[], length_type);
      void change(const MemoryRegion<byte>& in) { bits = in; }

      OctetString(class RandomNumberGenerator&, length_type len);
      OctetString(const std::string& str = "") { change(str); }
      OctetString(const byte in[], length_type len) { change(in, len); }
      OctetString(const MemoryRegion<byte>& in) { change(in); }
   private:
      SecureVector<byte> bits;
   };

/*************************************************
* Operations on Octet Strings                    *
*************************************************/
BOTAN_DLL bool operator==(const OctetString&, const OctetString&);
BOTAN_DLL bool operator!=(const OctetString&, const OctetString&);
BOTAN_DLL OctetString operator+(const OctetString&, const OctetString&);
BOTAN_DLL OctetString operator^(const OctetString&, const OctetString&);

/*************************************************
* Alternate Names                                *
*************************************************/
typedef OctetString SymmetricKey;
typedef OctetString InitializationVector;

}

#endif
