import sys
import cv2
import time
import numpy as np
from camera.rs_camera import RealSenseCamera
from grasp.ggcnn_torch import TorchGGCNN
from grasp.robot_grasp import RobotGrasp
from queue import Queue

WIN_NAME = 'RealSense'
WIDTH = 640
HEIGHT = 480
# rgb camera calibration result
EULER_EEF_TO_COLOR_OPT = [0.067052239, -0.0311387575, 0.021611456, -0.004202176, -0.00848499, 1.5898775] # xyzrpy meters_rad
EULER_COLOR_TO_DEPTH_OPT = [0.015, 0, 0, 0, 0, 0]
GGCNN_IN_THREAD = False

# The range of motion of the robot grasping
# If it exceeds the range, it will return to the initial detection position.
GRASPING_RANGE = [180, 600, -200, 200] # [x_min, x_max, y_min, y_max]

# initial detection position
DETECT_XYZ = [300, 0, 400] # [x, y, z]

# The distance between the gripping point of the robot grasping and the end of the robot arm flange
# The value needs to be fine-tuned according to the actual situation.
GRIPPER_Z_MM = 150 # mm

# release grasping pos
RELEASE_XYZ = [400, 400, 270]

# min z for grasping
GRASPING_MIN_Z = 175

def main():
    if len(sys.argv) < 2:
        print('Usage: {} {{robot_ip}}'.format(sys.argv[0]))
        exit(1)
    
    robot_ip = sys.argv[1]


    depth_img_que = Queue(1)
    ggcnn_cmd_que = Queue(1)
    
    camera = RealSenseCamera(width=WIDTH, height=HEIGHT)
    _, depth_intrin = camera.get_intrinsics()
    ggcnn = TorchGGCNN(depth_img_que, ggcnn_cmd_que, depth_intrin, width=WIDTH, height=HEIGHT, run_in_thread=GGCNN_IN_THREAD)
    fx = depth_intrin.fx
    fy = depth_intrin.fy
    cx = depth_intrin.ppx
    cy = depth_intrin.ppy
    time.sleep(3)
    grasp = RobotGrasp(robot_ip, ggcnn_cmd_que, EULER_EEF_TO_COLOR_OPT, EULER_COLOR_TO_DEPTH_OPT, GRASPING_RANGE, DETECT_XYZ, GRIPPER_Z_MM, RELEASE_XYZ, GRASPING_MIN_Z)

    color_image, depth_image = camera.get_images()
    color_shape = color_image.shape

    while grasp.is_alive():
        color_image, depth_image = camera.get_images()
        cv2.imshow(WIN_NAME, color_image) # 显示彩色图像
        if GGCNN_IN_THREAD:
            if not depth_img_que.empty():
                depth_img_que.get()
            depth_img_que.put([depth_image, grasp.CURR_POS[2] / 1000.0])
            cv2.imshow(WIN_NAME, color_image) # 显示彩色图像
        else:
            data = ggcnn.get_grasp_img(depth_image, cx, cy, fx, fy, grasp.CURR_POS[2] / 1000.0)
            if data:
                if not ggcnn_cmd_que.empty():
                    ggcnn_cmd_que.get()
                ggcnn_cmd_que.put(data[0])
                grasp_img = data[1]
                combined_img = np.zeros((color_shape[0], color_shape[1] + grasp_img.shape[1] + 10, 3), np.uint8)
                combined_img[:color_shape[0], :color_shape[1]] = color_image
                combined_img[:grasp_img.shape[0], color_shape[1]+10:color_shape[1]+grasp_img.shape[1]+10] = grasp_img

                cv2.imshow(WIN_NAME, combined_img) # 显示彩色图像
            else:
                cv2.imshow(WIN_NAME, color_image) # 显示彩色图像
        
        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            camera.stop()
            break

if __name__ == '__main__':
    main()
