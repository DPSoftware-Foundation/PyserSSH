from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='PyserSSH',
    version='4.0',
    license='MIT',
    author='damp11113',
    author_email='damp51252@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/damp11113/PyserSSH',
    description="A easy ssh server",
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        "paramiko"
    ]
)