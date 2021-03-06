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

                    if lp_str == lp_target:
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
