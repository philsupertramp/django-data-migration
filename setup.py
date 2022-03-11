import os

from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django-data-migrations',
    version=os.getenv('VERSION'),
    packages=['data_migration'],
    author='Philipp Zettl',
    author_email='philipp.zett@godesteem.de',
    include_package_data=True,
    description='Extraction tool for data only django migrations',
    keywords='django,database migrations',
    url='https://github.com/philsupertramp/django-data-migration/',
    license='MIT',
    install_requires=[
        'django >= 2.2'
    ],
    long_description=read('README.rst'),
    long_description_content_type='text/x-rst',
    classifiers=[
        # 3 - Alpha
        # 4 - Beta
        # 5 - Production/Stable
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 2.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content"
    ]
)
