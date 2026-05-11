from http.server import BaseHTTPRequestHandler
import json
import subprocess
import tempfile
import os
import re

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query params manually (simple approach)
        url = None
        if '?' in self.path:
            query = self.path.split('?', 1)[1]
            for param in query.split('&'):
                if '=' in param:
                    key, val = param.split('=', 1)
                    if key == 'url':
                        url = val

        # CORS headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if not url:
            self.wfile.write(json.dumps({
                'error': 'URL parametresi gerekli. ?url=https://x.com/...'
            }, ensure_ascii=False).encode())
            return

        # Clean URL - extract status ID
        url = url.strip()
        
        try:
            # Use yt-dlp to extract video URL only (fast, no download)
            with tempfile.TemporaryDirectory() as tmpdir:
                result = subprocess.run(
                    ['yt-dlp', '--get-url', '--no-playlist', '--no-warnings',
                     '--socket-timeout', '10', url],
                    capture_output=True, text=True, timeout=25,
                    cwd=tmpdir
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr.strip() or 'Video bilgisi alınamadı'
                    # Try to extract useful error
                    if 'No video formats found' in error_msg:
                        error_msg = 'Bu tweette video bulunamadı'
                    elif 'private' in error_msg.lower() or 'protected' in error_msg.lower():
                        error_msg = 'Bu hesap gizli, videoya erişilemiyor'
                    elif 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
                        error_msg = 'Tweet bulunamadı veya silinmiş'
                    
                    self.wfile.write(json.dumps({
                        'error': error_msg
                    }, ensure_ascii=False).encode())
                    return
                
                video_url = result.stdout.strip()
                
                # Also get video info (title, duration, thumbnail)
                info_result = subprocess.run(
                    ['yt-dlp', '--dump-json', '--no-playlist', '--no-warnings',
                     '--socket-timeout', '5', url],
                    capture_output=True, text=True, timeout=10,
                    cwd=tmpdir
                )
                
                info = {}
                if info_result.returncode == 0:
                    try:
                        info = json.loads(info_result.stdout)
                    except:
                        pass
                
                self.wfile.write(json.dumps({
                    'success': True,
                    'url': video_url,
                    'title': info.get('title', 'X Videosu'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', ''),
                }, ensure_ascii=False).encode())
                
        except subprocess.TimeoutExpired:
            self.wfile.write(json.dumps({
                'error': 'Zaman aşımı — video çok büyük olabilir, tekrar dene'
            }, ensure_ascii=False).encode())
        except Exception as e:
            self.wfile.write(json.dumps({
                'error': f'Beklenmeyen hata: {str(e)}'
            }, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
