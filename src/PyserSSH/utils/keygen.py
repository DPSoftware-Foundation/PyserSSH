import paramiko

def generate_ssh_keypair(private_key_path='id_rsa', public_key_path='id_rsa.pub', key_size=2048):
    """
    Generates an SSH key pair (private and public) and saves them to specified files.

    Args:
    - private_key_path (str): Path to save the private key.
    - public_key_path (str): Path to save the public key.
    - key_size (int): Size of the RSA key (default is 2048).
    """
    # Generate RSA key pair
    private_key = paramiko.RSAKey.generate(key_size)

    # Save the private key to a file
    private_key.write_private_key_file(private_key_path)

    # Save the public key to a file
    with open(public_key_path, 'w') as pub_file:
        pub_file.write(f"{private_key.get_name()} {private_key.get_base64()}")

    print(f"SSH Key pair generated: {private_key_path} and {public_key_path}")
