from setuptools import setup, find_packages

setup(
    name='PyserSSH',
    version='5.1.3',
    license='MIT',
    author='DPSoftware Foundation',
    author_email='contact@damp11113.xyz',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/damp11113/PyserSSH',
    description="python scriptable ssh server library. based on Paramiko",
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    keywords="SSH server",
    python_requires='>=3.6',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Topic :: Software Development",
        "Topic :: Terminals"
    ],
    install_requires=[
        "paramiko",
        "psutil"
    ],
    extras_require={
        'RemoDesk': [
            "mouse",
            "keyboard",
            "Brotli",
            "pillow",
            "numpy",
            "opencv-python"
        ],
    }
)