from setuptools import find_packages, setup

setup(
    name='hashBaseStructs',
    version='0.1.0',
    description='Here you can find Python3 lib with different hash structs for CDC task.',
    author='Alex Glushko',
    author_email='aglushko@hse.ru',
    url='https://github.com/Badcat330/HashBaseStructs',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 1 - Planning"
    ],
    package_dir={"": "hashBaseStructs"},
    packages=find_packages(where="hashBaseStructs"),
    python_requires=">=3.9",
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)
