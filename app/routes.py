import os
import time
import json
import pandas as pd
from io import StringIO
from flask import Flask, render_template, request, jsonify, send_file, current_app, send_from_directory, abort
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
from owl_highlighter import OWLHighlighter
import base64
from io import BytesIO

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mov', 'avi'}

# Initialize the highlighter
highlighter = OWLHighlighter(score_threshold=0.3)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to store detections (in a real application, use a database)
global_detections = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def convert_to_mp4(video_path):
    """
    Convert the input video file to MP4 format if it is not already in MP4 format.
    """
    if video_path.lower().endswith('.mp4'):
        return video_path
    
    mp4_video_path = os.path.splitext(video_path)[0] + '.mp4'
    
    video = VideoFileClip(video_path)
    video.write_videofile(mp4_video_path, codec='libx264', audio_codec='aac')
    video.close()
    
    return mp4_video_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'video' not in request.files or 'csv' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        video = request.files['video']
        csv_file = request.files['csv']

        if video.filename == '' or csv_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(video.filename):
            return jsonify({'error': 'Invalid video file type'}), 400

        # Save files
        video_filename = secure_filename(video.filename)
        csv_filename = secure_filename(csv_file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
        
        video.save(video_path)
        csv_file.save(csv_path)

        try:
            # Process video with OWLHighlighter
            result = highlighter.process_video(
                video_path=video_path,
                class_names=['organism']
            )

            # Process results
            processed_data = process_results(result, csv_path)
            
            # Store in global state
            global global_detections
            global_detections = processed_data['detections']

            return jsonify(processed_data)

        finally:
            # Cleanup
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(csv_path):
                os.remove(csv_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_results(result, csv_path):
    """Helper function to process OWLHighlighter results"""
    # Create timeline visualization
    timeline_path = os.path.join(app.config['UPLOAD_FOLDER'], 'timeline.png')
    highlighter.create_timeline(result, timeline_path)

    try:
        # Convert detections to JSON-serializable format
        detections = []
        for det in result.detections:
            buffered = BytesIO()
            det.image_patch.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            detection = {
                'id': len(detections) + 1,
                'time': det.timestamp,
                'description': det.label,
                'confidence': det.confidence,
                'image': img_str,
                'bbox': det.bbox,
                'frame_number': det.frame_number
            }
            detections.append(detection)

        # Read timeline image
        with open(timeline_path, 'rb') as f:
            timeline_base64 = base64.b64encode(f.read()).decode()

        # Process annotations
        annotations_df = pd.read_csv(csv_path)
        annotated_times = annotations_df['timecode'].tolist()

        # Split into annotated/unannotated
        annotated, unannotated = [], []
        for detection in detections:
            is_annotated = any(abs(detection['time'] - ann_time) < 1 
                             for ann_time in annotated_times)
            detection['is_annotated'] = is_annotated
            if is_annotated:
                annotated.append(detection)
            else:
                unannotated.append(detection)

        return {
            'video_info': {
                'name': result.video_name,
                'fps': result.fps,
                'frame_count': result.frame_count,
                'duration': result.duration
            },
            'detections': detections,
            'annotated': annotated,
            'unannotated': unannotated,
            'timeline_image': timeline_base64,
            'total_annotations': len(annotated_times),
            'total_annotated_detected': len(annotated),
            'total_unannotated_detected': len(unannotated)
        }

    finally:
        if os.path.exists(timeline_path):
            os.remove(timeline_path)

@app.route('/demo', methods=['GET'])
def demo():
    """Load and return demo data"""
    demo_data_path = os.path.join(app.config['UPLOAD_FOLDER'], 'demo', 'demo_detections.json')
    time.sleep(5)  # Simulate processing time

    with open(demo_data_path, 'r') as f:
        detections_data = json.load(f)
    
    global global_detections
    global_detections = detections_data['detections']

    return jsonify(detections_data)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    if filename.startswith('uploads/'):
        filename = filename[8:]

    base_dir = app.config['UPLOAD_FOLDER']
    full_path = os.path.join(base_dir, filename)
    app.logger.debug(f"Full path: {full_path}")

    if not os.path.exists(full_path):
        app.logger.debug(f"File not found: {full_path}")
        return abort(404)

    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)

    return send_from_directory(directory, filename)

@app.route('/reject_annotation', methods=['POST'])
def reject_annotation():
    data = request.json
    detection_id = data.get('id')
    
    global global_detections
    
    # Find the detection with the given id and mark it as rejected
    for detection in global_detections:
        if detection['id'] == detection_id:
            detection['rejected'] = True
            break
    
    return jsonify({
        'success': True,
        'message': f'Annotation with id {detection_id} rejected'
    })

@app.route('/edit_description', methods=['POST'])
def edit_description():
    data = request.json
    detection_id = data.get('id')
    new_description = data.get('newDescription')
    
    global global_detections
    
    # Find the detection with the given id and update its description
    for detection in global_detections:
        if detection['id'] == detection_id:
            detection['description'] = new_description
            detection['edited'] = True
            break
    
    return jsonify({
        'success': True,
        'message': f'Description for detection with id {detection_id} updated to "{new_description}"'
    })

@app.route('/get_updated_detections', methods=['GET'])
def get_updated_detections():
    global global_detections
    
    # Filter out rejected detections
    active_detections = [d for d in global_detections if not d.get('rejected', False)]
    
    annotated = [d for d in active_detections if d.get('is_annotated', False)]
    unannotated = [d for d in active_detections if not d.get('is_annotated', False)]
    
    return jsonify({
        'detections': active_detections,
        'annotated': annotated,
        'unannotated': unannotated,
        'total_annotations': len(annotated),
        'total_annotated_detected': len(annotated),
        'total_unannotated_detected': len(unannotated)
    })

@app.route('/download/<list_type>', methods=['GET'])
def download(list_type):
    global global_detections

    list_types = ['detections', 'annotated', 'unannotated']
    if list_type not in list_types:
        return jsonify({'error': 'Invalid list type'}), 400

    # Filter detections based on list_type
    if list_type == 'detections':
        data = global_detections
    elif list_type == 'annotated':
        data = [d for d in global_detections if d.get('is_annotated', False) and not d.get('rejected', False)]
    else:  # unannotated
        data = [d for d in global_detections if not d.get('is_annotated', False) and not d.get('rejected', False)]

    # Create a DataFrame
    df = pd.DataFrame(data)
    
    # Add columns to indicate if a detection was edited or rejected
    df['edited'] = df['edited'].fillna(False)
    df['rejected'] = df['rejected'].fillna(False)

    # Convert DataFrame to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # Send the CSV file
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        attachment_filename=f'{list_type}.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)