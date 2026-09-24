"""quilt-trace — visualize any substrate walker's witness chain."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="quilt-trace",
    version="0.1.0",
    description="The organism's eyes — visualize any substrate walker's witness chain",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/SuperInstance/quilt-trace",
    author="SuperInstance",
    license="Apache-2.0",
    python_requires=">=3.11",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.11",
    ],
)
