-- sample.sql
-- A sample file for testing SQL syntax highlighting.

SELECT
    id,
    name,
    email,
    created_at
FROM
    users
WHERE
    is_active = TRUE
    AND last_login > '2024-01-01'
ORDER BY
    created_at DESC;

/*
  This is a multi-line comment.
  It's here to ensure that the lexer handles block comments correctly.
*/

INSERT INTO logs (level, message) VALUES ('info', 'User #123 logged in.');

UPDATE products
SET price = price * 1.1, status = 'repriced'
WHERE category_id IN (SELECT id FROM categories WHERE name = 'Electronics');