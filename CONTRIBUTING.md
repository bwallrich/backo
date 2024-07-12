# Contributing to ctricto

Help wanted! We'd love your contributions to backo. Please review the following guidelines before contributing. Also, feel free to propose changes to these guidelines by updating this file and submitting a pull request.

- [I have a question...](#questions)
- [I found a bug...](#bugs)
- [I have a feature request...](#features)
- [I have a contribution to share...](#process)

## <a id="questions"></a> Have a Question?

Please don't open a GitHub issue for questions about how to use `backo`, as the goal is to use issues for managing bugs and feature requests. Issues that are related to general support will be closed and redirected to our gitter room.

For all support related questions, please use [discussions](https://github.com/bwallrich/backo/discussions).

## <a id="bugs"></a> Found a Bug?

If you've identified a bug in `backo`, please [submit an issue](#issue) to our GitHub repo: [bwallrich/backo](https://github.com/bwallrich/backo/issues/new). Please also feel free to submit a [Pull Request](#pr) with a fix for the bug!

## <a id="features"></a> Have a Feature Request?

All feature requests should start with [submitting an issue](#issue) documenting the user story and acceptance criteria. Again, feel free to submit a [Pull Request](#pr) with a proposed implementation of the feature.

If you are not sure, go to [discussions](https://github.com/bwallrich/backo/discussions)

## <a id="process"></a> Ready to Contribute

### <a id="issue"></a> Create an issue

Before submitting a new issue, please search the issues to make sure there isn't a similar issue doesn't already exist.

Assuming no existing issues exist, please ensure you include required information when submitting the issue to ensure we can quickly reproduce your issue.

We may have additional questions and will communicate through the GitHub issue, so please respond back to our questions to help reproduce and resolve the issue as quickly as possible.

New issues can be created with in our [GitHub repo](https://github.com/bwallrich/backo/issues/new).

### <a id="pr"></a>Pull Requests

Pull requests should target the `master` branch. Please also reference the issue from the description of the pull request using [special keyword syntax](https://help.github.com/articles/closing-issues-via-commit-messages/) to auto close the issue when the PR is merged. For example, include the phrase `fixes #14` in the PR description to have issue #14 auto close.

### <a id="style"></a> Styleguide

When submitting code, please make every effort to follow existing conventions and style in order to keep the code as readable as possible. Here are only one point to keep it mind : [pylint](https://pypi.org/project/pylint/) is strict in ci-cd. Your code must be compliant 100% to it (otherwise your push/pull will be rejected).

Please use **sparingly**

```python
# pylint: disable something...
```

### License

By contributing your code, you agree to license your contribution under the terms of the [MIT License](https://github.com/bwallrich/backo/blob/main/LICENSE).

All files are released with this licence.
