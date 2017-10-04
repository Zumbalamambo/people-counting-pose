import sys
import os

import math

import imageio
from moviepy.editor import *

def read_video(video_name):
    # Read video from file
    video_name_input = 'testset/' + video_name + '.mov'
    video = VideoFileClip(video_name_input)
    return video

def frame2image(video_name):
    video = read_video(video_name)

    video_frame_number = int(video.duration * video.fps) ## duration: second / fps: frame per second
    video_frame_ciphers = math.ceil(math.log(video_frame_number, 10)) ## ex. 720 -> 3

    os.makedirs('testset/' + video_name)

    for i in range(0, video_frame_number):
        video.save_frame('testset/' + video_name + '/frame_' + str(i).zfill(video_frame_ciphers) + '.jpg', i)

def frame2pose(video_name):
    import numpy as np

    sys.path.append(os.path.dirname(__file__) + "/../")

    from scipy.misc import imread, imsave

    from config import load_config
    from dataset.factory import create as create_dataset
    from nnet import predict
    from util import visualize
    from dataset.pose_dataset import data_to_input

    from multiperson.detections import extract_detections
    from multiperson.predict import SpatialModel, eval_graph, get_person_conf_multicut
    from multiperson.visualize import PersonDraw, visualize_detections

    import matplotlib.pyplot as plt

    cfg = load_config("demo/pose_cfg_multi.yaml")

    dataset = create_dataset(cfg)

    sm = SpatialModel(cfg)
    sm.load()

    draw_multi = PersonDraw()

    # Load and setup CNN part detector
    sess, inputs, outputs = predict.setup_pose_prediction(cfg)

    ################

    video = read_video(video_name)

    video_frame_number = int(video.duration * video.fps) ## duration: second / fps: frame per second

    for i in range(0, video_frame_number):
        image = video.get_frame(i)

        ######################

        image_batch = data_to_input(image)

        # Compute prediction with the CNN
        outputs_np = sess.run(outputs, feed_dict={inputs: image_batch})
        scmap, locref, pairwise_diff = predict.extract_cnn_output(outputs_np, cfg, dataset.pairwise_stats)

        detections = extract_detections(cfg, scmap, locref, pairwise_diff)
        unLab, pos_array, unary_array, pwidx_array, pw_array = eval_graph(sm, detections)
        person_conf_multi = get_person_conf_multicut(sm, unLab, unary_array, pos_array)

        print('person_conf_multi: ')
        print(type(person_conf_multi))
        print(person_conf_multi)

        # Add library to save image
        from PIL import Image, ImageDraw
        image_img = Image.fromarray(image)

        # Save image with points of pose
        draw = ImageDraw.Draw(image_img)

        people_num = 0
        point_num = 17
        print('person_conf_multi.size: ')
        print(person_conf_multi.size)
        people_num = person_conf_multi.size / (point_num * 2)
        people_num = int(people_num)
        print('people_num: ')
        print(people_num)

        point_i = 0 # index of points
        point_r = 5 # radius of points

        import random

        people_real_num = 0
        for people_i in range(0, people_num):
            point_color_r = random.randrange(0, 256)
            point_color_g = random.randrange(0, 256)
            point_color_b = random.randrange(0, 256)
            point_color = (point_color_r, point_color_g, point_color_b, 255)
            point_count = 0
            for point_i in range(0, point_num):
                if person_conf_multi[people_i][point_i][0] + person_conf_multi[people_i][point_i][1] != 0: # If coordinates of point is (0, 0) == meaningless data
                    point_count = point_count + 1
            if point_count > 5: # If there are more than 5 point in person, we define he/she is REAL PERSON
                people_real_num = people_real_num + 1
                for point_i in range(0, point_num):
                    draw.ellipse((person_conf_multi[people_i][point_i][0] - point_r, person_conf_multi[people_i][point_i][1] - point_r, person_conf_multi[people_i][point_i][0] + point_r, person_conf_multi[people_i][point_i][1] + point_r), fill=point_color)

        print('people_real_num: ')
        print(people_real_num)

        video_name_result = 'testset/' + video_name + '/frame_pose_' + str(i).zfill(video_frame_ciphers) + '.jpg'
        image_img.save(video_name_result, "PNG")

video_name = sys.argv[1] ## example: test_video_01
frame2pose(video_name)