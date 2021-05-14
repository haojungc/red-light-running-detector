import sys
import numpy as np
import cv2

#------ video reader ---------
cap = cv2.VideoCapture(sys.argv[1])
if not cap.isOpened():
    cout << "Could not open or find the video" << endl

#------ video writer-----------
odir = sys.argv[4]
fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
videoOut = cv2.VideoWriter(odir + "judge_result.avi",fourcc, 20.0, (1920,1080))

#------ info preprocess--------
TV_file = open( sys.argv[3], 'r')
SL_file = open( sys.argv[2], 'r')
RLstartFrame = 0
frameCount = 0
diff = [] # stopline and vehicle ycord diff list
for TVstr in TV_file:

    TV_bbx = TVstr.split(' ')   # frameid, top left x, top left y, width, height

    for i in range(5):
        TV_bbx[i] = int(TV_bbx[i])

    TV_y = bbx[2] + bbx[4]
    if frameCount == 0:
        RL_startFrame = bbx[1]  # Record the start frameId of Red light, for video output use

    SLstr = SL_file.readline()
    SL_y = int(SLstr)
    diff[] = SL_y - TL_y

    frameCount = frameCount + 1

SL_file.close()
TV_file.close()


# ------- Judge violation--------
violateFLag = 0
violateFrame = -1
violateCount = 0
slots_length = 10
judge_slots = [] # scan diff[] with 10 slot ex []
for i in range(frameCount) - 2*slots_length + 1:
    judge_slots_pre = diff[i: i+slots_length]
    judge_slots_pos = diff[i+slots_length+1: i+2*slots_length+1]
    pre_sum = 0
    pos_sum = 0
    for tmp in judge_slots_pre: # get sum of slot elements
        pre_sum = pre_sum + tmp
    for tmp in judge_slots_pos:
        pos_sum = pos_sum + tmp        

    if pre_sum < 0 and pre_sum * pos_sum < 0: # pre_sum < 0 indicates car was before the stopline
        violateCount = violateCount+1
    else:
        violateCount = 0

    if violateCount > 20:
        violateFrame = RL_startFrame + (i + slots_length)
        break
    

# ------- Output video ---------
flag, im = cap.read()
while flag:
    if violateCount == -1:
        print('no red light violation found')
        break
    flag, im = cap.read()  
    frameNum = cap.get(cv2.CAP_PROP_POS_FRAMES)
    start = violateFrame - slots_length
    end = violateFrame + slots_length
    if frameNum > start and frameNum < end :
        drawIm = im.copy()
        cv2.line(drawIm,(100,500), (1800,500), (0,255,0), 4)
        videoOut.write(drawIm)
    else:
        videoOut.write(im)
    


