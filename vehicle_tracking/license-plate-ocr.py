import sys
import cv2
import numpy as np
import traceback

import darknet.python.darknet as dn

from os.path                import splitext, basename
from glob                   import glob
from darknet.python.darknet import detect
from src.label              import dknet_label_conversion
from src.utils              import nms

def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub)

def match(lp, lp_target):
    if lp == lp_target:
        return True

    lp_list = list(lp)
    modified = False
    occur_1 = list(find_all(lp_target, '1'))
    for i in occur_1:
        if lp_list[i] == 'I':
            lp_list[i] = '1'
            modified = True

    occur_H = list(find_all(lp_target, 'H'))
    for i in occur_H:
        if lp_list[i] == 'M' or lp_list[i] == 'W':
            lp_list[i] = 'H'
            modified = True

    occur_M = list(find_all(lp_target, 'M'))
    for i in occur_M:
        if lp_list[i] == 'H':
            lp_list[i] = 'M'
            modified = True

    occur_W = list(find_all(lp_target, 'W'))
    for i in occur_W:
        if lp_list[i] == 'H' or lp_list[i] == 'V':
            lp_list[i] = 'W'
            modified = True

    lp = "".join(lp_list)
    if modified is True:
        print('Modified LP: %s' % lp)

    if lp == lp_target:
        return True
    else:
        return False

if __name__ == '__main__':

    try:
        
        input_dir  = sys.argv[1].rstrip('/')
        output_dir = input_dir

        lp_target = sys.argv[2]

        ocr_threshold = .4

        ocr_weights = bytes('data/ocr/ocr-net.weights', encoding='utf-8')
        ocr_netcfg  = bytes('data/ocr/ocr-net.cfg', encoding='utf-8')
        ocr_dataset = bytes('data/ocr/ocr-net.data', encoding='utf-8')

        ocr_net  = dn.load_net(ocr_netcfg, ocr_weights, 0)
        ocr_meta = dn.load_meta(ocr_dataset)

        imgs_paths = sorted(glob('%s/*lp.png' % output_dir))

        print('Performing OCR...')
        print('Target: %s' % lp_target)

        target_found = False
        for i,img_path in enumerate(imgs_paths):
            if target_found == True:
                print('\tTarget found. Ending OCR...')
                break

            print('\tScanning %s' % img_path)

            bname = basename(splitext(img_path)[0])

            R,(width,height) = detect(ocr_net, ocr_meta, img_path ,thresh=ocr_threshold, nms=None)

            if len(R):

                L = dknet_label_conversion(R,width,height)
                L = nms(L,.45)

                L.sort(key=lambda x: x.tl()[0])
                lp_str = ''.join([chr(l.cl()) for l in L])

                lp_len = len(lp_str)
                if lp_len >= 6 and lp_len <= 7:
                    print('\t\tLP: %s' % lp_str)

                    if lp_len == len(lp_target) and match(lp_str, lp_target) is True:
                        target_found = True

                        # Erases the trailing substring "_lp" from `bname`.
                        # original format of bname: "out<frame_id>_<object_id><class_name>_lp"
                        # modified format of bname: "out<frame_id>_<object_id><class_name>"
                        bname_target = bname.rsplit('_', 1)[0]
                        with open('%s/target.txt' % (output_dir), 'w') as f:
                            f.write(bname_target + '\n')
                        with open('%s/%s_str.txt' % (output_dir,bname),'w') as f:
                            f.write(lp_str + '\n')

            else:

                print('No characters found')

        if target_found == False:
            print('\tTarget not found. Ending OCR...')

    except:
        traceback.print_exc()
        sys.exit(1)

    sys.exit(0)
