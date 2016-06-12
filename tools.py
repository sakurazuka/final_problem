# coding=utf-8
import hashlib

def bmi(h,w):
	"""
	身長と体重からBMIを算出する
	"""
	height=h/100
	weight=w
	return weight / (height * height)

def sqlite2google(date):
	"""
	sqlite3で保存した日付のフォーマットを
	Google Chartsの日付のフォーマットに変換する
	"""
	[yyyy,mm,dd]=date.split('-',)
	#Google Chartでは月の値を１減算
	mm = str(int(mm)-1)
	if len(mm)==1:
		mm='0'+mm
	return ','.join([yyyy,mm,dd])

def sqlite2fmt(date,sep='/'):
	"""
	sqlite3で保存した日付のフォーマットを
	引数sepで渡された区切り文字に置換する
	"""
	[yyyy,mm,dd]=date.split('-',)
	if len(mm)==1:
		mm='0'+mm
	return sep.join([yyyy,mm,dd])
	
	
def getdigest(password,account_id):
	"""
	パスワードをハッシュにする
	"""
	salt='&sf)b4nv0(%I'
	#ソルトを加える
	digest=salt+str(account_id)+password
	#ストレッチを１０回実施
	for i in range(10):		
		digest = hashlib.sha256(digest).hexdigest()
	return digest
	
def is_password_ok(password, account_id, digest):
	"""
	パスワードの一致比較
	"""
	if digest == getdigest(password,account_id):
		return True
	else:
		return False
	
	
