from flask import Flask, request, jsonify, render_template
app = Flask(__name__)

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/songs', methods = ['POST'])
def make_chords():
    if not request.json or not 'notes' in request.json:
        abort(400)
    derp = {
            'num_notes': len(request.json['notes'])
    }
    return jsonify( { 'herp': derp } ), 201

@app.route('/about/')
def about_page():
    return render_template('about.html')
    
if __name__ == '__main__':
    app.run(debug=True)
