"""Session utility functions."""


class SessionUtils:
    @staticmethod
    def dedupe_lists(*lists):
        """Merge multiple lists, removing duplicates while preserving order."""
        seen = set()
        result = []
        for lst in lists:
            if not lst:
                continue
            for item in lst:
                item_id = id(item)
                if item_id not in seen:
                    seen.add(item_id)
                    result.append(item)
        return result
