import os
import moviepy.editor as mp
import pandas as pd
from app.model import OrganismDetectionModel

def convert_to_mp4(filepath):
    """
    Convert the input video file to MP4 format if it is not already in MP4 format.
    
    Args:
    filepath (str): Path to the input video file.
    
    Returns:
    str: Path to the converted MP4 video file.
    """
    if not filepath.endswith('.mp4'):
        video = mp.VideoFileClip(filepath)
        new_filepath = os.path.splitext(filepath)[0] + '.mp4'
        video.write_videofile(new_filepath, codec='libx264')
        return new_filepath
    return filepath

def process_video(video_path, annotations_path, testing=False):
    """
    Process the video to detect organisms and compare the detections with annotations.
    
    Args:
    video_path (str): Path to the MP4 video file.
    annotations_path (str): Path to the CSV file containing annotations.
    testing (bool): Flag indicating if the mock model should be used.
    
    Returns:
    tuple: Lists of detections, annotated timecodes, and unannotated detections.
    """
    # Instantiate the model with the testing flag
    model = OrganismDetectionModel(testing=testing)
    
    # Run the model to detect organisms
    detections = model.detect(video_path)
    
    # Read the annotations from the CSV
    annotations = pd.read_csv(annotations_path)
    
    # Extract the relevant time column
    # Assuming the 'Start Date' column indicates the time of annotation
    annotations['Start Date'] = pd.to_datetime(annotations['Start Date'], errors='coerce')
    annotations = annotations.dropna(subset=['Start Date'])
    annotated_timecodes = annotations['Start Date'].apply(lambda x: x.timestamp()).tolist()
    
    # Find unannotated detections (detections not close to any annotated timecode)
    unannotated_detections = [
        tc for tc in detections
        if not any(abs(tc - a) < 1 for a in annotated_timecodes)
    ]
    
    return detections, annotated_timecodes, unannotated_detections
