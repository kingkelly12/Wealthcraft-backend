"""
In-memory stand-in for the supabase-py client, for route and job tests.

Supports the query-builder subset the app uses:
    table(name).select(...).eq/neq/gt/gte/lt/lte/in_/is_(...)
        .or_('col.is.null,col.lt.x').order(col, desc=...).limit(n).single().execute()
    .insert(row|rows) .update(values) .delete() .upsert(row)
    rpc(name, params).execute()   (adjust_sanity is built in; stub others)

Rows are plain dicts held in `fake.tables[name]`. Embedded joins such as
'integrated_missions!mission_id(name, duration_months)' are not resolved:
tests store the nested dict on the row directly, exactly as PostgREST
would return it.
"""
import copy
import itertools
import types
import uuid


class FakeAPIError(Exception):
    """Mirrors postgrest's APIError for .single() on zero or many rows."""


class _Result(types.SimpleNamespace):
    pass


class _Query:
    def __init__(self, fake, table):
        self.fake = fake
        self.table = table
        self.filters = []
        self.op = 'select'
        self.payload = None
        self.is_single = False
        self.order_by = None
        self.limit_n = None
        self.count_mode = None

    # -- builders -------------------------------------------------------------
    def select(self, *_cols, count=None, **_kw):
        self.count_mode = count
        return self

    def _filter(self, fn):
        self.filters.append(fn)
        return self

    def eq(self, col, val):
        return self._filter(lambda r: _norm(r.get(col)) == _norm(val))

    def neq(self, col, val):
        return self._filter(lambda r: _norm(r.get(col)) != _norm(val))

    def gt(self, col, val):
        return self._filter(lambda r: r.get(col) is not None and r.get(col) > val)

    def gte(self, col, val):
        return self._filter(lambda r: r.get(col) is not None and r.get(col) >= val)

    def lt(self, col, val):
        return self._filter(lambda r: r.get(col) is not None and r.get(col) < val)

    def lte(self, col, val):
        return self._filter(lambda r: r.get(col) is not None and r.get(col) <= val)

    def ilike(self, col, pattern):
        """SQL ILIKE with % wildcards (escapes ignored: tests don't need them)."""
        import re
        rx = re.compile('^' + '.*'.join(re.escape(p) for p in pattern.split('%')) + '$', re.I | re.S)
        return self._filter(lambda r: r.get(col) is not None and bool(rx.match(str(r.get(col)))))

    def in_(self, col, vals):
        vals = {_norm(v) for v in vals}
        return self._filter(lambda r: _norm(r.get(col)) in vals)

    def is_(self, col, val):
        target = None if val in (None, 'null') else val
        return self._filter(lambda r: r.get(col) is target)

    @property
    def not_(self):
        outer = self

        class _Not:
            def is_(self, col, val):
                target = None if val in (None, 'null') else val
                return outer._filter(lambda r: r.get(col) is not target)

        return _Not()

    def or_(self, expr):
        """PostgREST or-filter, e.g. 'col.is.null,col.lt.2026-01-01T00:00:00'."""
        tests = []
        for part in expr.split(','):
            col, op, val = part.split('.', 2)
            if op == 'is':
                target = None if val == 'null' else val
                tests.append(lambda r, c=col, t=target: r.get(c) is t)
            elif op in _OPS:
                tests.append(lambda r, c=col, o=op, v=val: r.get(c) is not None and _OPS[o](str(r.get(c)), v))
            else:
                raise NotImplementedError(f'or_ operator {op}')
        return self._filter(lambda r: any(t(r) for t in tests))

    def order(self, col, desc=False, **_kw):
        self.order_by = (col, desc)
        return self

    def limit(self, n):
        self.limit_n = n
        return self

    def single(self):
        self.is_single = True
        return self

    def maybe_single(self):
        self.is_single = 'maybe'
        return self

    def insert(self, payload):
        self.op, self.payload = 'insert', payload
        return self

    def upsert(self, payload, on_conflict=None, **_kw):
        self.op, self.payload = 'upsert', payload
        self.conflict = [c.strip() for c in on_conflict.split(',')] if on_conflict else []
        return self

    def update(self, payload):
        self.op, self.payload = 'update', payload
        return self

    def delete(self):
        self.op = 'delete'
        return self

    # -- execution ------------------------------------------------------------
    def _matching(self, rows):
        return [r for r in rows if all(f(r) for f in self.filters)]

    def execute(self):
        rows = self.fake.tables.setdefault(self.table, [])
        self.fake.calls.append((self.op, self.table, copy.deepcopy(self.payload)))

        if self.op in ('insert', 'upsert'):
            new = self.payload if isinstance(self.payload, list) else [self.payload]
            out = []
            for item in new:
                keys = getattr(self, 'conflict', [])
                old = next((r for r in rows if keys and all(_norm(r.get(k)) == _norm(item.get(k)) for k in keys)), None)
                if old is not None:
                    old.update(item)
                    out.append(old)
                    continue
                row = {'id': str(uuid.uuid4()), **item}
                rows.append(row)
                out.append(row)
            return _Result(data=out, count=len(out))

        match = self._matching(rows)
        if self.op == 'update':
            for r in match:
                r.update(self.payload)
            return _Result(data=match, count=len(match))
        if self.op == 'delete':
            for r in match:
                rows.remove(r)
            return _Result(data=match, count=len(match))

        if self.order_by:
            col, desc = self.order_by
            match = sorted(match, key=lambda r: (r.get(col) is None, r.get(col)), reverse=desc)
        if self.limit_n is not None:
            match = match[: self.limit_n]
        total = len(match)
        if self.is_single:
            if len(match) != 1:
                if self.is_single == 'maybe' and not match:
                    return _Result(data=None, count=0)
                raise FakeAPIError(f'{self.table}: expected 1 row, got {len(match)}')
            return _Result(data=match[0], count=1)
        return _Result(data=match, count=total)


_OPS = {
    'eq': lambda a, b: a == b,
    'neq': lambda a, b: a != b,
    'lt': lambda a, b: a < b,
    'lte': lambda a, b: a <= b,
    'gt': lambda a, b: a > b,
    'gte': lambda a, b: a >= b,
}


def _adjust_sanity(fake, p_user_id, p_delta):
    """Mirrors public.adjust_sanity: clamp 0..100, return the new value."""
    for row in fake.rows('profiles'):
        if _norm(row.get('user_id')) == _norm(p_user_id):
            row['sanity'] = max(0, min(100, int(row.get('sanity', 100)) + int(p_delta)))
            return row['sanity']
    return None


def _norm(v):
    return str(v) if isinstance(v, uuid.UUID) else v


class FakeSupabase:
    def __init__(self, tables=None):
        self.tables = tables if tables is not None else {}
        self.calls = []
        self.rpc_handlers = {'adjust_sanity': _adjust_sanity}
        self._ids = itertools.count(1)

    def table(self, name):
        return _Query(self, name)

    def rpc(self, name, params=None):
        handler = self.rpc_handlers.get(name)
        if handler is None:
            raise FakeAPIError(f'rpc {name} not stubbed')
        data = handler(self, **(params or {}))
        return types.SimpleNamespace(execute=lambda: _Result(data=data))

    # convenience
    def rows(self, table):
        return self.tables.setdefault(table, [])
