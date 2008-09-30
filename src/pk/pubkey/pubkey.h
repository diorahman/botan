/*************************************************
* Public Key Interface Header File               *
* (C) 1999-2007 Jack Lloyd                       *
*************************************************/

#ifndef BOTAN_PUBKEY_H__
#define BOTAN_PUBKEY_H__

#include <botan/base.h>
#include <botan/pk_keys.h>
#include <botan/pk_pad.h>

namespace Botan {

enum Signature_Format { IEEE_1363, DER_SEQUENCE };

/*************************************************
* Public Key Encryptor                           *
*************************************************/
class BOTAN_DLL PK_Encryptor
   {
   public:
      SecureVector<byte> encrypt(const byte[], length_type,
                                 RandomNumberGenerator&) const;
      SecureVector<byte> encrypt(const MemoryRegion<byte>&,
                                 RandomNumberGenerator&) const;

      virtual u32bit maximum_input_size() const = 0;
      virtual ~PK_Encryptor() {}
   private:
      virtual SecureVector<byte> enc(const byte[], length_type,
                                     RandomNumberGenerator&) const = 0;
   };

/*************************************************
* Public Key Decryptor                           *
*************************************************/
class BOTAN_DLL PK_Decryptor
   {
   public:
      SecureVector<byte> decrypt(const byte[], length_type) const;
      SecureVector<byte> decrypt(const MemoryRegion<byte>&) const;
      virtual ~PK_Decryptor() {}
   private:
      virtual SecureVector<byte> dec(const byte[], length_type) const = 0;
   };

/*************************************************
* Public Key Signer                              *
*************************************************/
class BOTAN_DLL PK_Signer
   {
   public:
      SecureVector<byte> sign_message(const byte[], length_type);
      SecureVector<byte> sign_message(const MemoryRegion<byte>&);

      void update(byte);
      void update(const byte[], length_type);
      void update(const MemoryRegion<byte>&);

      SecureVector<byte> signature(RandomNumberGenerator&);

      void set_output_format(Signature_Format);

      PK_Signer(const PK_Signing_Key&, const std::string&);
      ~PK_Signer() { delete emsa; }
   private:
      PK_Signer(const PK_Signer&);
      PK_Signer& operator=(const PK_Signer&);

      const PK_Signing_Key& key;
      Signature_Format sig_format;
      EMSA* emsa;
   };

/*************************************************
* Public Key Verifier                            *
*************************************************/
class BOTAN_DLL PK_Verifier
   {
   public:
      bool verify_message(const byte[], length_type, const byte[], length_type);
      bool verify_message(const MemoryRegion<byte>&,
                          const MemoryRegion<byte>&);

      void update(byte);
      void update(const byte[], length_type);
      void update(const MemoryRegion<byte>&);

      bool check_signature(const byte[], length_type);
      bool check_signature(const MemoryRegion<byte>&);

      void set_input_format(Signature_Format);

      PK_Verifier(const std::string&);
      virtual ~PK_Verifier();
   protected:
      virtual bool validate_signature(const MemoryRegion<byte>&,
                                      const byte[], length_type) = 0;
      virtual length_type key_message_parts() const = 0;
      virtual length_type key_message_part_size() const = 0;

      Signature_Format sig_format;
      EMSA* emsa;
   private:
      PK_Verifier(const PK_Verifier&);
      PK_Verifier& operator=(const PK_Verifier&);
   };

/*************************************************
* Key Agreement                                  *
*************************************************/
class BOTAN_DLL PK_Key_Agreement
   {
   public:
      SymmetricKey derive_key(length_type, const byte[], length_type,
                              const std::string& = "") const;
      SymmetricKey derive_key(length_type, const byte[], length_type,
                              const byte[], length_type) const;

      PK_Key_Agreement(const PK_Key_Agreement_Key&, const std::string&);
   private:
      PK_Key_Agreement(const PK_Key_Agreement_Key&);
      PK_Key_Agreement& operator=(const PK_Key_Agreement&);

      const PK_Key_Agreement_Key& key;
      const std::string kdf_name;
   };

/*************************************************
* Encryption with an MR algorithm and an EME     *
*************************************************/
class BOTAN_DLL PK_Encryptor_MR_with_EME : public PK_Encryptor
   {
   public:
      length_type maximum_input_size() const;

      PK_Encryptor_MR_with_EME(const PK_Encrypting_Key&, const std::string&);
      ~PK_Encryptor_MR_with_EME() { delete encoder; }

   private:
      PK_Encryptor_MR_with_EME(const PK_Encryptor_MR_with_EME&);
      PK_Encryptor_MR_with_EME& operator=(const PK_Encryptor_MR_with_EME&);

      SecureVector<byte> enc(const byte[], length_type,
                             RandomNumberGenerator& rng) const;

      const PK_Encrypting_Key& key;
      const EME* encoder;
   };

/*************************************************
* Decryption with an MR algorithm and an EME     *
*************************************************/
class BOTAN_DLL PK_Decryptor_MR_with_EME : public PK_Decryptor
   {
   public:
      PK_Decryptor_MR_with_EME(const PK_Decrypting_Key&, const std::string&);
      ~PK_Decryptor_MR_with_EME() { delete encoder; }
   private:
      PK_Decryptor_MR_with_EME(const PK_Decryptor_MR_with_EME&);
      PK_Decryptor_MR_with_EME& operator=(const PK_Decryptor_MR_with_EME&);

      SecureVector<byte> dec(const byte[], length_type) const;

      const PK_Decrypting_Key& key;
      const EME* encoder;
   };

/*************************************************
* Public Key Verifier with Message Recovery      *
*************************************************/
class BOTAN_DLL PK_Verifier_with_MR : public PK_Verifier
   {
   public:
      PK_Verifier_with_MR(const PK_Verifying_with_MR_Key&, const std::string&);
   private:
      PK_Verifier_with_MR(const PK_Verifying_with_MR_Key&);
      PK_Verifier_with_MR& operator=(const PK_Verifier_with_MR&);

      bool validate_signature(const MemoryRegion<byte>&, const byte[], length_type);
      length_type key_message_parts() const { return key.message_parts(); }
      length_type key_message_part_size() const { return key.message_part_size(); }

      const PK_Verifying_with_MR_Key& key;
   };

/*************************************************
* Public Key Verifier without Message Recovery   *
*************************************************/
class BOTAN_DLL PK_Verifier_wo_MR : public PK_Verifier
   {
   public:
      PK_Verifier_wo_MR(const PK_Verifying_wo_MR_Key&, const std::string&);
   private:
      PK_Verifier_wo_MR(const PK_Verifying_wo_MR_Key&);
      PK_Verifier_wo_MR& operator=(const PK_Verifier_wo_MR&);

      bool validate_signature(const MemoryRegion<byte>&, const byte[], length_type);
      length_type key_message_parts() const { return key.message_parts(); }
      length_type key_message_part_size() const { return key.message_part_size(); }

      const PK_Verifying_wo_MR_Key& key;
   };

}

#endif
