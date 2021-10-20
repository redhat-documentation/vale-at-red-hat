# Vale at Red Hat Blog
<!-- vale off -->
## 21. May, 14:12, Friday

[Rolfe] Here are my updates on studious-fortnight.

**Goal**: To make studious-fortnight become a "Vale at Red Hat" repository worth moving over to the Red Hat doc tools repository.

**What I've done recently**:
- I updated the studious' with the Vale style from the Che eclipse documentation project that Yana and Fabrice developed.
- I've been welcoming new team members to this channel.
- I hosted the "Friday 15 for Vale" at Red Hat.
- I added a GitHub Action to studious' that runs Vale against any modified files. (Check it out [here under the Actions tab](https://github.com/rolfedh/studious-fortnight/actions).

**What I'm doing next**:
- Running the studious' Vale style against some of my product docs.
- Refining the style rules and vocabulary to reduce false positives.
- Adding a "project"  topic to studious'.
- Reviewing the GitHub Action I added.
- Refining the README.md content.
- Set up studious' permissions for contributors and add a `contributors.md` topic.

**Any needs or blockers**?
- I'd appreciate your notes on getting started with Vale and studious'.  Feel free to discuss them here and open issues and enhancement requests on https://github.com/rolfedh/studious-fortnight/issues
- Become a contributor to studious, particularly its styles.

## 19. May, 7:37 AM, Wednesday

Today, I added a _GitHub action_ to run Vale against this repository. The action consists of a `.github/workflows/main.yml` file. Currently, the action is configured to check new and modified files, not all files in this repository. To see the actions, look at this repository in GitHub and click the Actions tab.


## 16. May, 1:22 PM, Sunday

Rolfe: This weekend, I merged many updates into the studious-fortnight repository. These included:
- Removing the previous `/styles` folder and `.vale.ini` file.
- Adding the `.vale` styles folder and `.vale.ini` that Fabrice and Yana developed for the Che eclipse documentation project.
- Updating and expanding `README.md` with new information to help you get started with using Vale.
- Adding a "Troubleshooting common errors" topic to help newcomers identify and correct common issues.

I'm also adding this blog page.
