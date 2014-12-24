try:
    from setuptools import setup, find_packages
except:
    from distutils.core import setup, find_packages

install_requires = ['py3compat >= 0.2']

setup(
    name='daisychain',
    version='0.1',
    description='Configuration-based OO-dependency resolution workflow engine',
    author='Jeff Edwards',
    author_email='jeff@edwardsj.com',
    url='https://github.com/python-daisy/daisychain',
    license='MIT License',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    scripts = ['bin/daisy-chain'],
    install_requires=install_requires
)

