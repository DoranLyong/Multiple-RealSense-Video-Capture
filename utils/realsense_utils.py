import numpy as np 
import cv2 
import pyrealsense2 as rs


def getCamera(device_serial:str): 

    pipeline = rs.pipeline()
    config = rs.config() 
    config.enable_device(device_serial)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.infrared, 1, 640, 480, rs.format.y8, 30) # Left IR 
    config.enable_stream(rs.stream.infrared, 2, 640, 480, rs.format.y8, 30) # Right IR 

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



def getFrames(pipeline, *options):
    clipping_distance, align = options

    # Wait for a coherent pair of frames: depth and color
    # ---------------------------------------------------
    frames = pipeline.wait_for_frames() # Get frameset of color and depth

    if align: 
        # Align the depth frame to color frame
        frames = align.process(frames) # if aligned, depth_frame is aligned to 640x480
        
    # Get frames 
    # ----------
    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()
    leftIR_frame = frames.get_infrared_frame(1) # (ref) https://community.intel.com/t5/Items-with-no-label/How-to-show-d435-IR-image-using-python-wrapper-pyrealsense2/td-p/545526
    rightIR_frame = frames.get_infrared_frame(2)

    if not depth_frame or not color_frame:
        print(f"depth_frame:{depth_frame}, color_frame:{color_frame}")
        return False, False 

    # Convert images to numpy arrays
    # ------------------------------
    depth_img = np.asanyarray(depth_frame.get_data())
    color_img = np.asanyarray(color_frame.get_data())
    leftIR_img = np.asanyarray(leftIR_frame.get_data())
    rightIR_img = np.asanyarray(rightIR_frame.get_data())


    if clipping_distance:
        # Remove background - Set pixels further than clipping_distance to grey
        grey_color = 153
        depth_img = np.where((depth_img> clipping_distance) | (depth_img <= 0), grey_color, depth_img)

    return color_img, depth_img, leftIR_img, rightIR_img

    
def depth_options(profile, clipping_dist=1.5): 
    # Getting the depth sensor's depth scale (see rs-align example for explanation)
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    print(f"Depth Scale is: {depth_scale}")
    
    # We will be removing the background of objects more than
    # clipping_distance_in_meters meters away
    clipping_distance_in_meters = clipping_dist # meter
    clipping_distance = clipping_distance_in_meters / depth_scale
    print(f" Depth clipping_distance (m): {clipping_distance_in_meters}")
    print(f" Depth clipping_distance (pix value): {clipping_distance}")

    # Create an align object
    # rs.align allows us to perform alignment of depth frames to others frames
    # The "align_to" is the stream type to which we plan to align depth frames.
    align_to = rs.stream.color
    align = rs.align(align_to)

    return clipping_distance, align


def emitter_options(profile, set_emitter = 1):
    # remove 'dot patterns'; (ref) https://community.intel.com/t5/Items-with-no-label/How-to-enable-disable-emitter-through-python-wrapper/td-p/547900
    device = profile.get_device() 
    depth_sensor = device.query_sensors()[0]
    emitter = depth_sensor.get_option(rs.option.emitter_enabled)
    print("default emitter = ", emitter)

    set_emitter = set_emitter
    depth_sensor.set_option(rs.option.emitter_enabled, set_emitter)
    emitter1 = depth_sensor.get_option(rs.option.emitter_enabled)
    print("new emitter = ", emitter1)



