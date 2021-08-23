from cryptography.fernet import Fernet

def load_key():
    """
    Load the previously generated key
    """
    return open("secret.key", "rb").read()

def decrypt_message(encrypted_message):
    """
    Decrypts an encrypted message
    """
    if not encrypted_message:
        return encrypted_message

    key = load_key()
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message)

    return decrypted_message.decode()
