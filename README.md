# Web-parser
A script for searching all the endpoints of the site and building its map.

There are `test.py` module to test performance and the correctness of `scan_page()` work, and experimental `asyncho.py` module to request page asynchronously. 

### Example
The following code:
```python
url = "https://www.google.com/"

_, scanned, found = run_for_pages(
        url, nesting_limit=3,
        scanned_limit=2)
		
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
