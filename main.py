""" - realsense ; (ref) https://github.com/IntelRealSense/librealsense/issues/1735

"""
import logging
from pathlib import Path 
import os.path as osp

import numpy as np 
import cv2 
from omegaconf import OmegaConf
import pyrealsense2 as rs

from utils import getDeviceSerial, getCamera, getFrames


# === Video setting === # 
fourcc = cv2.VideoWriter_fourcc(*'MP4V')
record = False


# === File system setting === # 
cfg = OmegaConf.load('config.yaml')
spec = cfg.SPEC
path = osp.join('data', spec.cls_name, spec.ID)
types = ['rgb', 'depth']

for i in types:
    print(path)
    DATA_DIR = Path(osp.join(path, i))
    DATA_DIR.mkdir(parents=True, exist_ok=True)

s_num = 0  # scene number 

# === Camera process === # 
print("******  Camera Loading...  ******", end="\n ")

serial_list = getDeviceSerial()

pipeline_1, config_1 = getCamera(serial_list[0])
pipeline_2, config_2 = getCamera(serial_list[1])


# Start streaming from both cameras
pipeline_1.start(config_1)
pipeline_2.start(config_2)


try:
    while True:

        color_maps = [cv2.COLORMAP_JET, cv2.COLORMAP_RAINBOW, cv2.COLORMAP_BONE]

        # === Camera 1 === # 
        color_image_1, depth_image_1 = getFrames(pipeline_1)        
        depth_colormap_1 = cv2.applyColorMap( cv2.convertScaleAbs(depth_image_1, alpha=0.03), 
                                              color_maps[0]) # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        # === Camera 2 === #
        color_image_2, depth_image_2 = getFrames(pipeline_2)
        depth_colormap_2 = cv2.applyColorMap( cv2.convertScaleAbs(depth_image_2, alpha=0.03), 
                                              color_maps[2])


        print(depth_colormap_2.max())



        # Stack all images horizontally
        cam1_images = np.hstack((color_image_1, depth_colormap_1))
        cam2_images = np.hstack((color_image_2, depth_colormap_2))
        images = np.vstack((cam1_images, cam2_images))

        # Show images from both cameras
        cv2.namedWindow('RealSense', cv2.WINDOW_NORMAL)
        cv2.imshow('RealSense', images)

        cv2.imshow("depth", depth_image_1)

        key = cv2.waitKey(1)


        # Start: video capture signal
        if key == 27 : # 'ESC 
            break 
        
        elif key == ord('s'): # press 's' key 
            print("Capturing for image...")
            
            cam1_rgb_title = f"c1_rgb_{spec.cls_name}_{spec.ID}_{spec.scene}"
            cv2.imwrite(f"{osp.join(path,cam1_rgb_title)}.jpg", color_image_1 )

        elif key == ord('v'): # press 'v' 
            print("Recording start...")
            record = True 
            s_num += 1
            
            cam1_rgb_title = f"c1_rgb_{spec.cls_name}_{spec.ID}_s{s_num:04}"
            cam2_rgb_title = f"c2_rgb_{spec.cls_name}_{spec.ID}_s{s_num:04}"
            cam1_depth_title = f"c1_depth_{spec.cls_name}_{spec.ID}_s{s_num:04}"
            cam2_depth_title = f"c2_depth_{spec.cls_name}_{spec.ID}_s{s_num:04}"            

            video1_rgb = cv2.VideoWriter(f"{osp.join(path,types[0] , cam1_rgb_title)}.mp4", fourcc, 30.0, (color_image_1.shape[1], color_image_1.shape[0]), 1)
            video2_rgb = cv2.VideoWriter(f"{osp.join(path,types[0] , cam2_rgb_title)}.mp4", fourcc, 30.0, (color_image_2.shape[1], color_image_2.shape[0]), 1)
            video1_depth = cv2.VideoWriter(f"{osp.join(path,types[1], cam1_depth_title)}.mp4", fourcc, 30.0, (depth_colormap_1.shape[1], depth_colormap_1.shape[0]), 1)
            video2_depth = cv2.VideoWriter(f"{osp.join(path,types[1], cam2_depth_title)}.mp4", fourcc, 30.0, (depth_colormap_2.shape[1], depth_colormap_2.shape[0]), 1)


        elif key == 32: # press 'SPACE' 
            print("Recording stop...")
            record = False 

            video1_rgb.release()
            video2_rgb.release()
            video1_depth.release()
            video2_depth.release()

        if record == True: 
            print("Video recording...")
            video1_rgb.write(color_image_1)        
            video2_rgb.write(color_image_2)      
            video1_depth.write(depth_colormap_1)  
            video2_depth.write(depth_colormap_2)  
            




finally:
    # Stop streaming
    pipeline_1.stop()
    pipeline_2.stop()
