import os
import moviepy.editor as mp
import pandas as pd
from app.model import model

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

def process_video(video_path, annotations_path):
    """
    Process the video to detect organisms and compare the detections with annotations.
    
    Args:
    video_path (str): Path to the MP4 video file.
    annotations_path (str): Path to the CSV file containing annotations.
    
    Returns:
    tuple: Lists of detections, annotated timecodes, and unannotated detections.
    """
    # Run the model to detect organisms
    detections = model.detect(video_path)
    
    # Read the annotations
    annotations = pd.read_csv(annotations_path)
    
    # Get the list of annotated timecodes
    annotated_timecodes = annotations['timecode'].tolist()
    
    # Find unannotated detections
    unannotated_detections = [tc for tc in detections if not any(abs(tc - a) < 1 for a in annotated_timecodes)]
    
    return detections, annotated_timecodes, unannotated_detections
