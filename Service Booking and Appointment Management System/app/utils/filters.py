def apply_filters(query, **filters):
    for key, value in filters.items():
        if value is not None:
            query = query.filter(getattr(query.column_descriptions[0]['entity'], key) == value)
    return query
