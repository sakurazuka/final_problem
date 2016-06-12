#healthcare.pyを動かすためのDBを作成

#Windowsの場合
cd ¥python¥sqlite3¥final_problem¥sql
¥python¥sqlite3 ..db¥health.db < .¥healthcare_ini.sql

#Macの場合
cd ~/Desktop/python/final_problem/sql
sqlite3 ../db/health.db < ./healthcare_ini.sql

#simplified_settings.pyを動かすためのDBを作成
#Windowsの場合
cd ¥python¥sqlite3¥final_problem¥sql
¥python¥sqlite3 ..db¥test.db < .¥setup.sql

#Macの場合
cd ~/Desktop/python/final_problem/sql
sqlite3 ../db/test.db < ./setup.sql
