"""Setup for aioUnifi"""

# https://ubntwiki.com/products/software/unifi-controller/api
# https://jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/
# http://peterdowns.com/posts/first-time-with-pypi.html
# pip install -e .
# Upload to PyPI Live
# python setup.py sdist bdist_wheel
# twine upload dist/aiounifi-* --skip-existing

from setuptools import setup

setup(
    name='aiounifi',
    packages=['aiounifi'],
    version='9',
    description='An asynchronous Python library for communicating with Unifi Controller API',
    author='Robert Svensson',
    author_email='Kane610@users.noreply.github.com',
    license='MIT',
    url='https://github.com/Kane610/aiounifi',
    download_url='https://github.com/Kane610/aiounifi/archive/v9.tar.gz',
    install_requires=['aiohttp'],
    keywords=['unifi', 'homeassistant'],
    classifiers=[
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
)
