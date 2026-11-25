-- Run this inside YOUR application database, from the MySQL client on your EC2 instance.
-- You create the database and the dedicated application user yourself (see the project brief, Section 8).

CREATE TABLE notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    description TEXT,
    s3_object_key VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
