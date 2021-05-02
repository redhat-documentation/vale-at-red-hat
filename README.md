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

## Benefits of using Vale

Vale improves your content quality and productvity:
* Gives you feedback while you're writing, so you can fix-as-you-go.
* Helps you write content that's easier for readers to understand.
* Makes reviews faster and easier for writers and reviewers.
* Helps teams of writers produce content that is the the more consistent. 

## What to do

* [Install Vale on your workstation](https://docs.errata.ai/vale/install).
* Download this `.vale.ini` file to the root directory of your doc project or repo.
* Optional, but recommended: [Use Vale with your continuous integration (CI) service](https://docs.errata.ai/vale/install#using-vale-with-a-continuous-integration-ci-service)