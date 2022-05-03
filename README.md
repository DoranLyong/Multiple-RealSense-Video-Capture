# Multiple Realsense(e.g. D435) Video Capture 



## Installation 

* Please be sure to install [Intel RealSense SDK](https://github.com/IntelRealSense/librealsense/releases).
* Then, install python packages: 
    ``` bash 
    pip install -r requirements.txt
    ```



## Usage 

* Check the ```config.yaml``` (you can change whenever you need). 
* Run the code:
    ```bash
    python two-realsense.py  # for two camera devices 
    # or 
    python single-realsense.py # for one camera device 
    ```
* Control by your keyboard
    * 'v' button - to record your video 
    * 'SPACE' button - to save your video 
    * 's' button - to save a sample image (you can customize it if you want)



## Demo 

* Reference to [align-depth2color.py](https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py) for depth and color ```alignment``` & ```distance clipping```. 

* For understanding how it works, run the demo code with single realsense camera: 

  ```
  python demo.py 
  ```

  