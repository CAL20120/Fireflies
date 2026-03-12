import cv2
import os

from datetime import datetime

import sys

import argparse

def convert_to_video(first_image_path:str, kt_infos:dict=None, version:int=None):
    if not os.path.exists(first_image_path):
        print("### Invalid Path ###")
        return

    image_dir = os.path.dirname(first_image_path)


    in_ext = ('jpg', 'png', 'exr')

    target_images = [
        image for image in os.listdir(image_dir) if image.endswith(
            (in_ext)
        )
    ]

    target_images = sorted(target_images)
    
    if not target_images:
        print("### Couldn't find the images ###")
        return 
    

    print(target_images)

    out_path = os.path.join(image_dir, 'video_preview.mkv')


    first_image_cv = cv2.imread(first_image_path)
    first_h, first_w, _ = first_image_cv.shape

    out_resolution = (first_w, first_h + 150)


    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = cv2.VideoWriter(out_path, fourcc, 24, out_resolution)

    test_text = "Fireflies"

    general_info = {
        "Fireflies": "Fireflies", 
        "Date": datetime.now()
    }


    if kt_infos:
        pass


    target_font = cv2.FONT_HERSHEY_SIMPLEX

    current_frame_int = 1

    for image in target_images: 
        current_image = os.path.join(image_dir, image)

        current_frame = cv2.imread(current_image)

        info_bar = cv2.copyMakeBorder(
            current_frame, 
            0, 
            150, 
            0,
            0, 
            cv2.BORDER_CONSTANT, 
            value=[0, 0, 0]
        )

        color_text = (255, 255, 255)

        cv2.putText(
            img=info_bar, 
            text=test_text, 
            org=(50, out_resolution[1] - 50), 
            fontFace=target_font, 
            fontScale=3,
            thickness=3, 
            color=color_text, 
            lineType=cv2.LINE_AA
        )

        cv2.putText(
            img=info_bar, 
            text=f"{current_frame_int:04}",
            org=(int(out_resolution[0] / 2.25), out_resolution[1] - 50), 
            fontFace=target_font, 
            fontScale=3, 
            thickness=3,
            color=color_text, 
            lineType=cv2.LINE_AA
        )


        out_video.write(info_bar)

        current_frame_int = current_frame_int + 1


    out_video.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-first_image_path')
    args = parser.parse_args()

    convert_to_video(args.first_image_path)


if __name__ == "__main__":
    main()

    # convert_to_video(sys.argv[0])