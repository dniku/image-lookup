import os, json
import logging
import hashlib
from flask import Flask, render_template, request, redirect, url_for, \
	send_from_directory

# TODO: config logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['DB_PATH'] = 'answers.json'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
	os.makedirs(app.config['UPLOAD_FOLDER'])

if os.path.exists(app.config['DB_PATH']):
	with open(app.config['DB_PATH'], 'r') as f:
		answers = json.load(f)
else:
	answers = {}

def save_answers():
	with open(app.config['DB_PATH'], 'w') as f:
		json.dump(answers, f, sort_keys=True, indent=4)

def get_answer(imhash):
	return answers.get(imhash, '')

def update_answer(imhash, answer):
	if answer:
		answers[imhash] = answer
	else:
		if imhash in answers:
			del answers[imhash]
	save_answers()

@app.route('/')
def index():
	return render_template('index.html')

def imhash2path(imhash):
	return imhash + '.png'

@app.route('/upload', methods=['POST'])
def upload():
	mime2ext = {
		'image/png': '.png',
		# 'image/jpeg': '.jpg'
	}

	ext = mime2ext.get(request.mimetype)

	if ext:
		if request.data:
			imdata = request.data
			imhash = hashlib.md5(imdata).hexdigest()
			imname = imhash + ext
			impath = os.path.join(app.config['UPLOAD_FOLDER'], imname)
			if not os.path.exists(impath):
				logging.info("New image: %s" % imname)
				with open(impath, 'wb') as f:
					f.write(imdata)
			else:
				logging.info("Old image: %s" % imname)
			return url_for('results', imhash=imhash)
		else:
			logging.warning("No request data!")
	else:
		logging.warning("Unrecognized mimetype: %s" % request.mimetype)

	return url_for('index')

@app.route('/image/<imhash>')
def image(imhash):
	return send_from_directory(app.config['UPLOAD_FOLDER'], imhash2path(imhash))

@app.route('/results/<imhash>')
def results(imhash):
	answer = get_answer(imhash)
	return render_template('results.html', imhash=imhash, answer=answer)

@app.route('/update', methods=['POST'])
def update():
	imhash = request.form['imhash']
	answer = request.form['answer']
	update_answer(imhash, answer)
	return redirect(url_for('results', imhash=imhash))

if __name__ == '__main__':
	app.run(
			host='0.0.0.0',
			port=8080,
			debug=False
	)
