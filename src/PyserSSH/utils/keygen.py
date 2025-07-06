"""
PyserSSH - A Scriptable SSH server. For more info visit https://github.com/DPSoftware-Foundation/PyserSSH
Copyright (C) 2023-present DPSoftware Foundation (MIT)

Visit https://github.com/DPSoftware-Foundation/PyserSSH

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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
