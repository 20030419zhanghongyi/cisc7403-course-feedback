CREATE TABLE IF NOT EXISTS public.feedback (
    id SERIAL PRIMARY KEY,
    difficulty INTEGER NOT NULL
        CHECK (difficulty BETWEEN 1 AND 5),
    topic VARCHAR(32) NOT NULL
        CHECK (
            topic IN (
                'Virtual Machine',
                'Docker',
                'Kubernetes',
                'Serverless'
            )
        )
);
