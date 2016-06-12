/* テーブルの作成 */
DROP TABLE if exists users;
CREATE TABLE IF NOT EXISTS users (
	 account_id INTEGER PRIMARY KEY AUTOINCREMENT
     ,account_name TEXT NOT NULL
     ,email TEXT NOT NULL
     ,password TEXT NOT NULL
     ,serial TEXT NOT NULL
     ,birthday TEXT NOT NULL
     ,user_photo TEXT NOT NULL
     ,UNIQUE(email)
     ,UNIQUE(account_name,email));
CREATE INDEX IF NOT EXISTS 'ix_name' ON users (account_name,email);

DROP TABLE if exists bmi_data;
CREATE TABLE IF NOT EXISTS bmi_data (
	account_id INTEGER NOT NULL
	,date TEXT NOT NULL
	,height REAL NOT NULL
	,weight REAL NOT NULL
    ,UNIQUE(account_id,date));
CREATE INDEX IF NOT EXISTS 'ix_bmi' ON bmi_data (account_id,date);

DROP TABLE if exists blood_data;
CREATE TABLE IF NOT EXISTS blood_data (
	account_id INTEGER NOT NULL
	,datetime TEXT NOT NULL
	,high_pressure INTEGER NOT NULL
	,low_pressure INTEGER NOT NULL
	,pulse INTEGER NOT NULL
    ,UNIQUE(account_id,datetime));
CREATE INDEX IF NOT EXISTS 'ix_blood' ON blood_data (account_id,datetime);



/* ユーザ情報マスタデータ */
INSERT INTO users (
	account_name
	,password
	,email
	,serial
	,birthday
	,user_photo
	)
 VALUES (
 	'麹町太郎'
 	/* 'taro1234'をハッシュ化*/
 	,'4c6c1f0ca213adcd99b446b3547be12b2c770ea4cac07f769aa98a56a9cc377a'  
 	,'taro@hoge.com'
 	,'1234567890'
 	,'1994/01/01'
 	,'./upload/taro.png'
 	 );

INSERT INTO users (
	account_name
	,password
	,email
	,serial
	,birthday
	,user_photo
	) VALUES (
 	'麹町花子'
 	/* 'hanako123'をハッシュ化 */
	,'d34138a2b52313b69366debb4dbbd85ab1ca6af2020401ea5bb9cb744e413c2b'
 	,'hanako@hoge.com'
 	,'2234567890'
 	,'1996/01/01'
 	,'./upload/hanako.png'
 	 );


INSERT INTO bmi_data (account_id,date,height,weight) VALUES (1,  '2013-08-01',  170.5, 65.0);
INSERT INTO bmi_data (account_id,date,height,weight) VALUES (1,  '2013-09-01',  170.5, 66.0);
INSERT INTO bmi_data (account_id,date,height,weight) VALUES (1,  '2013-10-01',  170.5, 67.0);
INSERT INTO bmi_data (account_id,date,height,weight) VALUES (2,  '2013-08-01',  155.5, 50.0);
INSERT INTO bmi_data (account_id,date,height,weight) VALUES (2,  '2013-09-01',  155.5, 52.0);
INSERT INTO bmi_data (account_id,date,height,weight) VALUES (2,  '2013-10-01',  155.5, 53.0);
INSERT INTO blood_data (account_id,datetime,high_pressure,low_pressure,pulse) VALUES (1,  '2013-08-01',  121, 80, 80);
INSERT INTO blood_data (account_id,datetime,high_pressure,low_pressure,pulse) VALUES (1,  '2013-09-01',  126, 90, 80);
INSERT INTO blood_data (account_id,datetime,high_pressure,low_pressure,pulse) VALUES (1,  '2013-10-01',  131, 95, 80);
INSERT INTO blood_data (account_id,datetime,high_pressure,low_pressure,pulse) VALUES (2,  '2013-08-01',  131, 85, 90);
INSERT INTO blood_data (account_id,datetime,high_pressure,low_pressure,pulse) VALUES (2,  '2013-09-01',  136, 90, 100);
INSERT INTO blood_data (account_id,datetime,high_pressure,low_pressure,pulse) VALUES (2,  '2013-10-01',  126, 95, 95);
