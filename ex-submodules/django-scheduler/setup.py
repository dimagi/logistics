from setuptools import setup, find_packages


setup(
    name="scheduler",
    version="0.0.1",
    license="BSD",

    install_requires = [
        "django",
        "django-celery",
        "dimagi-utils",
    ],

    packages = find_packages(exclude=['*.pyc']),
    include_package_data=True,

    author="Rowena Luk, Cory Zue",
    author_email="information@dimagi.com",

    description="Database backed scheduler for Django",
    url="http://github.com/dimagi/django-scheduler"
)
