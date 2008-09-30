/*************************************************
* Algorithm Lookup Header File                   *
* (C) 1999-2007 Jack Lloyd                       *
*************************************************/

#ifndef BOTAN_LOOKUP_H__
#define BOTAN_LOOKUP_H__

#include <botan/base.h>
#include <botan/enums.h>
#include <botan/filters.h>
#include <botan/mode_pad.h>
#include <botan/kdf.h>
#include <botan/pk_pad.h>
#include <botan/libstate.h>
#include <botan/s2k.h>

namespace Botan {

/*************************************************
* Retrieve an object from the lookup table       *
*************************************************/
BOTAN_DLL const BlockCipher*
retrieve_block_cipher(Library_State&, const std::string&);

BOTAN_DLL const StreamCipher*
retrieve_stream_cipher(Library_State&, const std::string&);

BOTAN_DLL const HashFunction*
retrieve_hash(Library_State&, const std::string&);

BOTAN_DLL const MessageAuthenticationCode*
retrieve_mac(Library_State&, const std::string&);

BOTAN_DLL const S2K* retrieve_s2k(Library_State&, const std::string&);

BOTAN_DLL const BlockCipherModePaddingMethod*
retrieve_bc_pad(Library_State&, const std::string&);

/*************************************************
* Get an algorithm object                        *
*************************************************/
BOTAN_DLL BlockCipher* get_block_cipher(const std::string&);
BOTAN_DLL StreamCipher* get_stream_cipher(const std::string&);
BOTAN_DLL HashFunction* get_hash(const std::string&);
BOTAN_DLL MessageAuthenticationCode* get_mac(const std::string&);
BOTAN_DLL S2K* get_s2k(const std::string&);
BOTAN_DLL const BlockCipherModePaddingMethod* get_bc_pad(const std::string&);

/*************************************************
* Get an EMSA/EME/KDF/MGF function               *
*************************************************/
BOTAN_DLL EME*  get_eme(const std::string&);
BOTAN_DLL EMSA* get_emsa(const std::string&);
BOTAN_DLL MGF*  get_mgf(const std::string&);
BOTAN_DLL KDF*  get_kdf(const std::string&);

/*************************************************
* Get a cipher object                            *
*************************************************/
BOTAN_DLL Keyed_Filter* get_cipher(Library_State&,
                                   const std::string&,
                                   const SymmetricKey&,
                                   const InitializationVector&,
                                   Cipher_Dir);

BOTAN_DLL Keyed_Filter* get_cipher(Library_State&,
                                   const std::string&,
                                   const SymmetricKey&,
                                   Cipher_Dir);

BOTAN_DLL Keyed_Filter* get_cipher(Library_State&,
                                   const std::string&, Cipher_Dir);

/*************************************************
* Check to see if an algorithm exists            *
*************************************************/
BOTAN_DLL bool have_algorithm(const std::string&);

BOTAN_DLL bool have_block_cipher(const std::string&);
BOTAN_DLL bool have_stream_cipher(const std::string&);
BOTAN_DLL bool have_hash(const std::string&);
BOTAN_DLL bool have_mac(const std::string&);

/*************************************************
* Query information about an algorithm           *
*************************************************/
BOTAN_DLL length_type block_size_of(const std::string&);
BOTAN_DLL length_type output_length_of(const std::string&);

BOTAN_DLL bool valid_keylength_for(length_type, const std::string&);
BOTAN_DLL length_type min_keylength_of(const std::string&);
BOTAN_DLL length_type max_keylength_of(const std::string&);
BOTAN_DLL length_type keylength_multiple_of(const std::string&);

}

#endif
