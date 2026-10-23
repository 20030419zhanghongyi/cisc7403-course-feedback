"""Read a consistent summary with a single PostgreSQL statement."""
from .db import connect

TOPICS = ('Virtual Machine', 'Docker', 'Kubernetes', 'Serverless')


def get_summary():
    with connect() as connection:
        row = connection.execute(
            '''SELECT COUNT(*), AVG(difficulty),
                      COUNT(*) FILTER (WHERE topic = %s),
                      COUNT(*) FILTER (WHERE topic = %s),
                      COUNT(*) FILTER (WHERE topic = %s),
                      COUNT(*) FILTER (WHERE topic = %s)
               FROM public.feedback''', TOPICS
        ).fetchone()
    return {
        'total': row[0],
        'average': None if row[1] is None else format(row[1], '.2f'),
        'topics': list(zip(TOPICS, row[2:])),
    }
