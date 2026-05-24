# repo-label-creator: Automatically create custom issue/PR labels in a GitHub repository

**Want a quick way to create a bunch of standard labels in a GitHub repo?**

**You want `repo-label-creator`!**

Get the labels you need in a few steps:

1. Configure a fine-grained GitHub personal access token with write permissions
   on at least one of Issues or Pull Requests & set it up in your terminal as
   the `GITHUB_PAT` environment variable.
2. Clone this repo.
3. Create a virtual environment (Python 3.11+), activate, and
   `python -m pip install -r requirements.txt`.
4. Edit `labels.json` to define the labels you want to create.
5. Run `python create_labels.py <owner>/<repo`

And done!

---

`repo-label-creator` created most of the [labels on its own repository][own labels].

If you want to curate your own set of preferred labels in `labels.json`, then
fork the repo first, edit `labels.json` to your liking, and push your changes to
your fork. If you'd like to be able to curate your own `labels.json` elsewhere
and point `repo-label-creator` at it, please say so at [#2].

For now, this code is not packaged for distribution on PyPI. If you'd like to be
able to pip install it, please say so at [#5].


## Motivation

### Background

GitHub's labeling features for issues and PRs are quite helpful for organizing
tickets. For projects of substantial size, though, a structured approach to
organizing and formatting the labels is important to maximize value and
usability.

While working on the [Quansight Labs website][labs site] I was exposed to
[Tania Allard]'s style of GitHub label management, and liked it a lot. Check out
the [labels in the Labs site repo][labs site labels] for an example.

My take on her approach boils down to these aspects:

- All labels should be sorted into a small number of broader, named categories.
  - E.g., `area`, `topic`, `type`
- Each label should include its category name as well as its own name.
  - This unambiguously associates the label with its category.
- All labels in each category should have the same color.
  - This facilitates rapid recognition of the category of the label.
  - When possible, colors should be chosen for maximum accessibility for those
    with color-blindness.
- Each label should have a unique emoji as part of its name.
  - This allows for quick recognition of specific, individual labels.
- Label names should nearly always be short. If additional explanation is
  needed, put it in the `description` field.
- Some categories will naturally tend to only have one label apply per ticket
  (e.g., `type`); others will naturally allow multiple labels per ticket (e.g.,
  `area`).
- In rare cases, a label may have a different color from the rest of its
  category, when special emphasis is called for.
  - A good example here is `pr: DO NOT MERGE ❌`, which one might color in bright
    red so that it stands out.
- In extremely rare cases, a label might not reside in any category.
  - I actually can't think of any examples of this offhand.

### Specific Categories

The categories that make sense to me at this time, and thus the ones included in
the built-in `labels.json` config, are:

- `area` - The general section of the project the ticket relates to. Broadly
  speaking, this maps _loosely_ to where in the repo that changes would be
  located.
- `docs` - For `area: docs` tickets, this specifies the type of documentation
  being discussed, sorted according to the [Diátaxis framework][diataxis].
- `issue` - Status labels specific to issue tickets, which generally point
  toward whether, when, and how action would be taken on the topic raised in the
  ticket.
  - There may be situations where an `issue` label gets applied to a pull
    request, such as where a contributor implements a code change to demonstrate
    a proposed fix as part of making a bug report or feature request. This
    'cross-application' helps to communicate that the PR is not serving the
    "pure" PR function of implementing a decided-upon change.
- `meta` - These are effectively commentary directed at the open source
  community with an interest in the project.
  - Whereas `issue` and `pr` labels are focused on communicating the status and
    posture of a ticket with respect to implementation in the _project_, `meta`
    labels are focused on communicating how the maintainers would like the
    _community_ to think about the ticket.
  - The default labels in this category, `meta: good first issue`,
    `meta: help wanted`, and `meta: yagni` help to illustrate its community
    focus.
- `pr` - Status labels specific to pull requests, highlighting actions that are
  still required on a PR before it is ready for merge; or, highlighting its
  merge-ready status.
- `topic` - This is the category that is most idiosyncratic to each project, and
  the most likely to cross-cut the other categories. They collect together
  tickets with a common topic/theme, assisting with quick searches on that
  theme.
  - When a `topic` label is applied to a sufficient number of tickets, it can be
    a signal that it might be time to create a milestone, a project, or some
    other heavier-weight organizational tool to manage those tickets.
- `type` - This category holds labels whose role is to sort tickets according to
  the overall nature of the change to the codebase/repository. Is it fixing a
  problem? Adding a feature? Performing maintenance, or refactoring code?
  - In nearly all cases, there should be _exactly one_ `type` label applied to a
    ticket.


These are far from the only label categories that one could define. For example,
for larger projects that curate multiple maintenance branches, categories like
`branch` and/or `needs backport` might be valuable. Each project would develop
its own categories and labels according to its needs.

### Motivation

I've rolled out a similar approach to the above to a handful of my repos,
and it's worked quite well for me. I have a much easier time choosing which
labels to apply to most tickets, since the categories are a natural
multi-dimensional 'coordinate system' in which to locate things.

One drawback to this approach, though, is how many labels you need to create
from the outset of a project in order to put the framework in place. And, as far
as I can tell, the GitHub UI doesn't provide any sort of bulk processing
mechanisms for labels... it's a one-at-a-time, manual process the whole way.

(There may already be tooling out there to do this initial label creation, but I
didn't find any on an initial search. I'd be delighted to learn of any; please
[open a new ticket] to clue me in.)

So, I took the time it would have taken me to manually create this initial label
set on a handful of repos, and instead wrote a thing that would apply them onto
any repo. And, here we are!


## Implementation

### Interface

At present, the tool operates as a standalone Python module, executed as
`python create_labels.py <repo owner>/<repo-name>`. A GitHub personal access
token with appropriate permissions must be defined in the terminal environment
in the `GITHUB_PAT` variable, and the script should be run using a virtual
environment that's had `python -m pip install -r requirements.txt` run inside
it.

The CLI is implemented with `argparse`, and offers a couple of configuration
flags centered around the deletion of the default labels that GitHub applies to
new repositories:

```
$ python create_labels.py -h
usage: create_labels.py [-h] [--delete-default | --delete-only] repo

Utility to auto-apply a standard set of GitHub issue labels

positional arguments:
  repo              owner/repo to apply labels to, as '<owner>/<repo>'

options:
  -h, --help        show this help message and exit
  --delete-default  Also delete the GitHub-default labels, if they exist
  --delete-only     Delete any default GitHub labels without adding new ones
```

As noted above, currently the `labels.json` file location is hardcoded. Comment
on [#2] if you'd like to be able to point to a different location.

### `labels.json` Schema

Expressed (approximately) as dataclasses, the schema for `labels.json` is:

```
@dataclass
class Label:
    icon: str
    name: str
    text: str | None

@dataclass
class Category:
    name: str
    color: str  # Must be 6-digit RGB hex without the leading '#'
    labels: list[Label]

@dataclass
class LabelsJSON:
   groups: list[Category]
```

### Internals

GitHub exposes an [API] for listing, retrieving, creating, updating, and
deleting labels from a repository. All interactions with the labels list of the
target repository are achieved using `requests` calls to this API.


[#2]: https://github.com/bskinn/repo-label-creator/issues/2
[#5]: https://github.com/bskinn/repo-label-creator/issues/5
[api]: https://docs.github.com/en/rest/issues/labels?apiVersion=2022-11-28#list-labels-for-a-repository
[diataxis]: https://diataxis.fr
[labs site]: https://labs.quansight.org
[labs site repo]: https://github.com/Quansight/Quansight-website
[labs site labels]: https://github.com/Quansight/Quansight-website/labels
[open a new ticket]: https://github.com/bskinn/repo-label-creator/issues/new
[own labels]: https://github.com/bskinn/repo-label-creator/labels
[Tania Allard]: https://github.com/trallard
