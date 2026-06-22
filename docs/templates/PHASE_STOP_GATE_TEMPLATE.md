## 0. Stop-gate

Before making any changes, verify repository state:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
```

Expected: `/c/DEV/FRAMEWORK/Framework-voyage-mvp` in Git Bash. In PowerShell, verify the equivalent resolved Windows path.

```bash
git branch --show-current
git status -sb
git log --oneline --decorate -10
```

Expected:

- Branch: `[specified branch]`
- Base: `[specified base commit]`
- Required tags: `[specified tags or none]`
- Working tree: clean

Known Windows warnings that may be acceptable when documented as pre-existing:

```text
warning: could not open directory '.test-tmp-*/': Permission denied
```

ACL warnings do not excuse unrelated modified or untracked project files. If the working tree is not clean, excluding only verified pre-existing ACL directories, stop and report.

Confirm that the approved phase prompt exists and that every intended change is listed under allowed files. If the branch, base, tag, prompt, scope, or repository state is wrong, do not edit files.

Do not commit.
Do not push.

Replace these final two rules only when the approved phase prompt grants that exact Git authority.
