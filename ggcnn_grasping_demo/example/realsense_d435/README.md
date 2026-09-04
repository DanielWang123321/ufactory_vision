# Configuration with Intel Realsense D435 Camera

## Hardware Requirements

-   **Robot Arm**: [UFACTORY 850, xArm 5/6/7 Series, Lite6](https://www.ufactory.cc/ufactory-850/)
-   **Gripper**: [UFACTORY xArm Gripper G1/G2](https://www.ufactory.cc/product-page/ufactory-xarm-gripper/) or [Vacuum Gripper Lite6](https://www.ufactory.cc/product-page/ufactory-lite-6-kit/)
-   **Camera**: [Intel RealSense D435](https://realsenseai.com/products/stereo-depth-camera-d435/)
-   **Camera Mount**: Provided by UFACTORY (available for purchase or 3D printing)
    -   Purchase Link: [UFACTORY Camera Stand](https://www.ufactory.cc/product-page/ufactory-xarm-camera-stand/)
    -   3D File Download: [Realsense_Camera_Stand.STEP](https://www.ufactory.cc/wp-content/uploads/2024/05/CameraStand_1300.zip)

## Software

### Supported Python Versions

Supported Python versions: 3.9-3.14 (Recommended: 3.11).

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/xArm-Developer/ufactory_vision.git
cd ufactory_vision
```

### 2. Create a Python Virtual Environment

It is recommended to use a virtual environment for running this project.

#### **Windows (Using Anaconda)**

```bash
conda create --name ufactory_vision python=3.11
conda activate ufactory_vision
```

#### **Linux (Using venv)**

```bash
python3.11 -m venv ufactory_vision
source ufactory_vision/bin/activate
```

### 3. Install Dependencies and Run Examples

Please follow the corresponding installation and execution steps based on the camera model you are using.
First, ensure you are in the `realsense_d435` directory:

```bash
cd ggcnn_grasping_demo/example/realsense_d435
```

#### 3.1 Install Dependencies

```bash
pip install -r requirements_rs.txt
```

#### 3.2 Run Example

Replace `192.168.1.xxx` with the actual IP address of your robot arm controller.
*   **UFACTORY 850 or xArm 5/6/7 Series Robot Arm**
    ```bash
    python run_rs_d435_grasp.py 192.168.1.xxx
    ```
*   **UFACTORY Lite 6 Robot Arm**
    ```bash
    python run_rs_d435_grasp_lite6.py 192.168.1.xxx
    ```

## Important Notes

*   **TCP/Coordinate Offset**: Do not set TCP offset or coordinate offset, otherwise you may need to fine-tune the code.
*   **TCP Payload**: Set TCP payload to avoid false collision detection.
*   **Collision Detection**: Before running the example, ensure that collision detection is enabled. It is recommended to set the collision sensitivity to 3 or higher.
