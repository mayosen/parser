# Web-parser
A script for searching all the endpoints of the site and building its map.

There are `test.py` module to test performance and the correctness of scanning, and experimental `asyncho.py` module to request page asynchronously. 

### Compare
To compare checking found endpoints you can use https://www.xml-sitemaps.com/.

### Scan limitations settings
- `other_domains: bool` - If `False`, links what don't content initial url domains will be passed.

Example initial link: "https://cloud.google.com/":  
`other_domains = True`.  
Link "https://console.cloud.google.com/" will be done.  
Link "https://careers.google.com/cloud" will be done too.  
`other_domains = False`.  
Link "https://console.cloud.google.com/" will be done yet.  
Link "https://careers.google.com/cloud" will be skipped.  
- `nesting_limit: int` - A limit on endpoints what counts slashes in link.

- `time_limit: int` - A limit on runtime of script. 

- `scanned_limit: int` - A limit on requested and scanned pages.

- `found_limit: int` - A limit on total found unique pages.


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
