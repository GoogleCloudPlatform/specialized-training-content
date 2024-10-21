"""Using `setuptools` to create a source distribution."""

from setuptools import find_packages, setup

setup(
    name="fraud_trainer",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    description="Fraud detection model training application.",
)
