#!/bin/bash

check_file() 
{
	if [ ! -f "$1" ]
	then
		return 0
	else
		return 1
	fi
}

check_dir() 
{
	if [ ! -d "$1" ]
	then
		return 0
	else
		return 1
	fi
}


# Check if Darknet is compiled
check_file "darknet/libdarknet.so"
retval=$?
if [ $retval -eq 0 ]
then
	echo "Darknet is not compiled! Go to 'darknet' directory and 'make'!"
	exit 1
fi

check_file "vehicle_detection/darknet"
retval=$?
if [ $retval -eq 0 ]
then
	echo "Darknet for vehicle detection is not compiled. Go to 'vehicle_detection' directory and 'cmake . && make'."
	exit 1
fi

lp_model="data/lp-detector/wpod-net_update1.h5"
input_file=''
output_file='output.mp4'
img_sequence_dir='frames/'
frame_id_start='-1'
frame_id_end='-1'
output_dir=''
csv_file=''


# Check # of arguments
usage() {
	echo ""
	echo " Usage:"
	echo ""
	echo "   bash $0 -i input/dir -o output/dir -c csv_file.csv [-h] [-l path/to/model]:"
	echo ""
	echo "   -i   Input file path (mp4)"
    echo "   -s   frame_id_start (default = 0)"
    echo "   -e   frame_id_end (default = 1e9)"
	echo "   -o   Output dir path"
	echo "   -c   Output CSV file path"
	echo "   -t   Target license plate"
	echo "   -l   Path to Keras LP detector model (default = $lp_model)"
	echo "   -h   Print this help information"
	echo ""
	exit 1
}

while getopts 'i:s:e:o:t:c:l:h' OPTION; do
	case $OPTION in
		i) input_file=$OPTARG;;
        s) frame_id_start=$OPTARG;;
        e) frame_id_end=$OPTARG;;
		o) output_dir=$OPTARG;;
        t) lp_target=$OPTARG;;
		c) csv_file=$OPTARG;;
		l) lp_model=$OPTARG;;
		h) usage;;
	esac
done

if [ -z "$input_file"  ]; then echo "Input file not set."; usage; exit 1; fi
if [ -z "$output_dir" ]; then echo "Output dir not set."; usage; exit 1; fi
if [ -z "$lp_target" ]; then echo "Target license plate not set."; usage; exit 1; fi
if [ -z "$csv_file"   ]; then echo "CSV file not set." ; usage; exit 1; fi

# Check if input file exists
check_file $input_file
retval=$?
if [ $retval -eq 0 ]
then
	echo "Input file ($input_file) does not exist"
	exit 1
fi

# Check if dir for image sequence exists, if not, create it
img_sequence_dir=${input_file%/*/*}/$img_sequence_dir
check_dir $img_sequence_dir
retval=$?
if [ $retval -eq 0 ]
then
	mkdir -p $img_sequence_dir
fi

# Check if output dir exists, if not, create it
check_dir $output_dir
retval=$?
if [ $retval -eq 0 ]
then
	mkdir -p $output_dir
fi

# End if any error occur
set -e

# Set output filename
output_file=${input_file%/*/*}/$output_file

# Verifies the license plate format and erases '-' from the license plate
lp_target=$(echo "$lp_target" | sed 's/-//')
lp_len=${#lp_target}
if [[ $lp_len -lt 6 || $lp_len -gt 7 ]]
then
    echo "Invalid license plate (6 <= len <= 7, excluding '-')"
    exit 1
fi

# Detect vehicles
cd vehicle_detection/
./darknet detector demo cfg/coco.data cfg/yolov3.cfg yolov3.weights \
	$input_file -frame_id_start $frame_id_start -frame_id_end $frame_id_end \
    -out_filename $output_file -img_sequence_dir $img_sequence_dir -output_dir $output_dir -dont_show
cd ..

# Detect license plates
python3 license-plate-detection.py $output_dir $lp_model 2>&1

# OCR
python3 license-plate-ocr.py $output_dir $lp_target 2>&1

# Draw output and generate list
python3 gen-outputs.py $img_sequence_dir $output_dir 2>&1 > $csv_file

# Track the target vehicle and create an annotated video
python3 sot.py $input_file $output_dir $lp_target 2>&1

# Clean files and draw output
rm $output_dir/*_lp.png
rm $output_dir/*car.png
rm $output_dir/*_cars.txt
rm $output_dir/*_lp.txt
rm $output_dir/*_str.txt
