from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os
import glob
import subprocess
from scraper import scrape_data

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    search = request.form.get('search')
    total = request.form.get('total', type=int)
    filename = scrape_data(search, total)
    return jsonify({'filename': filename})

@app.route('/files', methods=['GET'])
def list_files():
    files = glob.glob('output/*')
    return jsonify(files)

@app.route('/delete', methods=['POST'])
def delete_file():
    filename = request.form.get('filename')
    try:
        os.remove(filename)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/refresh', methods=['POST'])
def refresh_data():
    search = request.form.get('search')
    total = request.form.get('total', type=int)
    filename = scrape_data(search, total)
    return jsonify({'filename': filename})

def scrape_data(search, total):
    result = subprocess.run(['python3', 'scraper.py', '-s', search, '-t', str(total)], capture_output=True, text=True)
    # Assumption: The scraper script prints the output file name as the last line of its output
    filename = result.stdout.strip().split('\n')[-1]
    return filename

if __name__ == "__main__":
    socketio.run(app, debug=True)
