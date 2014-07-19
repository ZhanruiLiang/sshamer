from setuptools import setup

setup(
    name='sshammer',
    version='0.1',
    description='SSH Hammer for the Great Firewall',
    packages=['sshammer'],
    install_requires=[
        'pexpect',
    ],
    package_data={
        'sshammer': ['ssh_config'],
    },
)
