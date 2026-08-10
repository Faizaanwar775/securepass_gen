from setuptools import find_packages, setup

setup(
    name="securepass-gen",
    version="1.0.0",
    description="A terminal-based password generator built entirely on the Python standard library.",
    long_description_content_type="text/markdown",
    author="Khizex Python Engineering Internship -- Week 6",
    python_requires=">=3.10",
    packages=find_packages(exclude=["tests", "tests.*"]),
    entry_points={
        "console_scripts": [
            "securepass-gen=securepass.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
)
