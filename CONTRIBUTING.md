# Contributing

When contributing to this project, please read the contribution rules first.

## Fixing an issue

### Workflow

This repository is using the **golden master** approach. So when making a contribution to the code, try to follow this workflow:
1.  Create a new remote branch to commit your changes. Do not commit on "master".
1.  Mention the issue number add a short description of your change in your commit messages: 
`#99 Fixed issue with foo bar`
1.  Add a description of your change and reference issue numbers under **Pending** in the [Changelog](CHANGES.md).
1.  Once you change is ready, create a MR (Merge Request) from your feature branch to the master branch.
1.  Fill in the template for the MR message and check all items in the checklist.
1.  Try to stick to "1 MR per issue".

### Test coverage

The project uses Pytest to validate new functionalities and fixed bugs, and prevent regressions. If no existing test 
covers your change, create a new test or modify an existing one.

### QA

*  Code has to conform to the Quality Rules defined in issue #10.
*  Code quality is tracked using SonarQube profiles.
*  Code security issues are scanned using [Bandit](https://pypi.org/project/bandit/).
*  Whitelisted security issues are tracked in issue #19, and stored in the 
[Bandit whitelisting file](test/bandit_whitelisting.json).


## Making a release

1.  Releases are marked by tags.
1.  To increase the version number at release, update the `__version__` field in the 
[__init__.py](netcdf_flattener/__init__.py) file. This centralized field is imported by the [package setup](setup.py) and 
[documentation](doc/conf.py).
1.  Replace **Pending** by the actual version number in the [Changelog](CHANGES.md).
