```
find ~ -type d -name .git >/tmp/list
grep -vE '\.Trash/|pdev.bkp/' /tmp/list | grep servicenow >/tmp/sn
main.py --repo_list /tmp/sn --project servicenow
idea servicenow
```
