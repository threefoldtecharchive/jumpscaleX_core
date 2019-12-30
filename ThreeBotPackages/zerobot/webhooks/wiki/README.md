# webhooks

This package is used to expose webhooks at port 8530.

Currently there is only one webhook `/webhook/github` which updates the local repos when a commit is pushed.

To use this webhook, go to your repo on github, configure the webhook to point to webhook url. Make sure you configure a `secret` in your webhook on github, and copy this secret to `/sandbox/var/github_webhook_secret`.
