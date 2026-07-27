"""Local-model launcher — a deliberately separate entry point.

The main launcher (``src/launcher/``) strips every API key and endpoint-
redirection variable from the container environment, unconditionally, and
asserts they are gone right before it execs ``claude``. That guarantee is not
negotiable and is not weakened by anything in this package.

Running against a self-hosted, Anthropic-compatible endpoint needs the exact
opposite: ``ANTHROPIC_BASE_URL`` (and usually ``ANTHROPIC_AUTH_TOKEN``) *must*
reach the session. Rather than punch a hole in the main launcher, that case
lives here as its own launcher, with its own config file and its own entry
script. The two paths share the container machinery (image, overlay, binds,
instance lifecycle) by importing it; they do not share the auth policy.

Entry point: ``local/madrun.sh`` → ``python3 -m launcher_local run``.
"""
