from setuptools import find_packages, setup

setup(
    name='webserial_update',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pydantic',
        'fanficfare',
        'toml',
        'typer',
    ],
    entry_points = {
        'console_scripts': [
            'webserial_update=webserial_update.cli:app'
        ]
    }
)
