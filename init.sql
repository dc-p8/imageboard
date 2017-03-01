PRAGMA foreign_keys = 'ON';

DROP TABLE IF EXISTS user;
CREATE TABLE IF NOT EXISTS user
(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	password TEXT,
	time_created INTEGER
);

DROP TABLE IF EXISTS thread;
CREATE TABLE IF NOT EXISTS thread
(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	title TEXT,
	post_id INTEGER,
	board_id INTEGER,

	FOREIGN KEY(post_id) REFERENCES post(id)
	FOREIGN KEY(board_id) REFERENCES board(id)
);


DROP TABLE IF EXISTS reply;
CREATE TABLE IF NOT EXISTS reply
(
	post_id INTEGER,
	reply_id INTEGER,

	FOREIGN KEY(post_id) REFERENCES post(id),
	FOREIGN KEY(reply_id) REFERENCES post(id)
);


DROP TABLE IF EXISTS post;
CREATE TABLE IF NOT EXISTS post
(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	content TEXT,
	time_created INTEGER,
	time_modified INTEGER,
	thread_id INTEGER,
	user_id INTEGER,

	FOREIGN KEY(thread_id) REFERENCES thread(id),
	FOREIGN KEY(user_id) REFERENCES user(id)
);

DROP TABLE IF EXISTS file;
CREATE TABLE IF NOT EXISTS file
(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	post_id INTEGER,
	FOREIGN KEY(post_id) REFERENCES post(id)
);

DROP TABLE IF EXISTS board;
CREATE TABLE IF NOT EXISTS board
(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	description TEXT
);

INSERT INTO board (name, description) VALUES ('gen', 'Discussions générales');
INSERT INTO board (name, description) VALUES ('mus', 'Discussions à propos de la musique');