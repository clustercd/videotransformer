# Privacy and publication

The repository contains application source, English documentation and synthetic
tests. Media, cookies, source URL archives, analysis results, logs, machine
metadata, private settings and virtual environments are excluded.

The public baseline was prepared on 20 October 2026. The original folder had no
Git history. Original source files were backed up outside the checkout before
editing. The initial Git author and committer use a neutral contributor identity.

## Secrets and local data

Use `PEXELS_API_KEY` or an ignored `private_settings.json` in the data directory.
Never put credentials in source files, documentation, screenshots or issues.
Configuration responses expose only whether a Pexels key is configured.
The Flask secret is generated at startup unless explicitly supplied.

Logs and download archives can contain personal paths, URLs and browsing
activity. Keep the entire data and logs directories private, including browser
cookie exports. Download requests contact the selected third-party source.
The dashboard uses third-party CDN assets; it is not fully offline.

The server binds to loopback. It can access local files and browser sessions
when the user requests those operations. It is intended for trusted local use,
not a public web service. Do not expose its port to other users.

## Release audit

```sh
python scripts/audit_public.py
python scripts/audit_git_history.py
```

Both commands accept `--private-denylist PATH` for an external JSON array of known
private identifiers, or use `PUBLIC_PRIVACY_DENYLIST`. Keep this list outside the checkout. Explicitly missing lists
cause an error instead of silently weakening the audit.

The source audit checks tracked and non-ignored new files. The history audit
checks every local Git object, including unreachable objects, historical paths,
authors, commit messages, refs, reflogs, repository configuration and the index.
Reports contain locations or object hashes, never matched secret values.

These are heuristic checks, not a guarantee that every possible personal fact or
secret format is detectable. Review new text and assets manually. Ignored local
files, external backups, downloaded dependencies and other clones are outside
the audit. Publish through Git rather than copying the entire working folder.
