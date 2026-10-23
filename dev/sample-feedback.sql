-- Run explicitly against the isolated development database only.
-- Refuse to alter a database that already contains feedback.
BEGIN;
LOCK TABLE public.feedback IN EXCLUSIVE MODE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.feedback) THEN
        RAISE EXCEPTION 'Feedback table is not empty; sample data was not added';
    END IF;
END;
$$;
INSERT INTO public.feedback (difficulty, topic)
VALUES (1, 'Docker'), (3, 'Docker'), (5, 'Kubernetes');
COMMIT;
