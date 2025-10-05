from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="github-sentinel",
    version="1.0.0",
    author="GitHub Sentinel Team",
    author_email="admin@github-sentinel.com",
    description="开源工具类AI Agent，自动监控GitHub仓库更新",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/github-sentinel",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "github-sentinel=src.main:main",
            "gs-cli=src.cli.commands:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["config/*.yaml"],
    },
)
