import cv2
import sys
import re

video_dir = sys.argv[1]
output_dir = sys.argv[2].rstrip('/')
target_lp = sys.argv[3]
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
output_video_name = output_dir.rsplit('/', 1)[0] + '/output_tracker.mp4'
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

center_x = int(bbox_ratio[0] * size[0])
center_y = int(bbox_ratio[1] * size[1])
object_width = int(bbox_ratio[2] * size[0])
object_height = int(bbox_ratio[3] * size[1])

bbox = (((center_x << 1) - object_width) >> 1, ((center_y << 1) - object_height) >> 1, object_width, object_height)
bbox_target = bbox

# Track
print('Start tracking %s' % (target_lp))
frame_count = 0
frames_until_target = []
rects_until_target = []
f = open('%s/target_bboxes.txt' % (output_dir), 'w')
while True:
    # Read a frame
    ret, frame = input_video.read()
    frame_count += 1

    if not ret:
        print('End tracking')
        f.close()
        break

    # Stores all the frames until `target_frame_id`.
    # If the target vehicle is found, track it backwards.
    if frame_count <= target_frame_id:
        frames_until_target.append(frame)
        if frame_count == target_frame_id:
            # Reverses the frame list.
            # {f1, f2,..., ft} => {ft, f(t-1),..., f1}
            # ft: the frame in which the target license plate is found
            frames_until_target.reverse() 

            # Initialize tracker
            ret = tracker.init(frame, bbox_target)
            if ret is False:
                print("Failed to initialize tracker")
                f.close()
                exit(1)
            pt1 = (int(bbox[0]), int(bbox[1]))
            pt2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            rects_until_target.append((pt1, pt2))

            # Tracks vehicle backwards from `ft`
            for fr in frames_until_target[1:]:
                # Update tracker
                ret, bbox = tracker.update(fr)

                # Stores the XY coordinates of the upper left point and the lower right point of the bbox.
                # If the bbox is missing, store ((0,0), (0,0)) 
                if ret and bbox[0] >= 0:
                    pt1 = (int(bbox[0]), int(bbox[1]))
                    pt2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    rects_until_target.append((pt1, pt2))
                else:
                    rects_until_target.append(((0, 0), (0, 0)))
            rects_until_target.reverse() 

            # Draws rectangles on each frame
            for i in range(len(frames_until_target)):
                (pt1, pt2) = rects_until_target[i]
                cv2.rectangle(frames_until_target[i], pt1, pt2, (0,0,255), 5, 1) # BGR
                output_video.write(frames_until_target[i])
            
            # Reinitializes the tracker
            ret = tracker.init(frame, bbox_target)
            if ret is False:
                print("Failed to initialize tracker")
                f.close()
                exit(1)

    # Tracks the target vehicle
    else:
        # Update tracker
        ret, bbox = tracker.update(frame)

        # Draw boundary box
        if ret and bbox[0] >= 0:
            pt1 = (int(bbox[0]), int(bbox[1]))
            pt2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, pt1, pt2, (0,0,255), 5, 1) # BGR

            # Saves xy-coordinates of target's bounding boxes
            f.write('%03d %d %d %d %d\n' % (frame_count, bbox[0], bbox[1], bbox[2], bbox[3]))

        output_video.write(frame)

input_video.release()
output_video.release()
