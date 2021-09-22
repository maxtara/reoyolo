from setuptools import setup, find_packages

description='A tool for alerting to homeassistant, when yolo (opencv) determins something is seen on a reolink security camera. Might be a little besoke for anyone else to use' 
setup(
    name='reoyolo',
    version='0.0.1',
    description=description,
    long_description=description,
    url='https://github.com/maxtara/reoyolo',
    author='maxtara',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Home Automation',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='home automation reolink homeassistant yolo',
    packages=find_packages(),
    install_requires=[
        'requests',
        'flask',
        'numpy',
        'pyinotify'
    ], # IMPORTANT - opencv-python is not a requirement, but is needed. Install it yourself using pip or from source. it is MUCH faster from source with the right flags
    extras_require={'dev': ['pytest']},
    entry_points={},
)