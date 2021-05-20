.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

We have a `code of conduct<code-of-conduct.md>`_, so please follow it in all your interactions with the project.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/opendatacube/datacube-ows/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

datacube-ows could always use more documentation, whether as part of the
official datacube-ows docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/opendatacube/datacube-ows/issues .

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

1. Fork the `datacube-ows` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/datacube-ows.git

3. Follow the instructions in `README.rst<https://datacube-ows.readthedocs.io/en/latest/readme.html>`_  to build a working python environment.

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the tests, including testing other Python versions with tox::

    $ flake8 datacube-ows tests
    $ python setup.py test or py.test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests (and should pass them - and all pre-existing tests!)
2. If the pull request adds or modifies functionality, the docs should be updated.
3. The pull request should work for Python 3.7+. Check the results of
   the github actions and make sure that your PR passes all checks and
   does not decrease test coverage.

Links
-----

In case you haven't found them yet, please checkout the following resources:

* `Documentation <https://datacube-ows.readthedocs.io/en/latest>`_
* `Slack <http://slack.opendatacube.org>`_
