# coding=utf-8
from bottle import route,template,run,static_file,request,post,HTTPError,redirect
import sqlite3
import os

@route('/', 'GET')
@route('/list', 'GET')
def simplified_list():
	db = sqlite3.connect('./db/test.db').cursor()
	rows=db.execute('SELECT * from users').fetchall()
	db.close()
	return template('./views/simplified_list.html',rows=rows)
	
@route('/edit', 'GET')
def simplified_edit():
	params={'account_name':unicode(request.query['account_name'],'utf-8'),'user_photo':'','submit_type':'更新'}
	db = sqlite3.connect('./db/test.db').cursor()
	row=db.execute('SELECT * from users where account_name=?', (params['account_name'],)).fetchone()
	if row and len(row)==2:
		params['account_name']=row[0]
		params['user_photo']=row[1]
	db.close()
			
	return template('./views/simplified_settings.html',params)

@route('/edit', 'POST')
def simplified_edit_post():
	#POSTで渡されたリクエストパラメータの値を取得
	params={'account_name':unicode(request.forms.get('account_name',''),'utf-8'),
	'bfr_account_name':unicode(request.forms.get('bfr_account_name',''),'utf-8'),
	'submit_type':'更新'}

    #POSTで渡されたファイル情報を取得
	photo=request.files.get('photo')  
	if photo and photo.filename:
		photo.save('./upload',overwrite=True) 
		params['user_photo']='./upload/'+photo.filename
		conn = sqlite3.connect('./db/test.db')
		db=conn.cursor()
		db.execute('''UPDATE users set account_name= ? , user_photo = ?  where account_name=?''',
			(params['account_name'], params['user_photo'], params['bfr_account_name'],))
		conn.commit()
		db.close()
	return redirect('/list')	

@route('/insert', 'GET')
def simplified_insert():
	return template('./views/simplified_settings.html', {'url':'./insert','submit_type':'登録'})	

@route('/insert', 'POST')
def simplified_insert():
	#POSTで渡されたリクエストパラメータの値を取得
	params={'account_name':unicode(request.forms.get('account_name',''),'utf-8'),'submit_type':'登録'}

    #POSTで渡されたファイル情報を取得
	photo=request.files.get('photo')  
	if photo and photo.filename:
		photo.save('./upload',overwrite=True) 
		params['user_photo']='./upload/'+photo.filename
		conn = sqlite3.connect('./db/test.db')
		db=conn.cursor()
		db.execute('''INSERT  INTO users  (account_name, user_photo ) values (?,?) ''',
		 (params['account_name'], params['user_photo'], ))
		conn.commit()
		db.close()

	return redirect('/list')	

@route('/delete', 'POST')
def simplified_delete():
	#POSTで渡されたリクエストパラメータの値を取得
	params={'account_name':unicode(request.forms.get('account_name'),'utf-8')}
	conn = sqlite3.connect('./db/test.db')
	db=conn.cursor()
	row=db.execute('SELECT * from users where account_name=?', (params['account_name'],)).fetchone()
	if row and len(row)==2:
		user_photo=row[1]
		if os.path.isfile(user_photo):
			os.remove(user_photo) 
	db.execute('''DELETE  FROM users  WHERE account_name=?''',
	 (params['account_name'], ))	
	conn.commit()
	db.close()

	return redirect('/list')	

@route('/bmi', 'GET')
def simplified_bmi():
	params={'account_name':unicode(request.query['account_name'],'utf-8')}
	db = sqlite3.connect('./db/test.db').cursor()
	row=db.execute('SELECT * from users where account_name=?', (params['account_name'],)).fetchone()
	db.close()
	if row:
		params['user_photo']=row[1]
		
		return template('./views/simplified_bmi.html',params) 
		
	return HTTPError(404, 'Page not found')

@route('/<directory>/<filename:re:.*\.(png|jpg|jpeg|gif)>')
def upload_file(directory, filename):
	if directory in ('images','upload'): 
		return static_file(filename, root=directory,mimetype='image/*')
	return HTTPError(404, 'Page not found')

run(host='localhost', port=8080, debug=True )