import csv
import os
import re
import sys
import copy
import time
import argparse

import cv2 as cv


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_dir", default="../sample-movie/")
    parser.add_argument("--files", default="file_list.csv")
    parser.add_argument("--destination_dir", default = 'tracking_results/')
    parser.add_argument("--width", help='cap width', type=int, default=1080)
    parser.add_argument("--height", help='cap height', type=int, default=720)

    args = parser.parse_args()

    return args

def isint(s):
    p = '[-+]?\d+'
    return True if re.fullmatch(p, s) else False


def initialize_tracker(window_name, image):
    params = cv.TrackerDaSiamRPN_Params()
    params.model = "model/DaSiamRPN/dasiamrpn_model.onnx"
    params.kernel_r1 = "model/DaSiamRPN/dasiamrpn_kernel_r1.onnx"
    params.kernel_cls1 = "model/DaSiamRPN/dasiamrpn_kernel_cls1.onnx"
    tracker = cv.TrackerDaSiamRPN_create(params)

    # target selection
    while True:
        bbox = cv.selectROI(window_name, image)

        try:
            tracker.init(image, bbox)
        except Exception as e:
            print(e)
            continue

        return tracker

def video_track(video_file,cap_width, cap_height, destination_dir):
    color_list = [
        [255, 0, 0],  # blue
        [0, 0, 255], #red
        [0, 255, 0], #lime
    ]

    if isint(video_file):
        video_file = int(video_file)
    cap = cv.VideoCapture(video_file)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, cap_width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, cap_height)

    # Tracker initialize ############################################################
    window_name = video_file.split('/')[-1]
    cv.namedWindow(window_name)

    #creating the header for the csv file
    tracking_csv_file = f"{destination_dir}{window_name.split('.')[0]}.csv"
    with open(tracking_csv_file, 'w', newline= '') as f:
        writer = csv.writer(f)
        writer.writerow(['frame','Risk_coordinate'])
    f.close()

    count = 1

    while True:
        ret, image = cap.read()

        if not ret:
            try:
                break
            except:
                sys.exit("Can't read first frame")
        # cv.namedWindow(window_name)
        cv.putText(
            image,
            'Frame # ' + str(count),
            (10, 25), cv.FONT_HERSHEY_SIMPLEX, 0.7, color_list[1], 2,
            cv.LINE_AA)
        cv.imshow(window_name,image)
        key = cv.waitKey(200) & 0xFF


        if key == 32:
            tracker = initialize_tracker(window_name, image)
            frame_num = 0
            while cap.isOpened():
                tracked_frame = frame_num +  count
                ret, image = cap.read()
                if not ret:
                    break
                debug_image = copy.deepcopy(image)

                # Tracking update
                start_time = time.time()
                ok, bbox = tracker.update(image)


                elapsed_time = time.time() - start_time
                if ok:
                    # Bounding box drawing after tracking

                    cv.rectangle(debug_image, bbox, color_list[0], thickness=2)
                    with open(tracking_csv_file, 'a+',newline='') as tracking_box:
                        writer = csv.writer(tracking_box)
                        writer.writerow([tracked_frame,bbox])


                    # with open(tracking_csv_file, 'w+', newline='') as tracking_box:
                    #     writer = csv.writer(tracking_box, lineterminator='\n')
                    #     writer.writerow(['frame','coordinate'])
                    #     # writer.writeheader([tracked_frame,bbox])
                    #     writer.writerows([[tracked_frame,bbox]])

                # Processing time
                cv.putText(
                    debug_image,
                    'Frame # ' + str(tracked_frame),
                    (10, 25), cv.FONT_HERSHEY_SIMPLEX, 0.7, color_list[1], 2,
                    cv.LINE_AA)
                cv.putText(
                    debug_image,
                    'DaSiamRPN' + " : " + '{:.1f}'.format(elapsed_time * 1000) + "ms",
                    (10, 50), cv.FONT_HERSHEY_SIMPLEX, 0.7, color_list[0], 2,
                    cv.LINE_AA)

                cv.imshow(window_name, debug_image)
                frame_num +=1



                k = cv.waitKey(1)
                if k == 32:  # SPACE
                    # redesignation
                    tracker = initialize_tracker(window_name, image)
                if k == 27:  # ESC
                    break
        try:
            count = tracked_frame
            count +=1
            tracked_frame = count
        except:
            count+=1
        # print(count)

    cv.destroyAllWindows()
    print('===========================================================')
    print('What type of accident it was?')
    print('Please select an option from the below list:')
    print('1. Front to rear, 2. Front to front, 3. Angle, 4. Sideswipe same direction, 5. N/A , 6. Bad quality/Not usable')
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    options= ['Front to rear', 'Front to front','Angle','Sideswipe same direction', 'N/A', 'Not usable']
    while True:
        try:
            inp = int(input("Enter the number corresponding to the accident type : "))
            if inp in range(len(options)+1):
                value = options[inp-1]
            else:
                print('Wrong input type. You have to select a number between 1 to 6. Please try again.')
                continue
        except ValueError:
            print('Wrong input type. You have to select a number between 1 to 6. Please try again.')
            continue
        else:
            print('You have selected : ', value)
            print('===========================================================')
            break
    return value

def main():
    args = get_args()
    cap_width = args.width
    cap_height = args.height
    input_file = args.files
    tmp_file = f"{input_file}.tmp"

    video_dir = args.video_dir

    destination_dir = args.destination_dir
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)


    with open(input_file, 'r', newline='') as csvfile, open(tmp_file, 'w+', newline='') as csvtempfile:
        writer = csv.writer(csvtempfile, delimiter=',')
        writer.writerow(['video_id','frame1','accident_begin','last','manner','status'])
        reader = csv.reader(csvfile, delimiter=',')
        # heading = next(reader)
        for row in reader:
            video_id,frame_1,accident_frame,last_frame,status,accident_type= row
            # files,status, accident_type = row
            if video_id =='video_id':
                print('skipped the header')
            elif status == 'status':
                writer.writerow(row)
            elif status != 'ok':
                video_file = f"{video_dir}{video_id}.mp4"
                print(video_file)
                accident_type = video_track(video_file,cap_width,cap_height, destination_dir)
                writer.writerow([video_id,frame_1,accident_frame,last_frame, accident_type, 'ok'])
            else:
                writer.writerow(row)
    os.remove(input_file)
    os.rename(tmp_file,input_file)

if __name__ == '__main__':
    main()
