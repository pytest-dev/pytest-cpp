from setuptools import setup


setup(
    name="pytest-cpp",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=['pytest_cpp'],
    entry_points={
        'pytest11': ['cpp = pytest_cpp.plugin'],
    },
    install_requires=['pytest', 'colorama'],

    # metadata for upload to PyPI
    author="Bruno Oliveira",
    author_email="nicoddemus@gmail.com",
    description="Use pytest's runner to discover and execute C++ tests",
    long_description=open('README.rst').read(),
    license="MIT",
    keywords="pytest test unittest",
    url="http://github.com/pytest-dev/pytest-cpp",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: C++',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
)
