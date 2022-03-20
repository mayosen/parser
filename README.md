# Web-parser
A script for searching all the endpoints of the site and building its map.

There are `main.py` module with necessary functions, `test.py` module to test performance and the correctness of scanning, and experimental `asyncho.py` module to request page asynchronously. 

### To Compare
To compare script in searching of endpoints you can use https://www.xml-sitemaps.com/.

### Searching parameters
1. `other_domains: bool`

This parameter filters links not containing required domain.
```python
initial_link = "https://cloud.google.com/"
link = "https://console.cloud.google.com/"
# If `True` will be passed, if `False` will be passed yet.
link = "https://careers.google.com/cloud"
# If `True` will be passed, if `False` will be skipped.
```

2. `nesting_limit: int` 

Limit on link nesting counted by slashes.
```python
nesting_limit = 2
link = "https://dvmn.org/modules/website-layout-for-pydev/"
# Will be passed.
link = "https://dvmn.org/modules/website-layout-for-pydev/current-lesson/"
# Will be skipped.
```

3. `time_limit: int or float`

A limit on runtime of script. 

4. `scanned_limit: int`

A limit on number scanned (requested) pages.

5. `found_limit: int`

A limit on total number of found unique pages.

6. `ignore_list: list`

A list with forbidden endpoints.
```python
initial_link = "https://dvmn.org/modules/"
ignore_list = [
            "/signin/", "/encyclopedia/", "/.../async-python/",
]
# The following links will be skipped:
link = "https://dvmn.org/signin"
link = "https://dvmn.org/encyclopedia/tutorial/tutorial_git/".
link = "https://dvmn.org/modules/async-python/"
```

- Instead of passing arguments separately, you can use `params` dict.
```python
site = "https://dvmn.org/modules/"
params = dict(
    other_domains=True,
    nesting_limit=3,
    time_limit=0,
    scanned_limit=0,
    found_limit=0,
    ignore_list=[
        "/signin/", "/encyclopedia/", "/.../async-python/",
    ],
)
times, scanned, found = run_for_pages(site, params=params)
``` 

### Example
The following code:
```python
url = "https://www.google.com/"

_, scanned, found = run_for_pages(
        url, nesting_limit=3,
        scanned_limit=2
		)
		
tree = build_tree(url, found)
		
write_report(
        url,
        scanned=len(scanned),
        found=len(found),
        endpoints=found,
        tree=tree,
    )
```	
makes the following json file:
```yaml
{
    "url": "https://www.google.com/",
    "scanned": 2,
    "found": 12,
    "endpoints": [
        "https://accounts.google.com/ServiceLogin",
        "https://accounts.google.com/TOS",
        "https://mail.google.com/mail/",
        "https://policies.google.com/privacy",
        "https://policies.google.com/terms",
        "https://support.google.com/accounts",
        "https://support.google.com/websearch/",
        "https://www.google.com/",
        "https://www.google.com/advanced_search",
        "https://www.google.com/history/optout",
        "https://www.google.com/preferences",
        "https://www.google.com/services/"
    ],
    "tree": {
        "google.com": {
            "accounts": {
                "ServiceLogin": null,
                "TOS": null
            },
            "mail": {
                "mail": null
            },
            "policies": {
                "privacy": null,
                "terms": null
            },
            "support": {
                "accounts": null,
                "websearch": null
            },
            "www": {
                "advanced_search": null,
                "history": {
                    "optout": null
                },
                "preferences": null,
                "services": null
            }
        }
    }
}
```
