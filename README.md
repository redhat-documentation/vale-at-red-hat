# studious-fortnight

As a technical writer, you can use the Vale command-line tool to check your content files for style issues. For example:
```
[rdlugyhe@rdlugyhe ~]$ cd openshift-docs/logging/troubleshooting/
[rdlugyhe@rdlugyhe troubleshooting]$ vale cluster-logging-troubleshooting-for-critical-alerts.adoc
```
The vale command output generates a colorful list of suggestions, warnings, and errors for the file. For example:

<pre> 238:27   <font color="#CC0000">error</font>       Did you really mean             Vale.Spelling       
                      &apos;rebalancing&apos;?                                      
 244:6    <font color="#3465A4">suggestion</font>  Verify your use of &apos;there       IBM.Usage           
                      are&apos; with the word usage                            
                      guidelines.                                         
 244:38   <font color="#C4A000">warning</font>     Consider using &apos;available&apos;      CheDocs.CommonTerms
                      instead of &apos;present&apos;                                
 244:47   <font color="#3465A4">suggestion</font>  Verify your use of &apos;then&apos; with  IBM.Usage  </pre>
 
Vale is a command-line tool to help you find and fix style issues in your content files.

As a technical writer at Red Hat, you can use this repo to help you get started with using Vale.

The `.vale` directory in this repo includes a collection of rules, or _styles_. These styles are based on the style guides that the Red Hat CCS organization uses. Members of _Eclipse Che documentation project_ team have been refining and using these styles for over a year.

The repo also includes a `.vale.ini` file that configures Vale to use the `.vale` styles to check your `.adoc` and `.md` content files.

## Getting started using Vale and the `red-hat` style

1. [Install the Vale command line tool on your workstation](https://docs.errata.ai/vale/install).
2. `git clone` this repo to your local machine.
3. Copy the `.vale.ini` file and `.vale` directory from the repo to the  directory where you keep your documentation projects.

  For example, if you keep documentation projects such as `/home/<username>/openshift-docs` in your home directory, copy `.vale.ini` and `.vale` to `/home/<username>/`

4. In a terminal, run the `vale` command on one of your content files. For example:
```bash
$ cd openshift-docs
$ vale modules/<filename>.adoc
```
5. Fix some of the issues in the content file.

6. Re-run the same `vale` command to see the new results.

## Optional: Eliminating false positives

1. Run the `vale` command on multiple content files by using a wildcard character `*`. For example:
```bash
$ vale modules/cluster-logging-exported*.adoc
```

2. Review the output for `Vale.Spelling` errors for valid words, such as product, feature, or component names.

<!-- 3. In your terminal window, open a new tab.

4. Make a vocabulary folder for you product by copying the `Che` folder in the `.vale/styles/Vocab` directory. For example:
```bash
$ cd ~/.vale/styles/Vocab/
$ cp -r Che Logging
```
 -->

5. Add those valid words to `~/.vale/styles/Vocab/accept.txt`.

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
<!-- * A _vocabulary_ is a simple directory that contains a collection of rules about your organization's -->


## Optional next steps

* [Install VS Code](https://code.visualstudio.com/docs/?dv=linux64_rpm) on your system, and install the [Vale plugin for VS Code](https://marketplace.visualstudio.com/items?itemName=errata-ai.vale-server).
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
