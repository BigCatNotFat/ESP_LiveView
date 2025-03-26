from flask import Flask, request, render_template, jsonify, send_from_directory
import os
from datetime import datetime
import base64

app = Flask(__name__)

# 设置图片保存目录
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 最新图片的文件名和时间戳
latest_image = {
    'filename': None,
    'timestamp': None
}

@app.route('/')
def index():
    """提供网页界面"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """处理来自ESP32S3的图片上传"""
    try:
        # 检查请求中是否有图片数据
        if 'image' not in request.files and 'image' not in request.form:
            return jsonify({'error': 'No image data found'}), 400
        
        if 'image' in request.files:
            # 处理二进制图片上传
            image_file = request.files['image']
            if image_file.filename == '':
                return jsonify({'error': 'No image selected'}), 400
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.jpg"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # 保存图片
            image_file.save(filepath)
        else:
            # 处理Base64编码的图片
            image_data = request.form['image']
            
            # 检查是否有Base64前缀，如果有则去除
            if ',' in image_data:
                image_data = image_data.split(',')[1]
                
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.jpg"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # 解码Base64并保存图片
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(image_data))
        
        # 更新最新图片信息
        latest_image['filename'] = filename
        latest_image['timestamp'] = timestamp
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'timestamp': timestamp
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/latest')
def get_latest_image():
    """获取最新上传的图片信息"""
    if latest_image['filename']:
        return jsonify({
            'filename': latest_image['filename'],
            'timestamp': latest_image['timestamp'],
            'url': f"/images/{latest_image['filename']}"
        })
    else:
        return jsonify({'error': 'No image uploaded yet'}), 404

@app.route('/images/<filename>')
def get_image(filename):
    """提供图片文件"""
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    # 在生产环境中，您应该使用适当的WSGI服务器如Gunicorn
    # 这里使用Flask的开发服务器并监听所有网络接口
    app.run(host='0.0.0.0', port=5002, debug=True)