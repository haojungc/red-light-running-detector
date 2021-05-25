#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on thur Feb 25 10:12:33 2021

@author: thlin002
"""

#importing some useful packages
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import math
import cv2
import os
import sys  # To get command line arguments
from scipy import stats  # TO use mode function
pi = 3.14159265358979323846
fRate = 20
kThres = 60

RLloc = sys.argv[3]
RL_file = open(RLloc, 'r')# get redlight start end frame information 
startFrame=int(RL_file.readline())
endFrame=int(RL_file.readline())
RL_file.close()

# ----------------noline fucntion----------------------
def noline(kalman ,kCount, y_k, im, frameNum, SL_file, videoOut):
    if frameNum <= endFrame and frameNum >= startFrame:
        SL_file.write(str( im.shape[0] - int(y_k[0][0] + .5) ) + "\n")
        kCount += 1
    if kCount > kThres:
        kalman.statePost = np.array( [im.shape[0]*1, 0] ).reshape((2,1))
        kCount = 0
    print("no stop lines found")
    videoOut.write(im)
#    cv2.imshow("Lane lines on image", im)
#    if cv2.waitKey(fRate) >= 0:
#        break

#----------------Get Video-----------------
cap = cv2.VideoCapture(sys.argv[1])
fps = cap.get(cv2.CAP_PROP_FPS)
if not cap.isOpened():
    cout << "Could not open or find the video" << endl

flag, im = cap.read()
im = cv2.resize(im, None, im, 1920.0/im.shape[1], 1920.0/im.shape[1])

#plt.figure(1)
#plt.imshow(im)
#plt.title(test_image_names[0])

# -----setting up kalman filter parameters------
kalman = cv2.KalmanFilter(2, 1, 0)
z_k = np.zeros( (1, 1) )
kalman.transitionMatrix = np.array( [[1., 1.], [0., 1.]] )

kalman.measurementMatrix = 1. * np.ones((1, 2))
kalman.processNoiseCov = 1e-5 * np.eye(2)
kalman.measurementNoiseCov = 1e-1 * np.ones((1, 1))
kalman.errorCovPost = 1. * np.ones((2, 2))
#cv2.setIdentity( kalman.measurementMatrix, 1. 		)
#cv2.setIdentity( kalman.processNoiseCov, 1e-5		)
#cv2.setIdentity( kalman.measurementNoiseCov, 1e-1   )
#cv2.setIdentity( kalman.errorCovPost, 1.			)

kalman.statePost = np.array( [im.shape[0]*1, 0.] ).reshape((2,1))
y_k = kalman.predict()
kCount = 0

# -------CREATE VIDEO WRITER------------------
# Define the codec and create VideoWriter object
odir = sys.argv[4]
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
videoOut = cv2.VideoWriter(odir + "outSL.avi", fourcc, fps, (im.shape[1],im.shape[0]))
vidMask = cv2.VideoWriter(odir + "outMask.avi", fourcc, fps, (im.shape[1],im.shape[0]), 0)  # last argument for greyscale image
vidCan = cv2.VideoWriter(odir + "outCan.avi", fourcc, fps, (im.shape[1], im.shape[0]), 0)
# -------Open output text file-----------------------
SL_file = open(odir + "SL_ycord.txt", 'w')
# -------Read yolo bbox text file from yolo darknet------
bdir = sys.argv[2]

while flag:
    flag, im = cap.read()
    if not flag:
        break
    frameNum = cap.get(cv2.CAP_PROP_POS_FRAMES)
    #cv2.imshow("Original image", im)
    #cv2.waitKey(fRate)
    # -----------------resize-----------------------
    im = cv2.resize(im, None, im, 1920.0/im.shape[1], 1920.0/im.shape[1])

    # -------------GREYSCALE IMAGE---------------
    # Grayscale one color channel
    # specify cmap = 'gray' in plt.imshow
    grayIm = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    #plt.figure(2)
    #plt.imshow(grayIm,cmap='gray')
    #plt.title('Greyscaled image')

    #---------------Erosion IMAGE------------------
    erosion_size = 1
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (2*erosion_size + 1, 2*erosion_size+1), (erosion_size, erosion_size))
    erosIm = cv2.erode(grayIm, element)

    #------------GAUSSIAN SMOOTHING-----------------
    # Use low pass filter to remove noise. Will remove high freq stuff like noise and edges
    # kernel_size specifies width/height of kernel, should be positive and odd
    # Also specify stand dev in X and Y direction, give zero to calculate from kernel size
    # Can also use average, median, and bilarteral blurring techniques
    kernel_size = 5; # bigger kernel = more smoothing
    smoothedIm = cv2.GaussianBlur(grayIm, (kernel_size, kernel_size), 0)
    #cv2.imshow("Smoothed image", smoothedIm)
    #cv2.waitKey(fRate)
    #plt.figure(3)
    #plt.imshow(smoothedIm,cmap='gray')
    #plt.title('Smoothed image')

    #--------------------CREATE MASK---------------------------
    half_bottom_width_ratio = 2.0/5.0
    height_ratio_1 = (0.75-0.5) # mid coord - top coord
    height_ratio_2 = (0.9-0.75) # bottom coord - mid coord 
    p0 = (im.shape[1] * (0.5 - half_bottom_width_ratio), im.shape[0] * (0.5+height_ratio_1+height_ratio_2)) # bottom left
    p1 = (im.shape[1] * (0.5 - half_bottom_width_ratio), im.shape[0] * (0.5+height_ratio_1)) # middle left
    p2 = (im.shape[1] * (0.5 - (half_bottom_width_ratio - height_ratio_1*math.tan(45 * pi/180))), im.shape[0]*0.50) # top left  
    p3 = (im.shape[1] * (0.5 + (half_bottom_width_ratio - height_ratio_1*math.tan(45 * pi/180))), im.shape[0]*0.50) # top right
    p4 = (im.shape[1] * (0.5 + half_bottom_width_ratio), im.shape[0] * (0.5+height_ratio_1)) # middle right
    p5 = (im.shape[1] * (0.5 + half_bottom_width_ratio), im.shape[0] * (0.5+height_ratio_1+height_ratio_2)) # bottom right
    road = [[p0,p1,p2,p3,p4,p5]] # house shape

    if int(frameNum) > int(startFrame) and int(frameNum) < int(endFrame):
        nstr = str(int(frameNum)).zfill(3)
        bfile = 'out' + nstr + '_cars.txt'
        try:
            btext = open(bdir + bfile, 'r')
        except:
            print(btext)
            print("could not open bbx txt file")

        # include car bounding box generated by yolo darknet
        mVs = []
        for line in btext:
            tmp = line.split()
            for i in range(5):
                tmp[i] = float(tmp[i])
            ratio = 0.8 # shrink inward from the box border
            pt1 = [ im.shape[1]*(tmp[1]-ratio*tmp[3]/2), im.shape[0]*(tmp[2]-tmp[4]/2) ] # top left
            pt2 = [ im.shape[1]*(tmp[1]+ratio*tmp[3]/2), im.shape[0]*(tmp[2]-tmp[4]/2) ] # top right
            pt3 = [ im.shape[1]*(tmp[1]+ratio*tmp[3]/2), im.shape[0]*(tmp[2]+tmp[4]/2) ] # bottom right
            pt4 = [ im.shape[1]*(tmp[1]-ratio*tmp[3]/2), im.shape[0]*(tmp[2]+tmp[4]/2) ] # bottom left
            mVs.append([pt1,pt2,pt3,pt4])

        bVertices = np.array(mVs, dtype=np.int32)
    
    rVertices = np.array(road, dtype=np.int32)
    mask = np.zeros_like(im)
    mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    cv2.fillPoly(mask, rVertices, 255 )
    # cv2.fillPoly(mask, bVertices, 255 ) replaced with forloop since overlay vertices would reverse the color
    if int(frameNum) > int(startFrame) and int(frameNum) < int(endFrame):
        for vertice in bVertices:
            cv2.fillPoly(mask, [vertice], 0 )
    
    vidMask.write(mask)
    #cv2.imshow("mask", mask)
    #cv2.waitKey(fRate)

    #------------------Threshold-----------------------
    mean, stddev = cv2.meanStdDev(grayIm, mask = mask)
    #print(str(mean) + " " + str(stddev))
    #print(int(mean[0]+1*stddev[0])) # for debugging
    ret,thresIm = cv2.threshold(smoothedIm, int(mean[0]+1.3*stddev[0]), 0, cv2.THRESH_TOZERO)
    #ret,thresIm = cv2.threshold(smoothedIm, 10, 0, cv2.THRESH_TOZERO)
    #cv2.imshow("Threshold image", thresIm)
    #cv2.waitKey(fRate)

    #-------------EDGE DETECTION---------------------
    # finds gradient in x,y direction, gradient direction is perpendicular to edges
    # checks pixels in gradient directions to see if they are local maximums, meaning on an edge
    # hysteresis thresholding has min and max value, edges with gradient intensity big enough are edges
    # edges that lie in bewteen are check to see if they connect to edges with intensity greater than max value, then it is considered edge
    # also assumes edges are long lines (not small pixels regions)
    minVal = 60
    maxVal = 150
    edgesIm = cv2.Canny(thresIm, minVal, maxVal)
    #plt.figure(4)
    #implot = plt.imshow(edgesIm,cmap='gray')

    #plt.scatter([0],[im.shape[0]])
    #plt.scatter([465],[320])
    #plt.scatter([475],[320])
    #plt.scatter([im.shape[1]],[im.shape[0]])

    #plt.title('Edge Detection')

    #----------------------APPLY MASK TO IMAGE-------------------------------
    # create image only where mask and edge Detection image are the same
    maskedIm = cv2.bitwise_and(edgesIm, mask)
    vidCan.write(maskedIm)
    #cv2.imshow("Masked Image", maskedIm)
    #cv2.waitKey(fRate)

    #Plot output of mask
    #plt.figure(6)
    #plt.imshow(maskedIm,cmap='gray')
    #plt.title('Masked Image')

    #Plot masked edges image
    #maskedIm3Channel = cv2.cvtColor(maskedIm, cv2.COLOR_GRAY2BGR)

    #------------------------HOUGH LINES----------------------------
    rho = 2
    theta = pi/180
    threshold = 90
    minLineLength = 100
    maxLineGap = 100

    lines = cv2.HoughLinesP(maskedIm, rho, theta, threshold, minLineLength = minLineLength, maxLineGap = maxLineGap)

    if lines is not None and len(lines) > 2:
        allLinesIm = np.zeros_like(maskedIm)
        #print(lines)
        for line in lines:
            cv2.line(allLinesIm,(line[0][0],line[0][1]),(line[0][2],line[0][3]),(255,255,0),2) # plot line

        #cv2.imshow("Hough Lines", allLinesIm)
        #cv2.waitKey(fRate)

        #---------------Select horizontal lines which is qualified--------------------
        horizonLines = []
        addedLine = False

        for currentLine in lines:
            #print(currentLine)
            x1 = currentLine[0][0]
            y1 = currentLine[0][1]
            x2 = currentLine[0][2]
            y2 = currentLine[0][3]
            lineLength = ((x2-x1)**2 + (y2-y1)**2)**.5 # get line length

            if lineLength > 30 and x2 != x1: # if line is long enough # dont divide by zero
                slope = (y2-y1)/(x2-x1) # get slope line
                #tanTheta = math.tan( (y2-y1)/(x2-x1) )
                angle = math.atan(slope) * 180/pi
                if abs(angle) < 2.5 and abs(angle) >= 0:
                    q1 = (x1 - 25, y1)
                    q2 = (x2 + 25, y1)
                    q3 = (x2 + 25, y1- 50.)     # trying different sampling area
                    q4 = (x1 - 25, y1- 50.)	#
                    #q3 = (x2, y1-min( abs(x2-x1)*2.5, 50. ))
                    #q4 = (x1, y1-min( abs(x2-x1)*2.5, 50. ))
                    lineVertices = np.array([[q1, q2, q3, q4]], dtype=np.int32)
                    lineMask = np.zeros_like(im)
                    lineMask = cv2.cvtColor(lineMask, cv2.COLOR_BGR2GRAY)
                    color = 255
                    cv2.fillPoly(lineMask, lineVertices, color, cv2.THRESH_BINARY)

                    lineMean, lineStddev = cv2.meanStdDev(grayIm, mask = lineMask)
                    if lineMean < mean + 1*stddev:
                        horizonLines.append([x1,y1,x2,y2,-slope,-angle])
                        addedLine = True
                    else:
                        print("white car / background detected")

        print(horizonLines)

        if addedLine == False:
            noline(kalman ,kCount, y_k, im, frameNum, SL_file, videoOut)
#            kCount += 1
#            if kCount > kThres:
#                kalman.statePost = np.array( [im.shape[0]*0.50, 0] ).reshape((2,1))
#                kCount = 0
#            print("Not enough qualified lines found")
#            videoOut.write(im)
#            cv2.imshow("Lane lines on image", im)
#            if cv2.waitKey(fRate) >= 0:
#                break
            continue

		# ------------------Calculate the most frequent slope-------------------------
        horizonAngles = []
#        addedLine = False
        for horizonLine in horizonLines:
#            if horizonLine[5] != 0:
            horLine_bin = round(horizonLine[5]*2)/2 # create bins
            horizonAngles.append(horLine_bin)
#            addedLine = True

#        if addedLine == False:
#            noline(kalman ,kCount, y_k, im, frameNum, SL_file, videoOut)
#            kCount += 1
#            if kCount > kThres:
#                kalman.statePost = np.array( [im.shape[0]*0.50, 0] ).reshape((2,1))
#                kCount = 0
#            print("Not enough non-zero-angle lines found")
#            videoOut.write(im);
#            cv2.imshow("Lane lines on image", im)
#            if cv2.waitKey(fRate) >= 0:
#                break
#            continue

        angleMode_t = stats.find_repeats(horizonAngles)
        try:
            maxIndex_a = np.argmax(angleMode_t[1])
            angleMode = float(angleMode_t[0][maxIndex_a])
        except:
            angleMode = float(horizonAngles[0])     # no repeat items so just pick arbitrary one
        
        print(angleMode)
        print("hello")
        #-----------------GET LINE ANGLE AVERAGES-----------------------
        angleGoodLines = []
        Sum = 0
        for horizonLine in horizonLines:
            if abs(horizonLine[5] - angleMode) < 0.3:
                angleGoodLines.append(horizonLine)
                Sum += horizonLine[5]
        print(len(angleGoodLines))
        angleMean = Sum/len(angleGoodLines)
        print(angleMean)

        # -----------------Calculate the most frequent y coord-------------------------
        yIntercepts = []
        for angleGoodLine in angleGoodLines:
            print("angleGoodLine Array---")
            print(angleGoodLine)
            print("---------------------")
            x1 = angleGoodLine[0]
            y1 = im.shape[0] - angleGoodLine[1]  # change the direction of y
            slope = angleGoodLine[4]
            yIntercept = y1 - slope*x1
            print("yIntercept array" + str(yIntercept))
            if math.isnan(yIntercept) == 0:
                yInter_bin = round(yIntercept/5.0,0) * 5
                yIntercepts.append(yInter_bin) # round to make bins of yintercept
        
        print(len(yIntercepts))
        
        yIntMode_t = stats.find_repeats(yIntercepts)
        try:
            maxIndex_y = np.argmax(yIntMode_t[1])
            yIntMode = float(yIntMode_t[0][maxIndex_y])
        except:
            yIntMode = float(yIntercepts[0])
        
        print("y intercept mode:" + str(yIntMode))
        # ------------------------Kalman Filter-------------------------
        y_k = kalman.predict()
        print("y_k.....................")
        print(y_k)
        print("........................")
        z_k = np.array( [yIntMode] )
        kalman.correct(z_k)

        # -----------------------PLOT LANE LINES------------------------
        stopLineIm = im.copy()
        slope = math.tan(angleMean * pi/180)
        x1 = 0
        y1 = y_k[0][0]
        x2 = im.shape[1]
        y2 = y1 + (x2-x1)*slope

        x1 = int(x1 + .5)	# round
        x2 = int(x2 + .5)
        y1 = int(y1 + .5)
        y2 = int(y2 + .5)

        print("draw line")
        print(x1)
        print(x2)
        print(y1)
        print(y2)

        if frameNum <= endFrame and frameNum >= startFrame:
            SL_file.write(str(im.shape[0]-y1) + "\n")

        cv2.line(stopLineIm,(x1,im.shape[0]-y1), (x2,im.shape[0]-y2), (0,255,0), 4) # plot line on color image
        videoOut.write(stopLineIm)
        #cv2.imshow("Lane lines on image", stopLineIm)
        #if cv2.waitKey(fRate) >= 0:
        #    break

    else:
        noline(kalman ,kCount, y_k, im, frameNum, SL_file, videoOut)
#        kCount += 1
#        if kCount > kThres:
#            kalman.statePost = np.array( [im.shape[0]*0.50, 0] ).reshape((2,1))
#            kCount = 0
#        print("Not enough hough lines found")
#        videoOut.write(im)
#        cv2.imshow("Lane lines on image", im)
#        if cv2.waitKey(fRate) >= 0:
#            break

# Release yolo text file
btext.close()
# Release written SL y cord text file
SL_file.close()
# Release output video
videoOut.release()
vidMask.release()
vidCan.release()
# Release input video
cap.release()
