from flask import Blueprint, send_from_directory, current_app
import os

home_bp = Blueprint('home', __name__)


@home_bp.route('/api/files/<path:filename>')
def serve_file(filename):
    from app.app_context import get_services
    svc = get_services()
    cache_dir = svc.config.get_value('core.cache_dir')
    photo_root = svc.config.get_value('core.photo_root_path')
    for directory in [cache_dir, photo_root]:
        if os.path.exists(os.path.join(directory, filename)):
            return send_from_directory(directory, filename)
    return "File not found", 404

frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')


@home_bp.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>图忆仓 - TuYiCang</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            .card { background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            a { color: #409eff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>图忆仓 (TuYiCang)</h1>
            <p>私有化本地相册知识库 - 支持文搜图+图搜图</p>
            <div class="card">
                <h2>欢迎使用</h2>
                <p>请配置前端目录或使用API进行交互。</p>
                <p>
                    <a href="/api/photos/status">查看API状态</a> |
                    <a href="/api/configs">查看配置</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    '''
