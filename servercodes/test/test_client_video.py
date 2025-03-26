#!/usr/bin/env python3
"""
ESP-LiveView 视频测试客户端
用于从视频中提取帧并上传到服务器，模拟ESP32S3实时拍摄功能

功能：
1. 从视频文件中提取帧
2. 按指定的时间间隔上传帧到服务器
3. 支持实时或加速模式
4. 显示上传进度和状态
"""

import requests
import argparse
import time
import os
import sys
import cv2
import tempfile
from datetime import datetime
import threading
from tqdm import tqdm  # 进度条库

class VideoFrameUploader:
    def __init__(self, server_url):
        """初始化上传器"""
        self.server_url = server_url
        # 去除URL末尾的斜杠（如果有）
        if self.server_url.endswith('/'):
            self.server_url = self.server_url[:-1]
        
        self.upload_url = f"{self.server_url}/upload"
        
        # 状态变量
        self.running = False
        self.frames_total = 0
        self.frames_uploaded = 0
        self.upload_errors = 0
    
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
    
    def upload_frame(self, frame):
        """上传单帧图像到服务器"""
        # 创建临时文件保存帧
        fd, temp_path = tempfile.mkstemp(suffix='.jpg')
        try:
            # 保存帧为JPEG
            cv2.imwrite(temp_path, frame)
            
            # 上传到服务器
            with open(temp_path, 'rb') as f:
                files = {'image': ('frame.jpg', f, 'image/jpeg')}
                response = requests.post(self.upload_url, files=files)
            
            # 检查响应
            if response.status_code == 200:
                self.frames_uploaded += 1
                return True
            else:
                self.upload_errors += 1
                return False
                
        except Exception as e:
            self.upload_errors += 1
            return False
        finally:
            # 删除临时文件
            os.close(fd)
            os.unlink(temp_path)
    
    def process_video(self, video_path, interval=1.0, realtime=True):
        """
        处理视频并上传帧
        
        参数:
            video_path: 视频文件路径
            interval: 上传间隔(秒)
            realtime: 是否以视频的实际速度上传
        """
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"✗ 无法打开视频文件: {video_path}")
            return False
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        print(f"视频信息:")
        print(f"- 分辨率: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
        print(f"- 帧率: {fps:.2f} fps")
        print(f"- 总帧数: {frame_count}")
        print(f"- 时长: {duration:.2f} 秒")
        
        # 计算要提取的帧
        frames_to_extract = []
        current_time = 0
        
        while current_time < duration:
            frame_number = int(current_time * fps)
            if frame_number < frame_count:
                frames_to_extract.append((frame_number, current_time))
            current_time += interval
        
        self.frames_total = len(frames_to_extract)
        print(f"将上传 {self.frames_total} 帧图像，间隔 {interval} 秒")
        
        # 设置运行状态
        self.running = True
        self.frames_uploaded = 0
        self.upload_errors = 0
        
        # 创建进度条
        progress_bar = tqdm(total=self.frames_total, desc="上传进度", unit="帧")
        
        # 开始提取和上传
        start_time = time.time()
        
        for i, (frame_number, timestamp) in enumerate(frames_to_extract):
            if not self.running:
                break
                
            # 设置视频位置
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            if not ret:
                print(f"✗ 无法读取帧 {frame_number}")
                self.upload_errors += 1
                continue
            
            # 上传帧
            upload_success = self.upload_frame(frame)
            
            # 更新进度条
            progress_bar.update(1)
            progress_bar.set_postfix({
                "成功": self.frames_uploaded,
                "错误": self.upload_errors,
                "时间点": f"{timestamp:.2f}s"
            })
            
            # 如果是实时模式，等待适当的时间
            if realtime and i < len(frames_to_extract) - 1:
                next_timestamp = frames_to_extract[i + 1][1]
                elapsed = time.time() - start_time
                wait_time = max(0, (next_timestamp - timestamp) - (elapsed - timestamp))
                
                if wait_time > 0:
                    time.sleep(wait_time)
        
        # 关闭进度条
        progress_bar.close()
        
        # 关闭视频
        cap.release()
        
        # 显示上传统计
        print("\n上传完成!")
        print(f"总帧数: {self.frames_total}")
        print(f"成功上传: {self.frames_uploaded}")
        print(f"上传失败: {self.upload_errors}")
        print(f"总用时: {time.time() - start_time:.2f} 秒")
        
        return self.frames_uploaded > 0
    
    def stop(self):
        """停止上传过程"""
        self.running = False

def main():
    parser = argparse.ArgumentParser(description='ESP-LiveView 视频测试客户端')
    parser.add_argument('--server', default='http://localhost:5002', help='服务器URL')
    parser.add_argument('--video', required=True, help='视频文件路径')
    parser.add_argument('--interval', type=float, default=1.0, help='上传帧的时间间隔(秒)')
    parser.add_argument('--realtime', action='store_true', help='以视频实际速度上传')
    parser.add_argument('--accelerate', type=float, default=1.0, help='加速倍数 (仅当--realtime未指定时有效)')
    
    args = parser.parse_args()
    
    # 初始化上传器
    uploader = VideoFrameUploader(args.server)
    
    # 测试服务器连接
    if not uploader.test_server_connection():
        sys.exit(1)
    
    # 处理视频
    try:
        uploader.process_video(
            args.video, 
            interval=args.interval,
            realtime=args.realtime
        )
    except KeyboardInterrupt:
        print("\n用户中断，正在停止...")
        uploader.stop()
        print("已停止")

if __name__ == "__main__":
    main()