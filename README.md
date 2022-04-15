# Web-parser
A script for searching all the endpoints of the site and building its map.

There are `parser.py` module with necessary functions, `test.py` module to test performance 
and the correctness of scanning, and experimental `asyncho.py` module to request page 
asynchronously (currently not supported, but in plans). 

## To Compare
To compare the correctness of endpoints search you can use: https://www.xml-sitemaps.com/.

## Example
The following code:
```python
site = "https://www.google.com/"
_, scanned, found = run_for_pages(site, nesting_limit=3, scanned_limit=2)
tree = build_tree(site, found)
write_report(
	site,
	scanned=len(scanned),
	found=len(found),
	endpoints=found,
	tree=tree,
)
```	
makes the following `www.google.json` file:
```yaml
{
    "url": "https://www.google.com/",
    "scanned": 2,
    "found": 13,
    "endpoints": [
        "https://accounts.google.com/ServiceLogin",
        "https://google.com/search/howsearchworks/",
        "https://mail.google.com/mail/",
        "https://policies.google.com/privacy",
        "https://policies.google.com/terms",
        "https://support.google.com/",
        "https://support.google.com/websearch/",
        "https://www.google.com/",
        "https://www.google.com/advanced_search",
        "https://www.google.com/history/optout",
        "https://www.google.com/intl/ru_ru/ads/",
        "https://www.google.com/preferences",
        "https://www.google.com/services/"
    ],
    "tree": {
        "google.com": {
            "accounts:domain": {
                "ServiceLogin": null
            },
            "search": {
                "howsearchworks": null
            },
            "mail:domain": {
                "mail": null
            },
            "policies:domain": {
                "privacy": null,
                "terms": null
            },
            "support:domain": {
                "websearch": null
            },
            "www:domain": {
                "advanced_search": null,
                "history": {
                    "optout": null
                },
                "intl": {
                    "ru_ru": {
                        "ads": null
                    }
                },
                "preferences": null,
                "services": null
            }
        }
    }
}
```

## Searching Parameters
You can set arguments manually in the code, load them from the config or pass them through 
command line.

1. `other_domains: bool`  
Command-line: `-o`, `--others`  
Any passed string except "false" is considered as `True`.

This parameter filters links not containing required domain.
```python
site = "https://cloud.google.com/"

other_domains = True
link = "https://console.cloud.google.com/"  	# Will be passed
link = "https://careers.google.com/cloud"  		# Will be passed

other_domains = False
link = "https://console.cloud.google.com/"  	# Will be passed
link = "https://careers.google.com/cloud"  		# Will be skipped
```

2. `nesting_limit: int`  
Command-line: `-n`, `--nesting`

A limit on link nesting counted by slashes.
```python
nesting_limit = 2

link = "https://dvmn.org/modules/website-layout-for-pydev/"
# Will be passed

link = "https://dvmn.org/modules/website-layout-for-pydev/current-lesson/"
# Will be skipped
```

3. `time_limit: int`  
Command-line: `-t`, `--time`

A limit on runtime of the script. 

4. `scanned_limit: int`  
Command-line: `-s`, `--scanned`

A limit on number of scanned (requested) pages.

5. `found_limit: int`  
Command-line: `-f`, `--found`

A limit on total number of unique pages found.

6. `ignore_list: list`  
Command-line: `-i`, `--ignore`

A list with forbidden endpoints.
```python
site = "https://dvmn.org/modules/"
ignore_list = [
	"/signin/", "/encyclopedia/", "/.../async-python/",
]
# The following links will be skipped:
link = "https://dvmn.org/signin"
link = "https://dvmn.org/encyclopedia/tutorial/tutorial_git/"
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

- Loading config. Config is a JSON with optional parameters for scanning.  
Command-line: `-c`, `--config`  
Manually:
```python
from utils import load_config
params = load_config("your_config.json")
```
