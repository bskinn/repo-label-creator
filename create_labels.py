import argparse as ap
import json
import os
from pathlib import Path

import requests as rq

DEFAULT_LABELS = [
    "bug",
    "documentation",
    "duplicate",
    "enhancement",
    "good first issue",
    "help wanted",
    "invalid",
    "question",
    "wontfix",
]

PRS_REPO = "repo"
PRS_DEL_DEFAULT = "delete_default"
PRS_DEL_ONLY = "delete_only"


def get_args():
    prs = ap.ArgumentParser(
        description="Utility to auto-apply a standard set of GitHub issue labels"
    )

    prs.add_argument(
        PRS_REPO,
        help="owner/repo to apply labels to, as '<owner>/<repo>'",
    )

    meg_delete = prs.add_mutually_exclusive_group()
    meg_delete.add_argument(
        "--delete-default",
        help="Also delete the GitHub-default labels, if they exist",
        action="store_true",
        dest=PRS_DEL_DEFAULT,
    )
    meg_delete.add_argument(
        "--delete-only",
        help="Delete any default GitHub labels without adding new ones",
        action="store_true",
        dest=PRS_DEL_ONLY,
    )

    return vars(prs.parse_args())


def main():
    args = get_args()

    repo = args[PRS_REPO]

    gh_token = os.environ.get("GITHUB_PAT")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {gh_token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    api_url_base = f"https://api.github.com/repos/{repo}/labels"

    # Cosmetic
    print("")

    # Removing the old labels
    if args[PRS_DEL_DEFAULT] or args[PRS_DEL_ONLY]:
        print("Removing GitHub default labels...\n")
        for default_label in DEFAULT_LABELS:
            del_resp = rq.delete(
                api_url_base + f"/{default_label}", headers=headers, timeout=30
            )

            print(
                f"Default label '{default_label}' result: {del_resp.status_code} ({del_resp.reason}) ({'deleted' if del_resp.ok else 'not found'})"  # noqa: E501
            )

        # Cosmetic
        print("")

    # Adding the new labels
    if not args[PRS_DEL_ONLY]:
        print("Adding the new labels...\n")
        labelsets = json.loads(Path("labels.json").read_text(encoding="utf-8"))[
            "groups"
        ]

        for labelset in labelsets:
            set_name = labelset["name"]
            color = labelset["color"]
            labels = labelset["labels"]

            for label in labels:
                label_name = f"{set_name}: {label['name']} :{label['icon']}:"

                get_resp = rq.get(
                    api_url_base + f"/{label_name}", headers=headers, timeout=30
                )

                if get_resp.ok:
                    # Label found, so let's update in place, but only if
                    # we need to. We know the name isn't changing, so
                    # we only need to check the color and description
                    if (gr_json := get_resp.json())["description"] == label.get(
                        "text", ""
                    ) and gr_json["color"] == color:
                        resp = get_resp
                        action = "unchanged"
                    else:
                        resp = rq.patch(
                            api_url_base + f"/{label_name}",
                            headers=headers,
                            data=json.dumps(
                                {
                                    "new_name": label_name,
                                    "description": f"{label.get('text', '')}",
                                    "color": color,
                                }
                            ),
                            timeout=30,
                        )
                        action = "updated"
                else:
                    # Not found, let's create
                    resp = rq.post(
                        api_url_base,
                        headers=headers,
                        data=json.dumps(
                            {
                                "name": label_name,
                                "description": f"{label.get('text', '')}",
                                "color": color,
                            },
                        ),
                        timeout=30,
                    )
                    action = "created"

                print(
                    f"Label '{label_name}' result: {resp.status_code} ({resp.reason}) ({action})"  # noqa: E501
                )

    print("\n...Done.\n")


if __name__ == "__main__":
    main()
