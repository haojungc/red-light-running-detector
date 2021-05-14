import sys

RL_file = open( sys.argv[0], 'r')
SL_file = open( sys.argv[1], 'r')
TV_file = open( sys.argv[2], 'r')

startFrame = int(RL_file.readline())
endFrame = int(RL_file.readline())
RL_file.close()

violateFLag = 0
judge_count = 0
violateFrame = -1;
for TVstr in TV_file:
    TV_bbx = TVstr.split(' ')   # frameid, top left x, top left y, width, height

    for i in range(5):
        TV_bbx[i] = int(TV_bbx[i])

    TV_y = bbx[2] + bbx[4]
    if bbx[0] >= startFrame and bbx[0] <= endFrame:
        SLstr = SL_file.readline()
        SL_y = int(SLstr)
        diff = SL_y - TL_y
        
        if diff < 0 and diff > old_diff:
            count = count + 1
        else if count > 0:
            count = count - 1
        
        if count > 5:
            violateFlag = 1
            violateFrame = bbx[0] 
            break

        old_diff = diff

if violateFlag:
    print('run red light detected at frame' + str(violateFrame))

SL_file.close()
TV_file.close()
