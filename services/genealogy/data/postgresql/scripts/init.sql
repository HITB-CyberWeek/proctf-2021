CREATE SEQUENCE user_id_seq;
CREATE TABLE users (
	id INTEGER NOT NULL PRIMARY KEY DEFAULT nextval('user_id_seq'),
	login VARCHAR(100) NOT NULL,
	password_hash VARCHAR(32) NOT NULL
);
ALTER SEQUENCE user_id_seq OWNED BY users.id;

CREATE SEQUENCE person_id_seq;
CREATE TABLE genealogy_tree_persons (	
	id INTEGER NOT NULL PRIMARY KEY DEFAULT nextval('person_id_seq'),
	owner_id INTEGER NOT NULL,
	birth_date BIGINT NOT NULL,
	death_date BIGINT NOT NULL,
	title VARCHAR(100) NOT NULL,
	first_name VARCHAR(100) NOT NULL,
	middle_name VARCHAR(100) NOT NULL,
	last_name VARCHAR(100) NOT NULL,
	photo_url VARCHAR(100) NOT NULL
);
ALTER SEQUENCE person_id_seq OWNED by genealogy_tree_persons.id;
CREATE INDEX genealogy_tree_persons_owner_id ON genealogy_tree_persons (owner_id);

CREATE SEQUENCE tree_id_seq;
CREATE TABLE genealogy_trees (
	id INTEGER NOT NULL PRIMARY KEY DEFAULT nextval('tree_id_seq'),
	user_id INTEGER NOT NULL UNIQUE,
	person_id INTEGER,
	title TEXT NOT NULL,
	description TEXT NOT NULL
);
ALTER SEQUENCE tree_id_seq OWNED by genealogy_trees.id;

CREATE INDEX genealogy_trees_user_id ON genealogy_trees (user_id);
CREATE INDEX genealogy_trees_person_id ON genealogy_trees (person_id);

CREATE TABLE genealogy_tree_person_parents (
	parent_id INTEGER NOT NULL,
	child_id INTEGER NOT NULL
);

CREATE INDEX genealogy_tree_person_parents_parent_id ON genealogy_tree_person_parents (parent_id);
CREATE INDEX genealogy_tree_person_parents_child_id ON genealogy_tree_person_parents (child_id);

CREATE TABLE genealogy_tree_owners (
	tree_id INTEGER NOT NULL,
	user_id BIGINT NOT NULL
);

CREATE INDEX genealogy_tree_owners_tree_id ON genealogy_tree_owners (tree_id);
CREATE INDEX genealogy_tree_owners_user_id ON genealogy_tree_owners (user_id);