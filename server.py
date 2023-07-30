from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/set_folder_path', methods=['POST'])
def set_folder_path():
    data = request.get_json()
    folder_path = data.get('folderPath')

    try:
        os.chdir(folder_path)
        return jsonify({'message': 'Percorso della cartella impostato con successo.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
