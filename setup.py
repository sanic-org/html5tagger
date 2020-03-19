from setuptools import setup, find_packages

setup(
    name="html5tagger",
    author="L. Kärkkäinen",
    author_email="tronic@noreply.users.github.com",
    description="Pythonic HTML5 generation without templating",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Tronic/html5tagger",
    packages=find_packages(),
    keywords=["HTML", "HTML5", "templating", "Jinja"],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Text Processing :: Markup :: HTML",
        "License :: OSI Approved :: MIT License",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
    python_requires = ">=3.6",
    use_scm_version=True,
    setup_requires = ["setuptools_scm"],
    install_requires = [],
    include_package_data = True,
)
