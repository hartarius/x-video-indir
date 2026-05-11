from http.server import BaseHTTPRequestHandler
import json, sys, io
from urllib.parse import unquote

HTML = r'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>X Video Indirici</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #0a0a0f; --card: #12121a; --border: #1e1e30; --text: #e4e4f0;
  --dim: #6b6b80; --accent: #1d9bf0; --accent-hover: #1a8cd8;
  --error: #ef4444; --success: #22c55e; --radius: 14px;
}
body {
  background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 2rem;
  background-image: radial-gradient(ellipse at 50% -30%, rgba(29,155,240,0.06) 0%, transparent 60%);
}
.container { width: 100%; max-width: 600px; text-align: center; }
.logo { font-size: 2.5rem; margin-bottom: 0.25rem; }
h1 { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.35rem; }
.subtitle { color: var(--dim); font-size: 0.9rem; margin-bottom: 2rem; }
.input-group {
  display: flex; gap: 0.5rem; background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 0.4rem; transition: border-color 0.2s;
}
.input-group:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(29,155,240,0.1); }
.input-group input {
  flex: 1; background: transparent; border: none; outline: none; color: var(--text);
  font-size: 0.95rem; padding: 0.75rem; font-family: inherit;
}
.input-group input::placeholder { color: var(--dim); }
.btn {
  background: var(--accent); color: #fff; border: none; border-radius: 10px;
  padding: 0.75rem 1.5rem; font-size: 0.9rem; font-weight: 600; cursor: pointer;
  transition: all 0.15s; white-space: nowrap; font-family: inherit;
}
.btn:hover { background: var(--accent-hover); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.result { margin-top: 1.5rem; display: none; }
.result.show { display: block; }
.result-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; text-align: left; }
.video-info { display: flex; gap: 1rem; align-items: flex-start; margin-bottom: 1rem; }
.video-thumb { width: 120px; height: 68px; border-radius: 8px; object-fit: cover; background: #1a1a2e; flex-shrink: 0; }
.video-meta { flex: 1; min-width: 0; }
.video-title { font-size: 0.9rem; font-weight: 600; line-height: 1.3; margin-bottom: 0.35rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.video-uploader { font-size: 0.8rem; color: var(--dim); }
.btn-download { display: flex; align-items: center; justify-content: center; gap: 0.5rem; width: 100%; background: var(--success); padding: 0.85rem; border-radius: 10px; font-size: 0.95rem; font-weight: 600; color: #fff; text-decoration: none; }
.btn-download:hover { background: #1ea34e; }
.spinner { display: none; width: 24px; height: 24px; border: 2.5px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading .spinner { display: inline-block; }
.loading .btn-text { display: none; }
.error-msg { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 10px; padding: 0.85rem; color: var(--error); font-size: 0.85rem; margin-top: 1rem; display: none; }
.error-msg.show { display: block; }
.toast { position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); background: var(--card); border: 1px solid var(--border); border-radius: 50px; padding: 0.75rem 1.5rem; font-size: 0.85rem; color: var(--text); box-shadow: 0 10px 40px rgba(0,0,0,0.5); opacity: 0; pointer-events: none; transition: opacity 0.3s; z-index: 100; }
.toast.show { opacity: 1; }
.footer { margin-top: 2rem; font-size: 0.75rem; color: var(--dim); opacity: 0.6; }
.footer a { color: var(--dim); text-decoration: none; }
@media (max-width: 480px) {
  body { padding: 1.25rem; }
  h1 { font-size: 1.4rem; }
  .input-group { flex-direction: column; }
  .btn { width: 100%; padding: 0.85rem; }
  .video-info { flex-direction: column; }
  .video-thumb { width: 100%; height: auto; aspect-ratio: 16/9; }
}
</style>
</head>
<body>
<div class="container">
  <div class="logo">⬇️</div>
  <h1>X Video Indirici</h1>
  <p class="subtitle">Tweet linkini yapistir, indir</p>
  <div class="input-group">
    <input id="urlInput" placeholder="https://x.com/kullanici/status/123..." autocomplete="off" autofocus>
    <button class="btn" id="fetchBtn" onclick="fetchVideo()"><span class="btn-text">Indir</span><span class="spinner"></span></button>
  </div>
  <div class="error-msg" id="error"></div>
  <div class="result" id="result">
    <div class="result-card">
      <div class="video-info">
        <img class="video-thumb" id="thumb" src="">
        <div class="video-meta">
          <div class="video-title" id="title"></div>
          <div class="video-uploader" id="uploader"></div>
        </div>
      </div>
      <a class="btn-download" id="downloadBtn" href="#" target="_blank">⬇️ Videoyu Indir</a>
    </div>
  </div>
  <div class="footer">yt-dlp gucuyle · Vercel · <a href="https://github.com/hartarius/x-video-indir" target="_blank">GitHub</a></div>
</div>
<div class="toast" id="toast"></div>
<script>
const API = '/api';
function showError(msg) { const e=document.getElementById('error'); e.textContent=msg; e.classList.add('show'); document.getElementById('result').classList.remove('show'); }
function hideError() { document.getElementById('error').classList.remove('show'); }
function showToast(msg) { const t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),2500); }
async function fetchVideo() {
  const input=document.getElementById('urlInput'), btn=document.getElementById('fetchBtn'), url=input.value.trim();
  if(!url) { showError('Tweet linkini yapistir'); return; }
  if(!url.includes('x.com/')&&!url.includes('twitter.com/')) { showError('Gecerli bir X/Twitter linki degil'); return; }
  hideError(); document.getElementById('result').classList.remove('show'); btn.classList.add('loading'); btn.disabled=true;
  try {
    const res=await fetch(API+'?url='+encodeURIComponent(url)), data=await res.json();
    if(data.error) { showError(data.error); return; }
    if(data.success) {
      document.getElementById('title').textContent=data.title||'X Videosu';
      document.getElementById('uploader').textContent=data.uploader?'@'+data.uploader:'';
      document.getElementById('thumb').src=data.thumbnail||'';
      document.getElementById('downloadBtn').href=data.url;
      document.getElementById('result').classList.add('show'); showToast('✅ Video hazir!');
    }
  } catch(err) { showError('Baglanti hatasi, tekrar dene'); }
  finally { btn.classList.remove('loading'); btn.disabled=false; }
}
document.getElementById('urlInput').addEventListener('keydown',function(e){if(e.key==='Enter')fetchVideo();});
document.getElementById('urlInput').addEventListener('focus',async function(){if(!this.value){try{const text=await navigator.clipboard.readText();if(text.includes('x.com/')||text.includes('twitter.com/')){this.value=text;showToast('📋 Link panodan alindi');} }catch{}}});
</script>
</body>
</html>'''

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
            return
        
        url = None
        if '?' in self.path:
            query = self.path.split('?', 1)[1]
            for param in query.split('&'):
                if '=' in param:
                    key, val = param.split('=', 1)
                    if key == 'url':
                        url = val

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if not url:
            self.wfile.write(json.dumps({'error': 'URL parametresi gerekli. ?url=https://x.com/...'}, ensure_ascii=False).encode('utf-8'))
            return

        url = url.strip()
        url = unquote(url)  # Decode URL encoding from Vercel routing
        try:
            import yt_dlp
            
            opts = {
                'quiet': True, 'no_warnings': True, 'no_color': True,
                'socket_timeout': 10, 'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    self.wfile.write(json.dumps({'error': 'Video bilgisi alinamadi'}, ensure_ascii=False).encode('utf-8'))
                    return
                
                video_url = info.get('url', '')
                if not video_url and 'formats' in info:
                    for fmt in info['formats']:
                        if fmt.get('url'):
                            video_url = fmt['url']
                            break
                
                if not video_url:
                    self.wfile.write(json.dumps({'error': 'Video URL bulunamadi'}, ensure_ascii=False).encode('utf-8'))
                    return
                
                self.wfile.write(json.dumps({
                    'success': True, 'url': video_url,
                    'title': info.get('title', 'X Videosu'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', ''),
                }, ensure_ascii=False).encode('utf-8'))
                
        except Exception as e:
            self.wfile.write(json.dumps({'error': f'Hata: {str(e)}'}, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
