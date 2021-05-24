import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'pyramid',
    'pyramid_jinja2',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'SQLAlchemy',
    'transaction',
    'pyramid_prometheus',
    'waitress',
    'pyramid_scheduler',
    'simplejson',
    'zope',
    'graypy',
    'stripe',
    'wheel', 'colander', 'deform',
    'zope_sqlalchemy',
    'requests',
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',  # includes virtualenv
    'pytest-cov',
]

setup(name='JIRAAnnouncer',
      version='0.0',
      description='JIRAAnnouncer',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      python_requires='>=3.6',
      author='Kenneth Aalberg',
      author_email='absolver@fuelrats.com',
      url='https://github.com/FuelRats/JIRAAnnouncer',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      extras_require={
          'testing': tests_require,
      },
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = jiraannouncer:main
      [console_scripts]
      initialize_JIRAAnnouncer_db = jiraannouncer.scripts.initializedb:main
      """,
      )
