from flask import render_template, request, jsonify, send_file, current_app
from app import app
from app.utils import convert_to_mp4, process_video
from werkzeug.utils import secure_filename
import os
from app.model import OrganismDetectionModel

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    testing_mode = current_app.config.get('TESTING', False)
    if 'video' not in request.files or 'csv' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    video = request.files['video']
    csv_file = request.files['csv']

    if video.filename == '' or csv_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    video_filename = secure_filename(video.filename)
    csv_filename = secure_filename(csv_file.filename)

    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    video.save(video_path)
    csv_file.save(csv_path)

    mp4_video_path = convert_to_mp4(video_path)
    detections, annotated, unannotated = process_video(mp4_video_path, csv_path, testing=testing_mode)

    return jsonify({
        'detections': detections,
        'annotated': annotated,
        'unannotated': unannotated
    })

@app.route('/download/<list_type>', methods=['GET'])
def download(list_type):
    list_types = ['detections', 'annotated', 'unannotated']
    if list_type not in list_types:
        return jsonify({'error': 'Invalid list type'}), 400

    # Assuming the lists are stored in session or temporary files
    list_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{list_type}.csv")

    # Check if the file exists
    if not os.path.exists(list_file_path):
        return jsonify({'error': 'File not found'}), 404

    # Send the file for download
    return send_file(list_file_path, as_attachment=True)
