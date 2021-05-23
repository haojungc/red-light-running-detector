import sys
import numpy as np
import cv2

#------ video reader ---------
cap = cv2.VideoCapture(sys.argv[1])
if not cap.isOpened():
    cout << "Could not open or find the video" << endl
    exit(1)
fps = cap.get(cv2.CAP_PROP_FPS)
width = float(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = float(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#------ video writer-----------
odir = sys.argv[4]
resize_ratio = 1920.0/width
size = (int(resize_ratio*width), int(resize_ratio*height))
fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
videoOut = cv2.VideoWriter(odir + "judge_result.avi",fourcc, fps, size)


#------ info preprocess--------
try:
    TV_file = open( sys.argv[3], 'r')
except:
    print('no TV_file available -> no target license plate detected within the red light interval')
SL_file = open( sys.argv[2], 'r')

RL_file = open( sys.argv[5], 'r')
RL_startFrame=int(RL_file.readline())
RL_endFrame=int(RL_file.readline())
RL_file.close()

frameCount = 0
diff = [] # stopline and vehicle ycord diff list

TVstr = TV_file.readline()
TV_bbx = TVstr.split(' ')   # frameid, top left x, top left y, width, height
for i in range(5):
    TV_bbx[i] = int(TV_bbx[i])
TV_startFrame = TV_bbx[0]

for SLstr in SL_file:
    if RL_startFrame + frameCount >= TV_startFrame:
        TV_y = TV_bbx[2] + TV_bbx[4]
        SL_y = int(SLstr)
        diff.append(SL_y - TV_y)
        print("SL-TV diff:" + str(SL_y-TV_y) + " //SL:" + str(SL_y) + " //TV:" + str(TV_y))

        TVstr = TV_file.readline()
        TV_bbx = TVstr.split(' ')   # frameid, top left x, top left y, width, height
        if len(TV_bbx) > 4:
            for i in range(5):
                TV_bbx[i] = int(TV_bbx[i])
        else:
            print("End of target vehicle bbx txt reached")
            break

    frameCount = frameCount + 1

SL_file.close()
TV_file.close()

# ------- Judge violation--------
violateFrame = -1
violateCount = 0
slots_length = 5
for i in range(frameCount - 2*slots_length + 1):
    judge_slots_pre = diff[i: i+slots_length]
    judge_slots_pos = diff[i+slots_length: i+2*slots_length]
    pre_sum = 0
    pos_sum = 0
    for tmp in judge_slots_pre: # get sum of slot elements
        pre_sum = pre_sum + tmp
    for tmp in judge_slots_pos:
        pos_sum = pos_sum + tmp

    if pre_sum < 0 and pos_sum > 0: # pre_sum < 0 indicates car was before the stopline
        violateCount = violateCount+1

    if violateCount > 0:
        violateFrame = TV_startFrame + (i + slots_length) # the frame in the middle slot
        print('found target vehicle violating law!')
        break
    

# ------- Output video ---------
start = violateFrame - fps*3    # 3 sec before
end = violateFrame + fps*3      # 3 sec after
flag, im = cap.read()
while flag:
    if violateFrame == -1:
        print('no red light violation found')
        break
    flag, im = cap.read()
    im = cv2.resize(im, None, im, resize_ratio, resize_ratio)
    frameNum = cap.get(cv2.CAP_PROP_POS_FRAMES)
    if frameNum > start and frameNum < end :
        drawIm = im.copy()
        # cv2.line(drawIm,(100,500), (1800,500), (0,255,0), 4)
        font                   = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (10,500)
        fontScale              = 1
        fontColor              = (255,255,255)
        lineType               = 2
        cv2.putText(drawIm,'Run Red Light!', bottomLeftCornerOfText, font, fontScale, fontColor, lineType)
        videoOut.write(drawIm)
    else:
        videoOut.write(im)

# Release output video
videoOut.release()
# Release input video
cap.release()

print('program ended succesfully')
