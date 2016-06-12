# coding=utf-8
from bottle import route,template,run,static_file,request,post,abort,redirect,app,hook,response
from tools import bmi,sqlite2google,sqlite2fmt,getdigest,is_password_ok
from datetime import date
import bottle
import sqlite3, os.path, sys
sys.path.append(os.path.abspath('./libs'))
from beaker.middleware import SessionMiddleware
from gviz_api_py.gviz_api  import DataTable

#データベース
FILENAME = "./db/health.db"

session_options = {
    'session.type': 'file',
    'session.data_dir': './session/',
    #'session.type': 'memory',
    'session.auto': True,
}
app_middlware = SessionMiddleware(app(), session_options)

@hook('before_request')
def login_check():
	#HTTPリクエストを処理する直前にログイン済みかどうかチェックする
	app_session = request.environ.get('beaker.session')
	if not app_session.get('logged_in'):
		if request.urlparts.path not in  ('/login','/signup','/welcome','/info-notlogin.html','/favicon.ico'):
			if  not request.urlparts.path.startswith(('/js/','/css/','/images/')):
				return redirect('/login')
	return "Login OK"

@route('/')
def index():
	return redirect('/health-bmi')

@route('/login', 'GET')
def login_get():
	app_session = request.environ.get('beaker.session')
	if app_session.get('logged_in'):
		return redirect('/')

 	return template('./login.html')

@route('/login', 'POST')
def login_post():
	params={}
	request_params_key=['password','email']
	for key in request_params_key:
		params[key]=unicode(request.forms.get(key,''),'utf-8')
	db = sqlite3.connect(FILENAME).cursor()
	row=db.execute('SELECT * from users where email=?',  (params['email'],)).fetchone()
	
	if row:
		if not is_password_ok(params['password'],row[0],row[3]):
			params['status']='error'
			params['error_msg']='パスワードに誤りがあります。'
			return template('./login.html',params)		
		#セッションの作成
		app_session = request.environ.get('beaker.session')
		app_session['logged_in'] = True
		app_session['account_id'] = row[0]
		app_session['account_name'] = row[1]
	else:
		params['status']='error'
		params['error_msg']='アカウントが見つかりません。新規登録してください。'
		return template('./login.html',params)		

	return redirect('/health-bmi')

@route('/logout')
def logout():
	app_session = request.environ.get('beaker.session')
	if app_session.get('logged_in'):
 		app_session['logged_in'] = False
 
	return redirect('/login')

@route('/api/blood_pressure')
def blood_pressure_api():
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])
	db = sqlite3.connect(FILENAME ).cursor()
	rows=db.execute(
	'''SELECT * from blood_data WHERE account_id=? order by DATE(datetime)''',
	(params['account_id'],)
	).fetchall()
	db.close()
	description={'date':('date',u'日付'), 'high':('number',u'最高血圧'),
	'low':('number',u'最低血圧' ),'high_th':('number',u'最高血圧の正常ライン'),
	'low_th':('number',u'最低血圧の正常ライン')}
	data = []
	
	for row in rows:
		[yyyy,mm,dd]=map(int,row[1].split('-',))
		data.append({'date':date(yyyy,mm,dd),'high':row[2],
		'low':row[3],'high_th':140,'low_th':90})

	data_table = DataTable(description)
	data_table.LoadData(data)
	response.content_type = 'application/json; charset=utf-8'

	#apiの識別でreqIdは区別する数値を割り当てる。デフォルト値は０
	req_id=0
	if 'tqx' in request.query:
		tqx=request.query['tqx']
		if  tqx:
			req_id=dict([p.split(':') for p in tqx.split(';')]).get('reqId', req_id)
		
	return data_table.ToJSonResponse(columns_order=("date", "high", "low",'high_th','low_th'),req_id=req_id)
	
@route('/api/blood_pulse')
def blood_pulse_api():
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])
	db = sqlite3.connect(FILENAME ).cursor()
	rows=db.execute(
	'''SELECT * from blood_data WHERE account_id=? order by DATE(datetime)''',
	(params['account_id'],)
	).fetchall()
	db.close()
	description={'date':('date',u'日付'), 'pulse':('number',u'脈拍')}
	data = []
	
	for row in rows:
		[yyyy,mm,dd]=map(int,row[1].split('-',))
		data.append({'date':date(yyyy,mm,dd),'pulse':row[4]})

	data_table = DataTable(description)
	data_table.LoadData(data)
	response.content_type = 'application/json; charset=utf-8'

	#apiの識別でreqIdは区別する数値を割り当てる。デフォルト値は１
	req_id=1
	if 'tqx' in request.query:
		tqx=request.query['tqx']
		if  tqx:
			req_id=dict([p.split(':') for p in tqx.split(';')]).get('reqId', req_id)

	return data_table.ToJSonResponse(req_id=req_id)
                                
@route('/health-blood','GET')
def health_blood():
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])
	#直近に測定したデータを１行取得
	db = sqlite3.connect(FILENAME ).cursor()
	row=db.execute(
	'''SELECT * from blood_data WHERE account_id=? order by DATE(datetime) desc''',
	(params['account_id'],)
	).fetchone()
	db.close()

	if row:
		#直近のデータをテンプレートに埋め込むための変数
		params['latest_date']=sqlite2fmt(row[1],'/')
		params['latest_high_pressure']=str(row[2])
		params['latest_low_pressure']=str(row[3])
		params['latest_pulse']=str(row[4])

	return template('./views/health-blood.html',params)

@route('/health-blood','POST')
def health_blood_post():
	'''
	テンプレートのhtmlにグラフ描画のデータをAPIから取得し、
	javascriptでグラフ画像を作成するやり方
	'''
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])
	request_params_key=['datetime','high_pressure','low_pressure','pulse']
	# リクエストパラメータの値を取得
	for key in request_params_key:
		params[key]=unicode(request.forms.get(key,''),'utf-8')

	conn = sqlite3.connect(FILENAME)
	db=conn.cursor()
	db.execute('''INSERT INTO blood_data 
			(account_id
			,datetime 
			,high_pressure
			,low_pressure
			,pulse )
		VALUES(?,?,?,?,?)''',
			(params['account_id'], params['datetime'].replace('/','-')
			,params['high_pressure'],params['low_pressure'],params['pulse'],))
	conn.commit()
	db.close()
	return redirect('/health-blood')		

@route('/health-bmi', 'GET')
def health_bmi():
	'''
	テンプレートのhtmlにグラフ描画のデータを埋め込み、
	javascriptでグラフ画像を作成するやり方
	'''
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])
	db = sqlite3.connect(FILENAME ).cursor()
	rows=db.execute(
	'''SELECT * from bmi_data WHERE account_id=? order by DATE(date)''',
	(params['account_id'],)
	).fetchall()
	db.close()

	records=''
	weight_hist=''
	params['bmi']=''
	params['height']=''
	params['weight']=''
	params['latest_date']=''

	for row in rows:
		latest_bmi=str(bmi(float(row[2]),float(row[3])))
		date= sqlite2google(row[1])
		records=records+"[new Date("+date+"),25,"+latest_bmi+",22,18.5,],\n\t" 
		weight_hist=weight_hist+"[new Date("+date+"),"+str(row[3])+",],\n\t"
		params['bmi']=latest_bmi
		params['height']=str(row[2])
		params['weight']=str(row[3])
		params['latest_date']=sqlite2fmt(row[1],'/')

	if len(records)>0:	
		params["records"]=records

	if len(weight_hist)>0:	
		params["weight_hist"]=weight_hist
		
 	return template('./views/health-bmi.html', params)

@route('/health-bmi','POST')
def health_bmi_post():
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])
	request_params_key=['date','weight','height',]
	# リクエストパラメータの値を取得
	for key in request_params_key:
		params[key]=unicode(request.forms.get(key,''),'utf-8')

	conn = sqlite3.connect(FILENAME)
	db=conn.cursor()
	db.execute('''INSERT INTO bmi_data 
			(account_id
			,date 
			,height 
			,weight)
		VALUES(?,?,?,?)''',
			(params['account_id'], params['date'].replace('/','-')
			,params['height'], params['weight'],))
	conn.commit()
	db.close()
	return redirect('/health-bmi')		

@route('/password_settings','GET')
def password_settings():
	app_session = request.environ.get('beaker.session')
	db_params=read_settings(app_session['account_id'])
	params={'account_name':db_params['account_name']}
	
	return template('./views/password_settings.html',params)

@route('/password_settings','POST')
def password_settings_post():
	app_session = request.environ.get('beaker.session')
	db_params=read_settings(app_session['account_id'])
	params={'account_name':db_params['account_name']}
	
	request_params_key=['current_password','password',]
	for key in request_params_key:
		params[key]=unicode(request.forms.get(key,''),'utf-8')

	is_ok = is_password_ok(params['current_password'], app_session['account_id'], db_params['password'])
	if not is_ok:
			params['status']='error'
			params['error_msg']='パスワードに誤りがあります。'
			return template('./views/password_settings.html', params)		
	
    #ハッシュ化したパスワードをsqlite3に保存
	hash_password=getdigest(params['password'],app_session['account_id'])
	conn = sqlite3.connect(FILENAME)
	db=conn.cursor()
	db.execute('''UPDATE users 
		SET password = ?
		WHERE account_id=?''',
			(hash_password,app_session['account_id'],))
	conn.commit()
	db.close()
	
	#更新成功したのでパスワードを初期化
	for key in request_params_key:
		del params[key]

	params['status']='success'

	return template('./views/password_settings.html',params)

@route('/settings','GET')
def settings():
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])

	return template('./views/settings.html',params)

@route('/settings','POST')
def settings_post():
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])
	
	request_params_key=['account_name','email','serial','birthday']
	# リクエストパラメータの値を取得
	for key in request_params_key:
		params[key]=unicode(request.forms.get(key,''),'utf-8')

    #ファイルデータを取得
	photo=request.files.get('photo')

	if photo and photo.filename and photo.filename != '':
		name,ext = os.path.splitext(photo.filename)
		if ext not in ( '.png', '.jpg', '.jpeg', 'gif' ):
			params['status']='error'
			params['error_msg']='画像ファイルを認識できませんでした。'
			return  template('./views/settings.html', params)
		photo.save('./upload',overwrite=True)
		params['user_photo']='./upload/'+photo.filename
		
    #リクエストパラメータの変数名と値をsqlite3に保存
	conn = sqlite3.connect(FILENAME)
	db=conn.cursor()
	db.execute('''UPDATE users 
		SET account_name= ? 
			,user_photo = ?
			,email = ?
			,serial = ?
			,birthday = ?
		WHERE account_id=?''',
			(params['account_name'], params['user_photo']
			,params['email'], params['serial'],params['birthday']
			,params['account_id'],))
	conn.commit()
	db.close()

	#更新完了
	params['status']='success'
	return template('./views/settings.html', params)	

'''
ディスクに保存した値を読み込む関数
'''
def read_settings(account_id):
	params={}
	#リクエストパラメータの変数名と値をdiskから読み込む
	db = sqlite3.connect(FILENAME).cursor()
	row=db.execute('SELECT * from users where account_id=?', (account_id,)).fetchone()

	if row:
		#初期データの作成
		params['account_id'] = row[0]
		params['account_name'] = row[1]
		params['email']=row[2]
		params['password']=row[3]
		params['serial']=row[4]
		params['birthday']=row[5]
		params['user_photo']=row[6]

	db.close()	
	return params

@route('/signup','GET')
def signup():
	return template('./views/signup.html')

@route('/signup','POST')
def signup_post():
	params={}
	#登録処理
	request_params_key=['account_name','password','email','serial','birthday']
	# リクエストパラメータの値を取得
	for key in request_params_key:
		params[key]=unicode(request.forms.get(key,''),'utf-8')
    #ファイルデータを取得
	photo=request.files.get('photo')
	
	if photo and photo.filename and photo.filename != '':
		name,ext = os.path.splitext(photo.filename)
		if ext not in ( '.png', '.jpg', '.jpeg','.gif' ):
			params['status']='error'
			params['error_msg']='画像ファイルを認識できませんでした。'
			return  template('./views/signup.html', params)
		photo.save('./upload',overwrite=True)
		params['user_photo']='./upload/'+photo.filename
	else:
		params['user_photo']=''
		
    #リクエストパラメータの変数名と値をsqlite3に保存
	conn = sqlite3.connect(FILENAME)
	db=conn.cursor()
	db.execute('''INSERT INTO users 
			(account_name 
			,user_photo 
			,password 
			,email 
			,serial 
			,birthday )
		VALUES(?,?,?,?,?,?)''',
			(params['account_name'], params['user_photo']
			,params['password'], params['email'], params['serial']
			,params['birthday'],))
	conn.commit()

	# ハッシュパスワードへUPDATEするため、新規発行したaccount_id取得
	row=db.execute('SELECT * from users where email=? and password=?', 
	(params['email'],params['password'],)).fetchone()

	#UPDATE実行
	db.execute('''UPDATE users SET password = ?
		WHERE account_id=?''',
			( getdigest(params['password'],row[0]),row[0],))

	conn.commit()
	
	db.close()

	return template('./views/welcome.html',
	account_name=params['account_name'])

@route('/help.html')
def help_page():
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])
	return template('./views/help.html', params)

@route('/info.html')
def info_page():
	app_session = request.environ.get('beaker.session')
	params=read_settings(app_session['account_id'])
	return template('./views/info.html', params)

@route('/info-notlogin.html')
def infonotlogin_page():
	return template('./views/info-notlogin.html')

@route('/css/<filename:re:.*\.css>')
def css_file(filename):
        return static_file(filename, root='css',mimetype='text/css')

@route('/js/<filename:re:.*\.js>')
def js_file(filename):
	return static_file(filename, root='js',mimetype='text/javascript')

@route('/<directory>/<filename:re:.*\.(png|jpg|jpeg|gif)>')
def upload_file(directory, filename):
	if directory in ('images','upload'): 
		return static_file(filename, root=directory,mimetype='image/*')
	else:
		abort(404,"Not Found")

run(host='localhost', port=8080, debug=True, app=app_middlware )
