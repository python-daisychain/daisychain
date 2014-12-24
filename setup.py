try:
    from setuptools import setup, find_packages
except:
    from distutils.core import setup, find_packages

setup(
    name='daisy',
    version='0.1',
    description='Configuration-based OO-dependency resolution workflow engine',
    author='Jeff Edwards',
    author_email='jeff@edwardsj.com'
    url='https://github.com/python-daisy/daisy',
    license='MIT License',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    scripts = ['bin/daisy-run']
)

