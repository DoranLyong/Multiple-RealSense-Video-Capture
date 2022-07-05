import numpy as np 
import cv2 
import pyrealsense2 as rs

from utils import getDeviceSerial, getCamera


# === Camera process === # 
# ------------------------
print("******  Camera Loading...  ******", end="\n ")

serial_list = getDeviceSerial()

pipeline_1, config_1 = getCamera(serial_list[0])

# Start streaming from both cameras
# ---------------------------------
profile_1 = pipeline_1.start(config_1)


# Getting the depth sensor's depth scale (see rs-align example for explanation)
depth_sensor = profile_1.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: " , depth_scale)


# We will be removing the background of objects more than
#  clipping_distance_in_meters meters away
clipping_distance_in_meters = 1.5 # meter
clipping_distance = clipping_distance_in_meters / depth_scale


# Create an align object
# rs.align allows us to perform alignment of depth frames to others frames
# The "align_to" is the stream type to which we plan to align depth frames.
align_to = rs.stream.color
align = rs.align(align_to)

# == PointCloud == # 
# -----------------
pc = rs.pointcloud() 
points = rs.points()

threshold_filter = rs.threshold_filter()
threshold_filter.set_option(rs.option.max_distance, 1.5)
threshold_filter.set_option(rs.option.min_distance, 0.5)


try: 
    while True: 
        # === Camera 1 === # 
        # Get frameset of color and depth
        frames = pipeline_1.wait_for_frames()
        
        # Align the depth frame to color frame
        aligned_frames = align.process(frames)
        

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame() # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            continue 

        # Convert images to numpy arrays
        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())


        # Remove background - Set pixels further than clipping_distance to grey
        grey_color = 153
        #depth_image_3d = np.dstack((depth_image,depth_image,depth_image)) #depth image is 1 channel, color is 3 channels

        bg_removed = np.where((depth_image> clipping_distance) | (depth_image <= 0), grey_color, depth_image)



        # Render images:
        #   depth align to color on left
        #   depth on right
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_BONE)
        bg_removed_colormap = cv2.applyColorMap(cv2.convertScaleAbs(bg_removed, alpha=0.03), cv2.COLORMAP_BONE)


        # Image blending 
        # ---------------
        blended_img = cv2.addWeighted(color_image, 0.5, depth_colormap, 1, 0)


        # Stack all images horizontally
        images = np.hstack((color_image, depth_colormap, blended_img, bg_removed_colormap))
        


        

        
        # Show images from cameras 
        cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)
        cv2.imshow('Align Example', images)
        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
        
        elif key == ord('s'): # press 's' key 
            # PointCloud 
#            aligned_depth_frame= threshold_filter.process(aligned_depth_frame)
            points = pc.calculate(aligned_depth_frame)
            pc.map_to(color_frame)

            
            print("Saving to 1.ply...")
            points.export_to_ply("1.ply", color_frame)
            print("Done")



finally:
    # Stop streaming
    pipeline_1.stop()    
