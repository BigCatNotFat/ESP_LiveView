#!/usr/bin/env python3
"""
ESP-LiveView 测试客户端
用于测试Flask图片上传和显示接口

功能：
1. 上传本地图片到服务器（二进制文件方式）
2. 上传本地图片到服务器（Base64编码方式）
3. 获取最新上传的图片信息
4. 下载并显示最新图片
5. 模拟ESP32S3定时上传图片
"""

import requests
import base64
import argparse
import time
import os
import sys
from datetime import datetime
import json
from PIL import Image
from io import BytesIO

class ESPLiveViewClient:
    def __init__(self, server_url):
        """初始化客户端"""
        self.server_url = server_url
        # 去除URL末尾的斜杠（如果有）
        if self.server_url.endswith('/'):
            self.server_url = self.server_url[:-1]
        
        self.upload_url = f"{self.server_url}/upload"
        self.latest_url = f"{self.server_url}/latest"
        self.images_url = f"{self.server_url}/images"
    
    def test_server_connection(self):
        """测试服务器连接"""
        try:
            response = requests.get(self.server_url, timeout=5)
            if response.status_code == 200:
                print(f"✓ 服务器连接成功: {self.server_url}")
                return True
            else:
                print(f"✗ 服务器返回错误状态码: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ 无法连接到服务器: {e}")
            return False
    
    def upload_image_binary(self, image_path):
        """使用二进制文件上传方式（multipart/form-data）"""
        if not os.path.exists(image_path):
            print(f"✗ 文件不存在: {image_path}")
            return None
        
        try:
            print(f"正在上传图片: {image_path}")
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
                response = requests.post(self.upload_url, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 上传成功! 文件名: {result.get('filename')}")
                return result
            else:
                print(f"✗ 上传失败: HTTP {response.status_code}")
                try:
                    print(response.json())
                except:
                    print(response.text)
                return None
        except Exception as e:
            print(f"✗ 上传过程中出错: {e}")
            return None
    
    def upload_image_base64(self, image_path):
        """使用Base64编码上传方式"""
        if not os.path.exists(image_path):
            print(f"✗ 文件不存在: {image_path}")
            return None
        
        try:
            print(f"正在以Base64编码上传图片: {image_path}")
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
            
            payload = {'image': base64_data}
            response = requests.post(self.upload_url, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Base64上传成功! 文件名: {result.get('filename')}")
                return result
            else:
                print(f"✗ Base64上传失败: HTTP {response.status_code}")
                try:
                    print(response.json())
                except:
                    print(response.text)
                return None
        except Exception as e:
            print(f"✗ Base64上传过程中出错: {e}")
            return None
    
    def get_latest_image_info(self):
        """获取最新图片信息"""
        try:
            print("正在获取最新图片信息...")
            response = requests.get(self.latest_url)
            
            if response.status_code == 200:
                info = response.json()
                print(f"✓ 最新图片: {info.get('filename')}")
                print(f"  时间戳: {info.get('timestamp')}")
                print(f"  URL: {info.get('url')}")
                return info
            elif response.status_code == 404:
                print("✗ 服务器上没有图片")
                return None
            else:
                print(f"✗ 获取最新图片信息失败: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"✗ 获取最新图片信息出错: {e}")
            return None
    
    def download_and_show_image(self, image_url=None):
        """下载并显示图片"""
        if image_url is None:
            # 如果未提供URL，先获取最新图片信息
            info = self.get_latest_image_info()
            if info is None:
                return False
            image_url = f"{self.server_url}{info.get('url')}"
        
        try:
            print(f"正在下载图片: {image_url}")
            response = requests.get(image_url)
            
            if response.status_code == 200:
                # 将图片保存到临时文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"downloaded_{timestamp}.jpg"
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"✓ 图片已下载并保存为: {filename}")
                
                # 尝试显示图片（如果在支持GUI的环境中）
                try:
                    img = Image.open(BytesIO(response.content))
                    img.show()
                    print("✓ 图片已打开查看")
                except Exception as e:
                    print(f"✗ 无法显示图片: {e}")
                
                return True
            else:
                print(f"✗ 下载图片失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 下载图片出错: {e}")
            return False
    
    def simulate_esp32s3(self, image_path, interval=10, count=3):
        """模拟ESP32S3定时上传图片"""
        if not os.path.exists(image_path):
            print(f"✗ 文件不存在: {image_path}")
            return False
        
        print(f"模拟ESP32S3，每{interval}秒上传一次图片，共{count}次")
        for i in range(count):
            print(f"\n[{i+1}/{count}] 上传周期开始")
            result = self.upload_image_binary(image_path)
            if result:
                print(f"上传完成，等待{interval}秒...")
                if i < count - 1:  # 最后一次不需要等待
                    time.sleep(interval)
            else:
                print("上传失败，停止模拟")
                return False
        
        print("\n模拟完成!")
        return True

def main():
    parser = argparse.ArgumentParser(description='ESP-LiveView 测试客户端')
    parser.add_argument('--server', default='http://localhost:5000', help='服务器URL')
    parser.add_argument('--mode', choices=['upload', 'upload-base64', 'get-latest', 'download', 'simulate'], 
                       default='upload', help='操作模式')
    parser.add_argument('--image', help='要上传的图片路径')
    parser.add_argument('--interval', type=int, default=10, help='模拟ESP32S3上传间隔(秒)')
    parser.add_argument('--count', type=int, default=3, help='模拟ESP32S3上传次数')
    
    args = parser.parse_args()
    
    client = ESPLiveViewClient(args.server)
    
    # 测试服务器连接
    if not client.test_server_connection():
        sys.exit(1)
    
    # 根据模式执行不同操作
    if args.mode == 'upload':
        if not args.image:
            print("错误: 上传模式需要指定图片路径 (--image)")
            sys.exit(1)
        client.upload_image_binary(args.image)
    
    elif args.mode == 'upload-base64':
        if not args.image:
            print("错误: Base64上传模式需要指定图片路径 (--image)")
            sys.exit(1)
        client.upload_image_base64(args.image)
    
    elif args.mode == 'get-latest':
        client.get_latest_image_info()
    
    elif args.mode == 'download':
        client.download_and_show_image()
    
    elif args.mode == 'simulate':
        if not args.image:
            print("错误: 模拟ESP32S3模式需要指定图片路径 (--image)")
            sys.exit(1)
        client.simulate_esp32s3(args.image, args.interval, args.count)

if __name__ == "__main__":
    main()