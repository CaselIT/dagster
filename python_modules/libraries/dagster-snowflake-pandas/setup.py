from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_snowflake_pandas/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()

# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-snowflake-pandas",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for integrating Snowflake and Pandas with Dagster.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-snowflake-pandas",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_snowflake_pandas_tests*"]),
    python_requires=">=3.8,<3.13",
    install_requires=[
        "dagster==1.6.14",
        "dagster-snowflake==0.22.14",
        "pandas",
        "requests",
        "snowflake-connector-python[pandas]>=3.4.0",
        "sqlalchemy!=1.4.42",  # workaround for https://github.com/snowflakedb/snowflake-sqlalchemy/issues/350
        "snowflake-sqlalchemy>=1.2",
    ],
    zip_safe=False,
)
