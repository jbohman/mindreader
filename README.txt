Mindreader README
==================

Getting Started
---------------

- Install PostgreSQL + PostGIS 2.x
  - http://trac.osgeo.org/postgis/wiki/UsersWikiPostGIS20Debian70src

- Install GeoAlchemy 2.x and SQLAlchemy 8.x (both not in PYPI yet)
  - http://geoalchemy-2.readthedocs.org/en/latest/
  - http://hg.sqlalchemy.org/sqlalchemy

- cd <directory containing this file>

- $venv/bin/python setup.py develop

- cp development.ini.default development.ini

- Edit sqlalchemy.url to use your postgresql database

- $venv/bin/initialize_Mindreader_db development.ini

- $venv/bin/pserve development.ini
