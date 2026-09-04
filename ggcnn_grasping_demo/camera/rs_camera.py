import math
import numpy as np
import pyrealsense2 as rs


class RealSenseCamera(object):
    def __init__(self, width=640, height=480, fps=30):
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
        self.profile = self.pipeline.start(self.config)
        self.align = rs.align(rs.stream.color)  # 与color流对齐
    
    def stop(self):
        self.pipeline.stop()
    
    def get_frames(self, align=False):
        frames = self.pipeline.wait_for_frames()  # 等待获取图像帧
        if align:
            return self.align.process(frames)  # 获取对齐帧
        return frames

    def get_intrinsics(self, align=False):
        frames = self.get_frames(align=align)
        color_frame = frames.get_color_frame()  # 获取color帧
        aligned_depth_frame = frames.get_depth_frame()  # 获取depth帧
        color_intrinsics = color_frame.profile.as_video_stream_profile().intrinsics  # 获取相机内参
        depth_intrinsics = aligned_depth_frame.profile.as_video_stream_profile().intrinsics  # 获取深度参数（像素坐标系转相机坐标系会用到）
        return color_intrinsics, depth_intrinsics

    def get_images(self, align=False):
        frames = self.get_frames(align=align)
        depth_frame = frames.get_depth_frame()  # 获取depth帧
        color_frame = frames.get_color_frame()  # 获取color帧
        depth_image = np.asanyarray(depth_frame.get_data())  # 深度图（默认16位）

        # convert metric
        depth_image = (depth_image * 0.001).astype(np.float32)
        depth_image[depth_image == 0] = math.nan
        
        # depth_image_8bit = cv2.convertScaleAbs(depth_image, alpha=0.03)  # 深度图（8位）
        # depth_image_3d = np.dstack((depth_image_8bit, depth_image_8bit, depth_image_8bit))  # 3通道深度图
        color_image = np.asanyarray(color_frame.get_data())  # RGB图
        return color_image, depth_image


if __name__ == '__main__':
    import cv2
    cam = RealSenseCamera()
    color_intrin, depth_intrin = cam.get_intrinsics()
    print(color_intrin)
    print(depth_intrin)
    fx = depth_intrin.fx
    fy = depth_intrin.fy
    cx = depth_intrin.ppx
    cy = depth_intrin.ppy
    print(fx, fy, cx, cy)
    
    while True:
        color_image, depth_image = cam.get_images()

        cv2.imshow('COLOR', color_image) # 显示彩色图像
        cv2.imshow('DEPTH', depth_image) # 显示深度图像

        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cam.stop()
            break