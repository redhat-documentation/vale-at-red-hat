# studious-fortnight
Vale config files, styles, and docs to help individuals and teams at \<organization\> roll out Vale.

## A brief intro to Vale, styles, and rules

* [Vale is a syntax-aware linter for prose.](https://github.com/errata-ai/vale)
* [The Vale project provides a collection of optional and useful _styles_](https://github.com/errata-ai/styles), including:
  * [Microsoft](https://github.com/errata-ai/Microsoft) - An implementation of the [Microsoft Writing Style Guide](https://docs.microsoft.com/en-us/style-guide/welcome/).
  * [Google](https://github.com/errata-ai/Google) - An implementation of the [Google Developer Documentation Style Guide](https://developers.google.com/style/). 
* Each style is a collection of _rules_. And each rule is defined by a single `.yml` file.
* You can customize rules and styles to meet your needs, or create new ones.

[comment]: <> (Do not expand this section. Expect users to go read existing docs elsewhere.)

Benefits:
* Vale helps you write better content that is easier for readers to understand and localization teams to translate. 
* It helps teams write more consistent content. 
* It gives you immediate feedback, so you can fix-as-you-go.
* It reduces delays and wasted effort in reviews.

## What to do

* [Install Vale on your workstation or use the Docker image](https://docs.errata.ai/vale/install).
* Optional, but recommended: [Use Vale with your continuous integration (CI) service](https://docs.errata.ai/vale/install#using-vale-with-a-continuous-integration-ci-service)