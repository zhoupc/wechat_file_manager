from setuptools import setup, find_packages

setup(
    name="wechat-file-manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyyaml",
        "tqdm",
    ],
    package_data={
        "": ["config.yaml"],
    },
    entry_points={
        "console_scripts": [
            "wechat-file-manager=wechat_file_manager:main",
            "wfm=wechat_file_manager:main",  # Added shorter command
        ],
    },
    author="Pengcheng Zhou",
    description="A tool to manage and deduplicate WeChat files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/zhoupc/wechat_file_manager",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.6",
)