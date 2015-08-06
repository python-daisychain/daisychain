try:
    from setuptools import setup, find_packages
except:
    from distutils.core import setup, find_packages

install_requires = ['py3compat >= 0.2']

setup(
    name='daisychain',
    version='0.1.2',
    description='Configuration-based OO-dependency resolution workflow engine',
    author='Jeff Edwards',
    author_email='jeff@edwardsj.com',
    url='https://github.com/python-daisychain/daisychain',
    license='MIT License',
    packages=find_packages(exclude=["*.test", "*.test.*", "test.*", "test"]),
    scripts = ['bin/daisy-chain'],
    install_requires=install_requires
)
