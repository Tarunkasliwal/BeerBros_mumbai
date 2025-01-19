# Example CQL commands to create tables
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY,
    name TEXT,
    dob DATE,
    gender TEXT,
    city TEXT,
    state TEXT
);

CREATE TABLE IF NOT EXISTS kundalis (
    user_id UUID PRIMARY KEY,
    birth_chart TEXT,
    insights MAP<TEXT, TEXT>
);