# studious-fortnight

This repo helps tech writers at Red Hat get up and running with Vale. It serves as the starting point for our Vale Community of Practice.

## How do you use Vale?

As a technical writer, you can use Vale as a command-line tool to check your content files for style issues. For example:

```
[rdlugyhe@rdlugyhe ~]$ cd openshift-docs/logging/troubleshooting/
[rdlugyhe@rdlugyhe troubleshooting]$ vale cluster-logging-troubleshooting-for-critical-alerts.adoc
```

The output from the `vale` command output generates a list of suggestions, warnings, and errors based on customizable  of styles and vocabularies. For example:

<pre> 238:27   <font color="#CC0000">error</font>       Did you really mean             Vale.Spelling       
                      &apos;rebalancing&apos;?                                      
 244:6    <font color="#3465A4">suggestion</font>  Verify your use of &apos;there       IBM.Usage           
                      are&apos; with the word usage                            
                      guidelines.                                         
 244:38   <font color="#C4A000">warning</font>     Consider using &apos;available&apos;      CheDocs.CommonTerms
                      instead of &apos;present&apos;</pre>

You can review the output, decide which issues are valid, and update your content file accordingly.

To reduce false positives for yourself and your team, you can update the style and vocabulary files Vale uses. For example, I confirmed that "rebalancing" is a valid word in my docs and added it to my vocabulary file. Later, I'll create a PR to update the repo and share my updated vocabulary file with everyone else.

## About this repo

As a technical writer at Red Hat, you can use this repo to help you get started with using Vale.

Aside content like this topic, the repo contains the following items:

* A `.vale` directory that contains a collection of _styles_. These styles are based on the style guides that the Red Hat CCS organization uses. Members of _Eclipse Che documentation project_ team have been refining and using these styles for over a year.

* A `.vale.ini` configuration file for Vale that tells it where to find the `.vale` directory, and other important settings.

## Getting started using Vale and the `red-hat` style

1. For Linux and Mac I recommend [installing Homebrew](https://brew.sh/).

1. [Install the Vale command line tool on your workstation](https://docs.errata.ai/vale/install).

  NOTE: On the Vale site, click the tab for your operating system.

1. Use `git clone` to copy this repo, studious-fortnight, to your local machine. For example:
```
$ cd ~
$ git clone git@github.com:rolfedh/studious-fortnight.git
```

1. Copy the `.vale.ini` file and `.vale` directory from the `studious-fortnight` directory to the directory where you keep your documentation projects.

  For example:
  ```
  $ cp -r ./studious-fortnight/.vale* ./
  ```

1. Run the `vale` command on one of your content files. For example:
```
$ cd openshift-docs
$ vale modules/<filename>.adoc
```

1. Review the vale output and use some of it update your content file.

1. Re-run the same `vale` command to see the new results.

Caveat: The styles are not perfect and not complete. Don't be discouraged by the output from vale. Simply review the output and choose what's useful to you. We're working on making them better.

<!-- ## Optional: Eliminating false positives

1. Run the `vale` command on multiple content files by using a wildcard character `*`. For example:
```bash
$ vale modules/cluster-logging-exported*.adoc
```

2. Review the output for `Vale.Spelling` errors for valid words, such as words that appear in the product.

5. Add those valid words to `~/.vale/styles/Vocab/Che/accept.txt`. -->

## The benefits of using Vale

How does Vale help you improve your content quality and productivity?

* It helps you fix style issues right away, before you create a PR.
* It improves peer reviews.
* It makes content more consistent.
* It makes content easier to localize.
* It makes content is easier to for users to understand.

## Vale styles and rules

* A _style_ is a simple directory that contains a collection of rules.
* A _rule_ is a `.yml` file that defines the issue, the solution, and other information.
* You can use a style as-is, or you customize the rules it contains to fit your needs.
* This repo includes
<!-- * A _vocabulary_ is a simple directory that contains a collection of rules about your organization's -->

## Optional next steps

* [Install VS Code](https://code.visualstudio.com/docs/?dv=linux64_rpm) and the [Vale plugin for VS Code](https://marketplace.visualstudio.com/items?itemName=errata-ai.vale-server).
* [Add Vale to your docs continuous integration (CI) service](https://docs.errata.ai/vale/install#using-vale-with-a-continuous-integration-ci-service).
* [Add Vale to your GitHub actions](https://github.com/errata-ai/vale-action).

## Related topics

* [Troubleshooting common errors](troubleshooting-common-errors.md).
* [Blog posts for Studious-Fortnight](vale-at-red-hat-blog.md)
* [Rolfe's "Vale notes" blog posts](https://rolfe.blog/category/vale/)

## How to get involved, get help, and contribute

* Join the Slack channel, [#vale-at-red-hat](https://coreos.slack.com/archives/C0218RXJK5E), in the CoreOS workspace.
* To report a bug _in this repo_ or request an enhancement, please mention it here: https://github.com/rolfedh/studious-fortnight/issues.
* To show appreciation and support for Joseph Kato's work on Vale, please consider making a donation: https://docs.errata.ai/vale/about#sponsors
