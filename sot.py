import cv2
import sys
import re

video_dir = sys.argv[1]
output_dir = sys.argv[2]
target_filename = output_dir + '/' + 'target.txt'
target_frame_id = None
bbox_ratio = (None, None, None, None)
with open(target_filename, 'r') as f:
    target = f.readline() 
    # Extracts frame_id and object_id from `target`.
    # regex of `target`: out[0-9]+_[0-9]+(car|truck|bus|motorbike)$
    # E.g., target = 'out012_5car'
    # frame_id = 12, object_id = 5
    target_frame_id, target_object_id = list(map(int, re.findall(r'\d+', target)))

    with open('%s/out%03d_cars.txt' % (output_dir, target_frame_id), 'r') as f2:
        line = None
        for i in range(target_object_id + 1):
            line = f2.readline()
        # Removes class_id from `line` and converts the remaining part to a tuple with 4 elements.
        # `line` format: <class_id> <object_center_x_coord  / frame_width> <object_center_y_coord / real_height> <object_width / frame_width> <object_height / frame_height>
        values = line.split()
        bbox_ratio = tuple(map(float, values[1:]))

(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

# All OpenCV trackers
tracker_types = ['BOOSTING', 'MIL', 'KCF', 'TLD', 'MEDIANFLOW', 'GOTURN', 'MOSSE', 'CSRT']
tracker_type = tracker_types[7]

# Create tracker object
if tracker_type == 'BOOSTING':
    tracker = cv2.TrackerBoosting_create()
if tracker_type == 'MIL':
    tracker = cv2.TrackerMIL_create()
if tracker_type == 'KCF':
    tracker = cv2.TrackerKCF_create()
if tracker_type == 'TLD':
    tracker = cv2.TrackerTLD_create()
if tracker_type == 'MEDIANFLOW':
    tracker = cv2.TrackerMedianFlow_create()
if tracker_type == 'GOTURN':
    tracker = cv2.TrackerGOTURN_create()
if tracker_type == 'MOSSE':
    tracker = cv2.TrackerMOSSE_create()
if tracker_type == "CSRT":
    tracker = cv2.TrackerCSRT_create()

# Read video
input_video = cv2.VideoCapture(video_dir)
fps = input_video.get(cv2.CAP_PROP_FPS)
size = (int(input_video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(input_video.get(cv2.CAP_PROP_FRAME_HEIGHT)))

# Write video
fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
output_video_name = output_dir.rsplit('/', 2)[0] + '/output_tracker.mp4'
output_video = cv2.VideoWriter(output_video_name,  fourcc, fps, size)

# Exit if video isn't opened
if not input_video.isOpened():
    print('Error: Couldn\'t open the video')
    exit(1)

# Read first frame
ret, frame = input_video.read()
if not ret:
    print('Error: Couldn\'t read the video')
    exit(1)

frame_width = input_video.get(cv2.CAP_PROP_FRAME_WIDTH)
frame_height = input_video.get(cv2.CAP_PROP_FRAME_HEIGHT)

center_x = int(bbox_ratio[0] * frame_width)
center_y = int(bbox_ratio[1] * frame_height)
object_width = int(bbox_ratio[2] * frame_width)
object_height = int(bbox_ratio[3] * frame_height)

bbox = (((center_x << 1) - object_width) >> 1, ((center_y << 1) - object_height) >> 1, object_width, object_height)

# Track
frame_count = 0
tracker_initialized = False
while True:
    # Read a frame
    ret, frame = input_video.read()
    frame_count += 1

    if not ret:
        exit(1)

    if frame_count > target_frame_id:
        if tracker_initialized is False:
            # Initialize tracker
            ret = tracker.init(frame, bbox)
            if ret is False:
                print("Failed to initialize tracker")
                exit(1)
            tracker_initialized = True
        else:
            # Update tracker
            ret, bbox = tracker.update(frame)

        # Draw boundary box
        if ret and bbox[0] >= 0:
            pt1 = (int(bbox[0]), int(bbox[1]))
            pt2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, pt1, pt2, (255,0,0), 2, 1)

    output_video.write(frame)

input_video.release()
output_video.release()
