import sys

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Error: too few arguments")
        print("Usage: python3 %s <input-filename> <output-filename> <sample-size> <threshold>" % (sys.argv[0]))
        sys.exit()

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    sample_size = int(sys.argv[3])
    threshold = int(sys.argv[4])
    
    with open(input_filename, 'r', encoding='utf-8') as file:
        data = list(map(int, file.readlines()))

    frame_start = 0
    frame_end = 0
    frame_start_is_set = False
    data_size = len(data)
    total = 0

    for i in range(sample_size):
        total += data[i]

    if (total >= threshold):
        frame_start = 0
        frame_start_is_set = True

    for i in range(data_size - sample_size):
        total -= data[i]
        total += data[i + sample_size]
        if (frame_start_is_set == False and total >= threshold):
            frame_start = i + 1
            frame_start_is_set = True
        elif (frame_start_is_set == True and total < threshold):
            frame_end = i + sample_size
            break
    
    with open(output_filename, 'w', encoding='utf-8') as file:
        file.write('%d\n%d' % (frame_start, frame_end))
