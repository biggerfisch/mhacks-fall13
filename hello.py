from flask import Flask
app = Flask(__name__)

@app.route('/flask')
def goodbye_world():
	return 'I lied. Hello.'
  
if __name__ == '__main__':
	app.run()
