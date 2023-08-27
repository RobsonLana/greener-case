CREATE DATABASE IF NOT EXISTS landing_db ;

CREATE TABLE IF NOT EXISTS landing_db.solar_panels (
	sha_id VARCHAR(64) NOT NULL
	origin VARCHAR(32) NOT NULL,
	updated_at DATETIME NOT NULL,
	port VARCHAR(16),
	price VARCHAR(32),
	structure VARCHAR(16),
	PRIMARY KEY (sha_id)
) ;
