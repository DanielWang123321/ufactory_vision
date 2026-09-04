import sys
import numpy as np
import depthai as dai
import cv2
import math
from datetime import timedelta

RGB_SOCKET = dai.CameraBoardSocket.CAM_A
LEFT_SOCKET = dai.CameraBoardSocket.CAM_B
RIGHT_SOCKET = dai.CameraBoardSocket.CAM_C
ALIGN_SOCKET = RIGHT_SOCKET

COLOR_RESOLUTION = dai.ColorCameraProperties.SensorResolution.THE_1080_P
LEFT_RIGHT_RESOLUTION = dai.MonoCameraProperties.SensorResolution.THE_400_P

ISP_SCALE = 3


class DepthAiCamera(object):
    def __init__(self, width=640, height=400, fps=30, disable_rgb=False):
        np.set_printoptions(threshold=sys.maxsize) # print all data in an image
        # Closer-in minimum depth, disparity range is doubled (from 95 to 190):
        extended_disparity = True
        # Better accuracy for longer distance, fractional disparity 32-levels:
        subpixel = False
        # Better handling for occlusions:
        lr_check = True

        self.width = width
        self.height = height
        self.disable_rgb = disable_rgb

        self.device = dai.Device()

        self.calibration = self.device.readCalibration2()

        self.rgbIntrinsics = None

        self.rgbDistortion = self.calibration.getDistortionCoefficients(RGB_SOCKET)
        self.rightDistortion = self.calibration.getDistortionCoefficients(RIGHT_SOCKET)
        distortionModel = self.calibration.getDistortionModel(RGB_SOCKET)
        if distortionModel != dai.CameraModel.Perspective:
            raise RuntimeError("Unsupported distortion model for RGB camera. This example supports only Perspective model.")

        # Create pipeline
        pipeline = dai.Pipeline()

        # Define sources and outputs
        cam_rgb = pipeline.create(dai.node.ColorCamera)
        cam_rgb.setBoardSocket(RGB_SOCKET)
        cam_rgb.setResolution(COLOR_RESOLUTION)
        cam_rgb.setFps(fps)
        cam_rgb.setIspScale(1, ISP_SCALE)

        left = pipeline.create(dai.node.MonoCamera)
        left.setResolution(LEFT_RIGHT_RESOLUTION) # 640*400
        left.setFps(fps)
        left.setCamera("left")

        right = pipeline.create(dai.node.MonoCamera)
        right.setResolution(LEFT_RIGHT_RESOLUTION) # 640*400
        right.setFps(fps)
        right.setCamera("right")

        stereo = pipeline.create(dai.node.StereoDepth)
        sync = pipeline.create(dai.node.Sync)

        out = pipeline.create(dai.node.XLinkOut)
        align = pipeline.create(dai.node.ImageAlign)

        # stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        stereo.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)
        stereo.setLeftRightCheck(lr_check)
        stereo.setExtendedDisparity(extended_disparity)
        stereo.setSubpixel(subpixel)
        stereo.setDepthAlign(ALIGN_SOCKET)

        out.setStreamName("out")

        sync.setSyncThreshold(timedelta(seconds=0.5 / fps))

        # Linking
        cam_rgb.isp.link(sync.inputs["rgb"])
        left.out.link(stereo.left)
        right.out.link(stereo.right)
        stereo.depth.link(align.input)
        align.outputAligned.link(sync.inputs["depth_aligned"])
        cam_rgb.isp.link(align.inputAlignTo)
        sync.out.link(out.input)

        self.device.startPipeline(pipeline)
        self.que_out = self.device.getOutputQueue(name="out", maxSize=4, blocking=False)

    def __exit__(self):
        self.device.close()

    def get_intrinsics(self, width=None, height=None):
        if width is None or height is None:
            color_frame, depth_frame = self.get_frames(force=True)
            rgb_intrinsics = self.calibration.getCameraIntrinsics(RGB_SOCKET, int(color_frame.shape[1]), int(color_frame.shape[0]))
            # left_intrinsics = self.calibration.getCameraIntrinsics(LEFT_SOCKET, int(depth_frame.shape[1]), int(depth_frame.shape[0]))
            right_intrinsics = self.calibration.getCameraIntrinsics(RIGHT_SOCKET, int(depth_frame.shape[1]), int(depth_frame.shape[0]))
        else:
            rgb_intrinsics = self.calibration.getCameraIntrinsics(RGB_SOCKET, width, height)
            # left_intrinsics = self.calibration.getCameraIntrinsics(LEFT_SOCKET, width, height)
            right_intrinsics = self.calibration.getCameraIntrinsics(RIGHT_SOCKET, width, height)

        return np.array(rgb_intrinsics), np.array(right_intrinsics)

    def get_frames(self, force=False):
        msg_group = self.que_out.get()
        if not self.disable_rgb or force:
            color_frame = msg_group["rgb"].getCvFrame()
        else:
            color_frame = None
        depth_frame = msg_group["depth_aligned"].getFrame()
        return color_frame, depth_frame
    
    def get_images(self):
        color_frame, depth_frame = self.get_frames()
        if color_frame is not None:
            if self.rgbIntrinsics is None:
                 self.rgbIntrinsics = self.calibration.getCameraIntrinsics(RGB_SOCKET, int(color_frame.shape[1]), int(color_frame.shape[0]))
            color_image = cv2.undistort(
                color_frame,
                np.array(self.rgbIntrinsics),
                np.array(self.rgbDistortion),
            )
        else:
            color_image = None
        depth_image = (np.asanyarray(depth_frame) * 0.001).astype(np.float32)
        depth_image[depth_image == 0] = math.nan
        return color_image, depth_image


if __name__ == '__main__':
    cam = DepthAiCamera()
    color_intrin, depth_intrin = cam.get_intrinsics()
    print(color_intrin)
    print(depth_intrin)

    fx = depth_intrin[0][0]
    fy = depth_intrin[1][1]
    cx = depth_intrin[0][2]
    cy = depth_intrin[1][2]
    print(fx, fy, cx, cy)

    while True:
        # color_image, depth_image = cam.get_frames()
        color_image, depth_image = cam.get_images()
        # print('COLOR:', color_image.shape, 'DEPTH:', depth_image.shape)
        if color_image is not None:
            cv2.imshow('COLOR', color_image) # 显示彩色图像
        cv2.imshow('DEPTH', depth_image) # 显示深度图像

        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cam.stop()
            break