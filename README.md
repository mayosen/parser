# Parser

[![MIT License][license-image]][license]

Asynchronously find all site's endpoints and build its map.

## Technologies
- Python 3.11
- asyncio
- aiohttp
- pytest
- Poetry

## Usage

Command

```sh
$ poetry run parse --max-scanned 5 https://www.google.com
```

will generate file like

```json
{
    "start_url": "https://www.google.com",
    "total_scanned": 7,
    "total_found": 9,
    "elapsed_time": 0.33,
    "stop_reason": "SCANNED_LIMIT",
    "scanned": [
        "https://www.google.com",
        "https://www.google.com/intl/ru/about.html",
        "https://www.google.com/intl/ru/about/",
        "https://www.google.com/intl/ru/ads/",
        "https://www.google.com/intl/ru/policies/privacy/",
        "https://www.google.com/intl/ru/policies/terms/",
        "https://www.google.com/setprefdomain"
    ],
    "found": [
        "https://www.google.com",
        "https://www.google.com/advanced_search",
        "https://www.google.com/imghp",
        "https://www.google.com/intl/ru/about.html",
        "https://www.google.com/intl/ru/about/",
        "https://www.google.com/intl/ru/ads/",
        "https://www.google.com/intl/ru/policies/privacy/",
        "https://www.google.com/intl/ru/policies/terms/",
        "https://www.google.com/setprefdomain"
    ]
}
```

### Configuration
```sh
$ poetry run parse --help

Usage: parse [OPTIONS] URL

  Parse given URL and save results to json in current directory.

Options:
  --timeout FLOAT           Total timeout for scanning. Parser doesn't
                            guarantee what parsing will be finished
                            immediately after the timeout.
  --max-scanned INTEGER     Limit for scanned urls. Parser doesn't guarantee
                            what exactly 'n' urls will be scanned, but at
                            least 'n'.
  --max-found INTEGER       Limit for found urls. Parser doesn't guarantee
                            what exactly 'n' urls will be found, but at least
                            'n'.
  --request-timeout FLOAT   Timeout for single request.  [default: 10]
  --workers-number INTEGER  Number of workers who scan urls concurrently.
                            [default: 5]
  --check-interval FLOAT    Interval for checking the exceeded limits (s).
                            [default: 0.1]
  --help                    Show this message and exit.
```


Alternatively you can use parser as library:

```python
import asyncio
from parser.web import parse


async def main():
    found, scanned, reason = await parse("https://www.google.com", max_scanned=5)


asyncio.run(main())
```

## Download

Whole project

```sh
$ git clone https://github.com/mayosen/parser.git -b main
$ poetry install
```

As library

```sh
$ poetry add git+https://github.com/mayosen/parser.git#main
```

## Testing

```sh
$ poetry run pytest
```

[license-image]: https://img.shields.io/badge/license-MIT-blue.svg
[license]: LICENSE.md
