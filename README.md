# studious-fortnight

Vale is a command-line tool to help you find and fix style issues in your content files.

As a technical writer at Red Hat, you can use this repo to help you get started with using Vale.

The `.vale` directory in this repo includes a collection of rules, or _styles_. These styles are based on the style guides that the Red Hat CCS organization uses. Members of _Eclipse Che documentation project_ team have been refining and using these styles for over a year.

The repo also includes a `.vale.ini` file that configures Vale to use the `.vale` styles to check your `.adoc` and `.md` content files.

## Get started using Vale and the `red-hat` style

1. [Install the Vale command line tool on your workstation](https://docs.errata.ai/vale/install).
2. `git clone` this repo to your local machine.
3. Copy the `.vale.ini` file and `.vale` directory from the repo to the  directory where you keep your documentation projects.

  For example, if you keep documentation projects such as `/home/<username>/openshift-docs` in your home directory, copy `.vale.ini` and `.vale` to `/home/<username>/`

4. In a terminal, run the `vale` command on one of your content files. For example:
```bash
$ cd openshift-docs
$ vale modules/<filename>.adoc
```

## Benefits of using Vale

How does Vale help you improve your content quality and productivity?

* It helps you catch and fix style issues right away.
* It makes content is easier to understand and localize.
* It improves peer reviews.
* It makes content more consistent.

## Vale styles and rules

* A _style_ is a simple directory that contains a collection of rules.
* A _rule_ is a `.yml` file that defines the issue, the solution, and other information.
* You can use a style as-is, or you customize the rules it contains to fit your needs.
* This repo includes
// A _vocabulary_ is a simple directory that contains a collection of rules about your organization's

* You can download [various ready-to-use styles from Vale](https://github.com/errata-ai/styles), including ones based on the IBM, Google, and Microsoft style guides.

## Optional next steps

* [Install VS Code](https://code.visualstudio.com/docs/?dv=linux64_rpm) on your system, and install the [Vale plugin for VS Code](https://marketplace.visualstudio.com/items?itemName=errata-ai.vale-server).
* [Add Vale to your docs continuous integration (CI) service](https://docs.errata.ai/vale/install#using-vale-with-a-continuous-integration-ci-service).
* [Add Vale to your GitHub actions](https://github.com/errata-ai/vale-action).

## How to get involved, get help, and contribute

* See the [Troubleshooting common errors](troubleshooting-common-errors.md) topic.
* Join the Slack channel, [#vale-at-red-hat](https://coreos.slack.com/archives/C0218RXJK5E), in the CoreOS workspace.
* To report a bug _in this repo_ or request an enhancement, please mention it here: https://github.com/rolfedh/studious-fortnight/issues.
* To show appreciation and support for Joseph Kato's work on Vale, please consider making a donation: https://docs.errata.ai/vale/about#sponsors
