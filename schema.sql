-- This file should contain all code required to create & seed database tables.
DROP TABLE IF EXISTS rating_interaction;
DROP TABLE IF EXISTS request_interaction;
DROP TABLE IF EXISTS rating;
DROP TABLE IF EXISTS request;
DROP TABLE IF EXISTS exhibition;
DROP TABLE IF EXISTS floor;
DROP TABLE IF EXISTS department;

-- create tables for lmnh_database
CREATE TABLE department(
    department_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_name varchar(100) UNIQUE NOT NULL
);

INSERT INTO department (department_name) VALUES
    ('Entomology'),
    ('Geology'),
    ('Zoology'),
    ('Ecology'),
    ('Paleontology');

CREATE TABLE floor(
    floor_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    floor_name varchar(100) UNIQUE NOT NULL
);

INSERT INTO floor (floor_name) VALUES
    ('Vault'),
    ('1'),
    ('2'),
    ('3');

CREATE TABLE exhibition(
    exhibition_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    exhibition_name varchar(100) NOT NULL,
    exhibition_description text,
    floor_id int NOT NULL REFERENCES floor(floor_id),
    department_id int NOT NULL REFERENCES department(department_id),
    exhibition_start_date date NOT NULL,
    public_id varchar(10) UNIQUE NOT NULL
);

INSERT INTO exhibition (
    exhibition_name,
    exhibition_description,
    floor_id,
    department_id,
    exhibition_start_date,
    public_id
) VALUES
    (
        'Measureless to Man',
        'An immersive 3D experience: delve deep into a previously-inaccessible cave system.',
        (SELECT floor_id FROM floor WHERE floor_name = '1'),
        (SELECT department_id FROM department WHERE department_name = 'Geology'),
        DATE '2021-08-23',
        'EXH_00'
    ),
    (
        'Adaptation',
        'How insect evolution has kept pace with an industrialised world',
        (SELECT floor_id FROM floor WHERE floor_name = 'Vault'),
        (SELECT department_id FROM department WHERE department_name = 'Entomology'),
        DATE '2019-07-01',
        'EXH_01'
    ),
    (
        'The Crenshaw Collection',
        'An exhibition of 18th Century watercolours, mostly focused on South American wildlife.',
        (SELECT floor_id FROM floor WHERE floor_name = '2'),
        (SELECT department_id FROM department WHERE department_name = 'Zoology'),
        DATE '2021-03-03',
        'EXH_02'
    ),
    (
        'Cetacean Sensations',
        'Whales: from ancient myth to critically endangered.',
        (SELECT floor_id FROM floor WHERE floor_name = '1'),
        (SELECT department_id FROM department WHERE department_name = 'Zoology'),
        DATE '2019-07-01',
        'EXH_03'
    ),
    (
        'Our Polluted World',
        'A hard-hitting exploration of humanity''s impact on the environment.',
        (SELECT floor_id FROM floor WHERE floor_name = '3'),
        (SELECT department_id FROM department WHERE department_name = 'Ecology'),
        DATE '2021-05-12',
        'EXH_04'
    ),
    (
        'Thunder Lizards',
        'How new research is making scientists rethink what dinosaurs really looked like.',
        (SELECT floor_id FROM floor WHERE floor_name = '1'),
        (SELECT department_id FROM department WHERE department_name = 'Paleontology'),
        DATE '2023-02-01',
        'EXH_05'
    );

CREATE TABLE request(
    request_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_value int UNIQUE NOT NULL,
    request_description varchar(100) NOT NULL
);

INSERT INTO request (request_value, request_description) VALUES
    (0, 'Assistance'),
    (1, 'Emergency');

CREATE TABLE request_interaction(
    request_interaction_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id int NOT NULL REFERENCES request(request_id),
    exhibition_id int NOT NULL REFERENCES exhibition(exhibition_id),
    event_at timestamptz NOT NULL  
);

CREATE TABLE rating(
    rating_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rating_value int UNIQUE NOT NULL,
    rating_description varchar(100)
);

INSERT INTO rating (rating_value, rating_description) VALUES
    (0, 'Terrible'),
    (1, 'Bad'),
    (2, 'Neutral'),
    (3, 'Good'),
    (4, 'Amazing');

CREATE TABLE rating_interaction(
    rating_interaction_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rating_id int NOT NULL REFERENCES rating(rating_id),
    exhibition_id int NOT NULL REFERENCES exhibition(exhibition_id),
    event_at timestamptz NOT NULL
);


