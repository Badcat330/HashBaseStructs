from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='hashBaseStructs',
    version='0.1.0',
    description='Here you can find Python3 lib with different hash structs for CDC task.',
    long_description=long_description,
    long_description_content_type="text/markdown",
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
    install_requires=['blake3'
                      # , 'tigerhash>=0.2.0'
                      ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)
