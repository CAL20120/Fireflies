import os
import sys

import cv2

from datetime import datetime

import json

import argparse


def convert_to_video(
        first_image_path:str, kt_infos:dict=None, 
        version:int=None, user:str=None, general_infos:dict=None):
    

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

    out_resolution = (first_w, first_h + 230)


    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = cv2.VideoWriter(out_path, fourcc, 24, out_resolution)

    test_text = "Fireflies"

    target_font = cv2.FONT_HERSHEY_SIMPLEX

    current_frame_int = 1

    frame_pos_w = int(out_resolution[0] / 2.25)

    margin = 35


    if kt_infos:
        kt_status = kt_infos['status']
        kt_status = f"status: {kt_status}"

    if general_infos:
        scene_name = general_infos['scene_name']
        time = general_infos['time']


    for image in target_images: 
        current_image = os.path.join(image_dir, image)

        current_frame = cv2.imread(current_image)

        info_bar = cv2.copyMakeBorder(
            current_frame, 
            80, 
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
            thickness=2, 
            color=color_text, 
            lineType=cv2.LINE_AA
        )

        if version:
            cv2.putText(
                img=info_bar, 
                text=str(version), 
                org=(50 + 100, out_resolution[1] - 50), 
                fontFace=target_font, 
                fontScale=3,
                thickness=2, 
                color=color_text, 
                lineType=cv2.LINE_AA
            )


        cv2.putText(
            img=info_bar, 
            text=f"{current_frame_int:04}",
            org=(frame_pos_w, out_resolution[1] - 50), 
            fontFace=target_font, 
            fontScale=3, 
            thickness=2,
            color=color_text, 
            lineType=cv2.LINE_AA
        )

        info_w = int(out_resolution[0] - 500)

        if kt_infos:
            (txt_w, txt_h), _ = cv2.getTextSize(
                text=kt_status, 
                fontFace=target_font, 
                fontScale=1.5, 
                thickness=2
            )

            posx = out_resolution[0] - txt_w - margin
            posy = out_resolution[1] - margin - (txt_h * 2)

            cv2.putText(
                img=info_bar, 
                text=kt_status,
                org=(posx, posy), 
                fontFace=target_font, 
                fontScale=1.5, 
                thickness=2,
                color=color_text, 
                lineType=cv2.LINE_AA
            )

            if user:
                kt_artist = f"Artist: {user}"

                (txt_w, txt_h), _ = cv2.getTextSize(
                    text=kt_status, 
                    fontFace=target_font, 
                    fontScale=1.5, 
                    thickness=2
                )

                posx = out_resolution[0] - txt_w - margin
                posy = posy + txt_h + margin

                cv2.putText(
                    img=info_bar, 
                    text=kt_artist,
                    org=(posx, posy), 
                    fontFace=target_font, 
                    fontScale=1.5, 
                    thickness=2,
                    color=color_text, 
                    lineType=cv2.LINE_AA
                )
            

        if general_infos:
            print("### General infos found ###")

            time = general_infos['time']
            (txt_w, txt_h), _ = cv2.getTextSize(
                text=scene_name, 
                fontFace=target_font, 
                fontScale=0.8, 
                thickness=1
            )

            posx = margin
            posy = margin + txt_h

            cv2.putText(
                img=info_bar, 
                text=scene_name,
                org=(posx, posy), 
                fontFace=target_font, 
                fontScale=0.8, 
                thickness=1,
                color=color_text, 
                lineType=cv2.LINE_AA
            )
             
            (txt_w, txt_h), _ = cv2.getTextSize(
                text=time, 
                fontFace=target_font, 
                fontScale=0.8, 
                thickness=1
            )

            posx = out_resolution[0] - txt_w - margin
            posy = margin + txt_h

            cv2.putText(
                img=info_bar, 
                text=time,
                org=(posx, posy), 
                fontFace=target_font, 
                fontScale=0.8, 
                thickness=1,
                color=color_text, 
                lineType=cv2.LINE_AA
            )


        out_video.write(info_bar)

        current_frame_int = current_frame_int + 1


    out_video.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-first_image_path', type=str)
    
    parser.add_argument(
        '-kt_infos', 
        type=json.loads, 
        help="The Dict generated from the prod tracker " \
        "script to include info on the generated video (pass a str and will be converted to a dcit)"
    )

    parser.add_argument(
        '-general_infos', 
        type=json.loads
    )

    parser.add_argument('-user', type=str)

    args = parser.parse_args()

    convert_to_video(first_image_path=args.first_image_path, kt_infos=args.kt_infos, 
                     user=args.user, general_infos=args.general_infos)


if __name__ == "__main__":
    main()

    # convert_to_video(sys.argv[0])