from abc import abstractmethod, ABC

from scanner import split_endpoints


class BaseParser(ABC):
    def __init__(
            self,
            other_domains=True,
            nesting_limit=0,
            time_limit=0,
            scanned_limit=0,
            found_limit=0,
            ignore_list: list[str] = None,
    ):
        self.other_domains = other_domains
        self.nesting_limit = nesting_limit
        self.ignore_list = [split_endpoints(ignore_sample) for ignore_sample in ignore_list] if ignore_list else None

        self.time_limit = time_limit
        self.scanned_limit = scanned_limit
        self.found_limit = found_limit

        self.pages_scanned = set()
        self.pages_found = set()

    @abstractmethod
    def run(self, url: str) -> tuple[dict, list, list]:
        raise NotImplementedError
