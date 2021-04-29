#!/usr/bin/env python3

import os, sys

in_arg_idx = 2
out_arg_idx = 7
args = ['ffmpeg', '-i', '',
        '-vcodec', 'copy', 
        '-acodec', 'copy', '']

out_file = 'converter.sh'
out_dir = sys.argv[1]
in_dir = sys.argv[2]

# Creates bash script
with open(out_file, 'w') as f:
    f.write("#!/usr/bin/env bash\n\n")
    f.write("mkdir -p " + out_dir + "\n")
    first = True
    for filename in os.listdir(in_dir):
        print('file:', filename)

        name, extension = os.path.splitext(filename)

        in_path = os.path.join(in_dir, filename)
        out_path = os.path.join(out_dir, name + '.mp4')

        args[in_arg_idx] = in_path
        args[out_arg_idx] = out_path
        
        # Write to bash script
        if first is True:
            first = False
        else:
            f.write("\n")
        f.write(args[0])
        for i in range(1, len(args)):
            f.write(" " + args[i])