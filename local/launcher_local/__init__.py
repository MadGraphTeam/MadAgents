"""Local-model launcher — a deliberately separate entry point.

The main launcher (``src/launcher/``) strips every API key and endpoint-
redirection variable from the container environment, unconditionally, and
asserts they are gone right before it execs ``claude``. That guarantee is not
negotiable and is not weakened by anything in this package.

Running against a self-hosted endpoint is what this package is for, and how much
of that guarantee survives depends on the provider. On ``opencode`` (the default
here) all of it does: the endpoint and its key are declared in a generated
config file, so the assertion still runs. On ``claude_code`` it cannot —
``ANTHROPIC_BASE_URL`` (and usually ``ANTHROPIC_AUTH_TOKEN``) *must* reach the
session as variables, so the assertion is skipped on that path alone. Rather
than punch a hole in the main launcher, both cases live here as their own
launcher, with their own config file and entry script. The two paths share the
container machinery (image, overlay, binds, instance lifecycle) by importing it;
they do not share the auth policy.

Entry point: ``local/madrun.sh`` → ``python3 -m launcher_local run``.
"""
