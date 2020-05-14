from dataclasses import dataclass
import json
from typing import Any, Dict, List

import click
import requests


@dataclass
class Slack:
    ctx: click.Context
    webhook_url: str

    def report_results(self, results):
        obj = self.ctx.obj
        if not self.webhook_url:
            return

        click.echo("== sending slack notifications if needed")

        notify_reason = None
        if results.exit_code == 2:
            notify_reason = "found issues"
        elif results.exit_code != 0:
            notify_reason = "encountered an error"

        if not notify_reason:
            click.echo("not sending a notification, there's nothing to notify about",)
            return

        payload = {
            "text": f"Semgrep Action {notify_reason} during a scan on {obj.meta.repo_name}",
            "blocks": self.generate_message(notify_reason, obj.meta),
            "icon_emoji": ":mag_right:",
            "username": "Semgrep",
        }
        try:
            response = requests.post(
                self.webhook_url, data={"payload": json.dumps(payload)}, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException:
            click.echo(f"Slack returned this error: {response.text}", err=True)

    @staticmethod
    def generate_message(notify_reason: str, meta) -> List[Dict[str, Any]]:
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":point_right: Semgrep Action {notify_reason} during *<{meta.ci_url}|a scan on {meta.repo_name}>*",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repo:*\n<{meta.repo_url}|{meta.repo_name}>",
                    },
                    {"type": "mrkdwn", "text": f"*Triggered by:*\n{meta.ci_actor}",},
                    {
                        "type": "mrkdwn",
                        "text": f"*Scanned git ref:*\n`{meta.repo_ref}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Scanned git SHA:*\n`{meta.repo_sha[:8]}`",
                    },
                ],
            },
        ]