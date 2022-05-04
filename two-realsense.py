""" - realsense ; (ref) https://github.com/IntelRealSense/librealsense/issues/1735

"""
import logging
from pathlib import Path 
import os.path as osp
import argparse 

import numpy as np 
import cv2 
from omegaconf import OmegaConf
import pyrealsense2 as rs

from utils import getDeviceSerial, getCamera, getFrames, depth_options, emitter_options


# === Argparse === # 

parser = argparse.ArgumentParser(description='Set depth distance option.')
parser.add_argument('--clip', type=float, default=1.5,
                    help='distance clipping value (meter)')
parser.add_argument('--alpha', type=float, default=0.03,
                    help='OpenCV ColorMap alpha')

args = parser.parse_args()
print(args)


# === Video setting === # 
fourcc = cv2.VideoWriter_fourcc(*'MP4V')
record = False


# === File system setting === # 
cfg = OmegaConf.load('config.yaml')
spec = cfg.SPEC
path = osp.join('data', spec.cls_name, spec.ID)
types = ['rgb', 'depth', 'IR']

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
profile_1 = pipeline_1.start(config_1)
profile_2 = pipeline_2.start(config_2)

clipping_distance, align = depth_options(profile_1, clipping_dist=args.clip)
options = [clipping_distance, align]# if not want 'clipping_distance', 'align',
                                    # set [None, None]. 

# Set dot-patterens for IR image 
for profile in [profile_1, profile_2]:
    emitter_options(profile, set_emitter=0) # remove dot-patterns -> set_emitter=0
                                            # else -> set_emitter=1 

color_maps = [cv2.COLORMAP_JET, cv2.COLORMAP_RAINBOW, cv2.COLORMAP_BONE, cv2.COLORMAP_PINK]
set_maps = color_maps[2]


try:
    while True:

        # === Camera 1 === # 
        color_image_1, depth_image_1, leftIR_image_1, rightIR_image_1 = getFrames(pipeline_1, *options)        
        depth_colormap_1 = cv2.applyColorMap(   cv2.convertScaleAbs(depth_image_1, alpha=args.alpha), 
                                                set_maps) # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        # === Camera 2 === #
        color_image_2, depth_image_2, leftIR_image_2, rightIR_image_2 = getFrames(pipeline_2, *options)
        depth_colormap_2 = cv2.applyColorMap(   cv2.convertScaleAbs(depth_image_2, alpha=args.alpha), 
                                                set_maps)

        # Image blending                      
        # --------------                       
        blended_img_1 = cv2.addWeighted(color_image_1, 0.5, depth_colormap_1, 1, 0)
        blended_img_2 = cv2.addWeighted(color_image_2, 0.5, depth_colormap_2, 1, 0)

        # Convert grayscale IR image to 3-channel image 
        # -------------------------------------------
        leftIR_image_1 = cv2.cvtColor(leftIR_image_1, cv2.COLOR_GRAY2BGR)
        leftIR_image_2 = cv2.cvtColor(leftIR_image_2, cv2.COLOR_GRAY2BGR)



        # Stack all images horizontally
        cam1_images = np.hstack((color_image_1, depth_colormap_1, blended_img_1, leftIR_image_1 ))
        cam2_images = np.hstack((color_image_2, depth_colormap_2, blended_img_2, leftIR_image_2 ))
        images = np.vstack((cam1_images, cam2_images))

        # Show images from both cameras
        cv2.namedWindow('RealSense', cv2.WINDOW_NORMAL)
        cv2.imshow('RealSense', images)

        key = cv2.waitKey(1)


        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27: # ESC 
            cv2.destroyAllWindows()
            break
        
        # Start: video capture signal
        elif key == ord('s'): # press 's' key 
            print("Capturing for image...")
            
            cam1_rgb_title = f"c1_rgb_{spec.cls_name}_{spec.ID}_{spec.scene}"
            cv2.imwrite(f"{osp.join(path,cam1_rgb_title)}.jpg", color_image_1 )

        elif key == ord('v'): # press 'v' 
            print("Recording start...")
            record = True 
            s_num += 1

            cam_title = {f"{cam_id}_{img_type}":f"{cam_id}_{img_type}_{spec.cls_name}_{spec.ID}_s{s_num:04}" for img_type in types for cam_id in ['c1', 'c2']}
            print(cam_title.keys())
            
            video1_rgb = cv2.VideoWriter(f"{osp.join(path,types[0] , cam_title['c1_rgb'])}.mp4", fourcc, 30.0, (color_image_1.shape[1], color_image_1.shape[0]), 1)
            video2_rgb = cv2.VideoWriter(f"{osp.join(path,types[0] , cam_title['c2_rgb'])}.mp4", fourcc, 30.0, (color_image_2.shape[1], color_image_2.shape[0]), 1)

            video1_depth = cv2.VideoWriter(f"{osp.join(path,types[1], cam_title['c1_depth'])}.mp4", fourcc, 30.0, (depth_colormap_1.shape[1], depth_colormap_1.shape[0]), 1)
            video2_depth = cv2.VideoWriter(f"{osp.join(path,types[1], cam_title['c2_depth'])}.mp4", fourcc, 30.0, (depth_colormap_2.shape[1], depth_colormap_2.shape[0]), 1)

            video1_leftIR = cv2.VideoWriter(f"{osp.join(path,types[2], cam_title['c1_IR'])}.mp4", fourcc, 30.0, (leftIR_image_1.shape[1], leftIR_image_1.shape[0]), 1)
            video2_leftIR = cv2.VideoWriter(f"{osp.join(path,types[2], cam_title['c2_IR'])}.mp4", fourcc, 30.0, (leftIR_image_2.shape[1], leftIR_image_2.shape[0]), 1)


        elif key == 32: # press 'SPACE' 
            print("Recording stop...")
            record = False 

            video1_rgb.release()
            video2_rgb.release()
            video1_depth.release()
            video2_depth.release()
            video1_leftIR.release()
            video2_leftIR.release()


        if record == True: 
            print("Video recording...")
            video1_rgb.write(color_image_1)        
            video2_rgb.write(color_image_2)      

            video1_depth.write(depth_colormap_1)  
            video2_depth.write(depth_colormap_2)  

            video1_leftIR.write(leftIR_image_1)
            video2_leftIR.write(leftIR_image_2)
            




finally:
    # Stop streaming
    pipeline_1.stop()
    pipeline_2.stop()
