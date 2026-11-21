"""Small helpers around the supabase-py query builder."""


class OneRow:
    """Mimics a response whose .data is a single row dict, or None if no row."""
    __slots__ = ('data',)

    def __init__(self, data):
        self.data = data


def fetch_one(query) -> OneRow:
    """
    Use instead of `.single().execute()`.

    `.single()` makes PostgREST raise (PGRST116) when no row matches, so every
    `if not res.data: return 404` written after it was dead code and missing
    rows surfaced as 500s. This returns OneRow(None) instead.
    """
    res = query.limit(1).execute()
    return OneRow(res.data[0] if res and res.data else None)
