import numpy as np 
import cv2 
import pyrealsense2 as rs


def getCamera(device_serial:str): 

    pipeline = rs.pipeline()
    config = rs.config() 
    config.enable_device(device_serial)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    return pipeline, config 


def getDeviceSerial() -> list: 
    # (ref) https://stackoverflow.com/questions/67976611/how-to-get-intel-realsense-d435i-camera-serial-numbers-from-frames-for-multiple
    # Configure depth and color streams...
    realsense_ctx = rs.context()
    connected_devices = []

    for i in range(len(realsense_ctx.devices)):
        detected_camera = realsense_ctx.devices[i].get_info(rs.camera_info.serial_number)
        connected_devices.append(detected_camera)
    
    return connected_devices



def getFrames(pipeline):
    # Wait for a coherent pair of frames: depth and color
    frames = pipeline.wait_for_frames()
    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()

    if not depth_frame or not color_frame:
        print(f"depth_frame:{depth_frame}, color_frame:{color_frame}")
        return False, False 

    # Convert images to numpy arrays
    depth_img = np.asanyarray(depth_frame.get_data())
    color_img = np.asanyarray(color_frame.get_data())

    return color_img, depth_img

    
