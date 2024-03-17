@echo off

title change urllib3 to 1.26.15
pip install urllib3==1.26.15

title building dist
python setup.py sdist

title uploading to pypi
twine upload -r pypi dist/*

pause