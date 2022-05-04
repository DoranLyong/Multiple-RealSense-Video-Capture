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
pipeline, config = getCamera(serial_list[0])

# Start streaming from your realsense camera
profile = pipeline.start(config)

clipping_distance, align = depth_options(profile, clipping_dist=args.clip)
options = [clipping_distance, align]# if not want 'clipping_distance', 'align',
                                    # set [None, None]. 

# Set dot-patterens for IR image 
emitter_options(profile, set_emitter=0) # remove dot-patterns -> set_emitter=0
                                        # else -> set_emitter=1 


color_maps = [cv2.COLORMAP_JET, cv2.COLORMAP_RAINBOW, cv2.COLORMAP_BONE]
set_maps = color_maps[0]

try: 
    while True: 
        # === Camera 1 === # 
        color_image, depth_image, leftIR_image, rightIR_image = getFrames(pipeline, *options)

        # Render depth image for visualization: 
        # ------------------------------------
        depth_colormap = cv2.applyColorMap( cv2.convertScaleAbs(depth_image, alpha=args.alpha), 
                                            set_maps) # Apply colormap on depth image (image must be converted to 8-bit per pixel first)

        # Image blending                      
        # --------------                       
        blended_img = cv2.addWeighted(color_image, 0.5, depth_colormap, 1, 0)


        # Convert grayscale IR image to 3-channel image 
        # -------------------------------------------
        leftIR_image = cv2.cvtColor(leftIR_image, cv2.COLOR_GRAY2BGR)
        rightIR_image = cv2.cvtColor(rightIR_image, cv2.COLOR_GRAY2BGR)
        
        # Stack all images horizontally
        # -----------------------------
        images = np.hstack((color_image, depth_colormap, blended_img, leftIR_image, rightIR_image))

        # Show images from cameras 
        cv2.namedWindow('Example', cv2.WINDOW_NORMAL)
        cv2.imshow('Example', images)
        key = cv2.waitKey(1)


        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
        
        # Start: video capture signal
        elif key == ord('s'): # press 's' key 
            print("Capturing for image...")
            
            cam_rgb_title = f"c1_rgb_{spec.cls_name}_{spec.ID}_{spec.scene}"
            cv2.imwrite(f"{osp.join(path,cam_rgb_title)}.jpg", color_image)

        elif key == ord('v'): # press 'v' 
            print("Recording start...")
            record = True 
            s_num += 1

            cam_title = {img_type:f"c1_{img_type}_{spec.cls_name}_{spec.ID}_s{s_num:04}" for img_type in types}
            print(cam_title.keys())

            video_rgb = cv2.VideoWriter(f"{osp.join(path,types[0] , cam_title['rgb'])}.mp4", fourcc, 30.0, (color_image.shape[1], color_image.shape[0]), 1)
            video_depth = cv2.VideoWriter(f"{osp.join(path,types[1], cam_title['depth'])}.mp4", fourcc, 30.0, (depth_colormap.shape[1], depth_colormap.shape[0]), 1)
            video_leftIR = cv2.VideoWriter(f"{osp.join(path,types[2] , cam_title['IR'])}.mp4", fourcc, 30.0, (leftIR_image.shape[1], leftIR_image.shape[0]), 1)


        elif key == 32: # press 'SPACE' 
            print("Recording stop...")
            record = False 

            video_rgb.release()
            video_depth.release()
            video_leftIR.release()


        if record == True: 
            print("Video recording...")
            video_rgb.write(color_image)        
            video_depth.write(depth_colormap)  
            video_leftIR.write(leftIR_image)

finally:
    # Stop streaming
    pipeline.stop()           
