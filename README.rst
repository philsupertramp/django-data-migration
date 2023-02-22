django-data-migration
=====================

|Test dev branch|
|Pypi|

| Developing and maintaining a django project over many years can start to become a constant fight against time consuming tasks including execution of a test suite, recreation of a local environment or setting up a project in a new environment.

| Due to different flavors of deployment and/or different approaches within the same working environment migration files of long running django applications tent to be bloated and contain unnecessary code. Sometimes we even create migrations in the purpose of single-time usage to move, edit, duplicate or basically modify data.

| Generally speaking, the idea behind it is clever.

| With this approach you gained the option to trigger the execution of leaf migrations prior to starting your updated application code.

.. code:: text

           Missing migration?
           /                \
     yes, migrate        no, continue
           \                /
        restart app with new code

| But on the other hand you create a new node within a already giant migration graph.
| This is where ``django-data-migration`` comes in place. It is a drop-in replacement for regular migrations, without the need of a dedicated node in the migration tree.
| It does that, by providing a "data-only" migration graph, that can optionally be maintained automatically in parallel with the existing migration graph, or executed independently, depending on your needs.

Installation
============

Install package:

| ``pip install django-data-migrations``

| Configure package in Django settings:

.. code:: python

    INSTALLED_APPS = [
        # django apps
        'data_migration',
        # your apps
    ]

Configuration
=============

| The package is configurable using the

.. code:: python

    DATA_MIGRATION = {}

setting.

Currently supported attributes:

- ``SQUASHABLE_APPS``: a list of app(-label) names which allow squashing, you should only provide your own apps here


Usage
=====

Extended management commands:
- ``makemigrations``
- ``migrate``
- ``squashmigrations``
- ``data_migrate``

``makemigrations``
~~~~~~~~~~~~~~~~~~

.. code:: shell

    # generate data migration file
    ./manage.py makemigrations --data-only [app_name]

    # generate data migration file with readable name "name_change"
    ./manage.py makemigrations --data-only [app_name] name_change

    # generate empty file
    ./manage.py makemigrations --data-only [app_name] --empty

    # generate without fileheader
    ./manage.py makemigrations --data-only [app_name] --no-header

The ``makemigrations`` command generates a file
``[app_name]/data_migrations/[id]_[name].py`` with content like

.. code:: python

    class Node:
        name = '0001_first'
        dependencies = ()
        migration_dependencies = ('testapp.0001_initial', )
        routines = [
        ]

``migrate``
~~~~~~~~~~~

.. code:: shell

    # apply data migration file
    ./manage.py migrate --data-only

    # revert complete data migration state
    ./manage.py migrate --data-only zero

    # revert partial data migration state
    ./manage.py migrate --data-only 0002_some_big_change



``squashmigrations``
~~~~~~~~~~~~~~~~~~~~

| App-wise squashing of data/regular migrations.

.. code:: shell

    # regular squashing of test_app migrations 0001-0015
    ./manage.py squashmigrations test_app 0001 0015

    # squash and replace test_app migrations 0001-0015 and extract data_migrations
    ./manage.py squashmigrations --extract-data-migrations test_app 0001 0015

``data_migrate``
~~~~~~~~~~~~~~~~

| Extended squashing. Allows squashing a single app, a list of apps, or all apps at once.

.. code:: shell

    # squash and replace all migrations at once
    ./manage.py data_migrate --all

    # squash and replace migrations app-wise
    ./manage.py data_migrate test_app


Development
===========

To develop the package further set up a local environment using the
provided ``./dev-requirements.txt`` file.

To run the test suite and generate a coverage report run

.. code:: shell

    coverage run -m pytest -v tests
    coverage [html|report]

.. |Test dev branch| image:: https://github.com/philsupertramp/django-data-migration/actions/workflows/test-dev.yml/badge.svg?branch=dev
   :target: https://github.com/philsupertramp/django-data-migration/actions/workflows/test-dev.yml

.. |Pypi| image:: https://badge.fury.io/py/django-data-migrations.svg
    :target: https://badge.fury.io/py/django-data-migrations
