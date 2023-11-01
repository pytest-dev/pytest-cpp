Here are the steps on how to make a new release.

1. Create a ``release-VERSION`` branch from ``upstream/main``.
2. Update ``CHANGELOG.rst``.
3. Push the branch to ``upstream``.
4. Once all tests pass, start the ``deploy`` workflow manually, or execute::

       gh workflow run deploy.yml -r release-VERSION -f version=VERSION

5. Merge the PR.
