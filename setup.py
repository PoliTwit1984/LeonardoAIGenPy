from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="LeonardoAIGenPy",
    version="0.1.4",
    author="Joe Wilson",
    author_email="joe.wilson@live.com",
    description="A Python package for interacting with Leonardo AI for image generation and upscaling.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Politwit1984/LeonardoAIGenPy",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests",
    ],
    package_data={
        "": ["templates.json"],
    },
    include_package_data=True,
)
