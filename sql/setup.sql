DROP TABLE if exists users;
CREATE TABLE IF NOT EXISTS users (
     account_name TEXT NOT NULL,
     user_photo TEXT NOT NULL,
     UNIQUE(account_name,user_photo));
/* CREATE INDEX IF NOT EXISTS 'ix_name' ON users (account_name); */

INSERT INTO users (account_name, user_photo) VALUES ('麹町太郎' , './upload/taro.png');
INSERT INTO users (account_name, user_photo) VALUES ('麹町花子' , './upload/hanako.png');
