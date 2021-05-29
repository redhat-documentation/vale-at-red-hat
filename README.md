# studious-fortnight

This repo helps tech writers at Red Hat get up and running with Vale. It serves as the starting point for the Vale Community of Practice at Red Hat.

## What does using Vale look like?

As a technical writer, you typically run `vale` on the command-line against a content file:

```
[rdlugyhe@rdlugyhe ~]$ cd openshift-docs/logging/troubleshooting/
[rdlugyhe@rdlugyhe troubleshooting]$ vale cluster-logging-troubleshooting-for-critical-alerts.adoc
```

The command output gives you a list of suggestions, warnings, and errors based on customizable styles and vocabularies.

Here's what some typical command output looks like (minus colored syntax highlighting- which I can't reproduce here):

<pre> 238:27   <font color="#CC0000">error</font>       Did you really mean             Vale.Spelling       
                      &apos;rebalancing&apos;?                                      
 244:6    <font color="#3465A4">suggestion</font>  Verify your use of &apos;there       IBM.Usage           
                      are&apos; with the word usage                            
                      guidelines.                                         
 244:38   <font color="#C4A000">warning</font>     Consider using &apos;available&apos;      CheDocs.CommonTerms
                      instead of &apos;present&apos;</pre>


Where:
* The first column of the output gives the line and column number of the issue. `238:27` means line `238` contains an issue strating at character `27`
* The second column of the output gives the type of issue, `error`, `suggestion`, or `warning`.
* The third column gives you the style prompt.
* The fourth column gives you the source of the rule.

As a writer, you review output, decide which issues are valid, and update your content file accordingly.

You might ask: "What if you don't like the command output shown above?"

That's good! It means you're thinking critically about the Vale style can help make them better, which brings us to...

## How can you contribute to this project?

![Open Source Wants You](./images/open-source-wants-you-39-percent.jpg)

We need contributors like you to help improve and expand upon the Vale style rules we use at Red Hat.

To become a contributor, check out this [contributor's guide](contributors-guide.md)

## What are the important parts of this repo?

* The `.vale` directory contains a collection of _styles_, which are collections of rules that are based on the style guides we use at Red Hat. Members of _Eclipse Che documentation project_ team have been refining and using these styles for over a year.

* The `.vale.ini` configuration file that tells Vale where to find the `.vale` directory and other important settings.

## How do you get started?

1. For Linux and Mac I suggest [installing the Homebrew package manager](https://brew.sh/). It makes installing and updating software like Vale easier. (I'll also mention how to install Vale without using homebrew later on.)

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
* To report a bug _in this repo_ or request an enhancement, [create an issue](https://github.com/rolfedh/studious-fortnight/issues).
* To show appreciation and support for Joseph Kato's work on Vale, consider [making a donation](https://docs.errata.ai/vale/about#sponsors).
