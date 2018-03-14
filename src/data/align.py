import argparse
import cv2
import json
import os
from os.path import join

from src.data.utils import crop, clipped_normal, filename_to_group, \
    get_transformed_eye_points, rotate
from src.utils.paths import PATH_DATA


log_interval = 1000


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch 2d-align faces')
    parser.add_argument('-s', '--output_size', type=int, default=256,
                        help='Final image size')
    args = parser.parse_args()

    celeb_json = join(PATH_DATA, 'celeb_params.json')
    image_dir = join(PATH_DATA, 'celeb_id_raw')
    output_dir = join(PATH_DATA, 'celeb_id_aligned')

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    with open(celeb_json, 'r') as f:
        data = json.load(f)

    out_data = {}

    for c, (k, v) in enumerate(data.items()):
        if c % log_interval == 0:
            print('Processed {}/{}'.format(c, len(data)))
            with open(join(output_dir, 'data.json'), 'w') as f:
                json.dump(out_data, f)

        im_f = join(image_dir, k)
        if not os.path.exists(im_f):
            print('Could not find {}'.format(im_f))
            continue

        im = cv2.imread(im_f)
        if im is None:
            print('Error reading {}'.format(im_f))
            continue

        im, M = rotate(im, v, args.output_size)
        im, cx, cy = crop(im, v)
        im_h, _, _ = im.shape
        scale = float(args.output_size) / float(im_h)
        im = cv2.resize(im, (args.output_size, args.output_size),
                        interpolation=cv2.INTER_CUBIC)

        out_v = {}
        out_v['filename'] = k

        eye_left, eye_right = get_transformed_eye_points(v, M, cx, cy, scale)
        if eye_left is not None:
            out_v['eye_left'] = {}
            out_v['eye_left']['x'] = eye_left[0]
            out_v['eye_left']['y'] = eye_left[1]
            out_v['box_left'] = {}
            out_v['box_left']['w'] = clipped_normal(96)
            out_v['box_left']['h'] = clipped_normal(96)
        else:
            out_v['eye_left'] = None

        if eye_right is not None:
            out_v['eye_right'] = {}
            out_v['eye_right']['x'] = eye_right[0]
            out_v['eye_right']['y'] = eye_right[1]
            out_v['box_right'] = {}
            out_v['box_right']['w'] = clipped_normal(96)
            out_v['box_right']['h'] = clipped_normal(96)
        else:
            out_v['eye_right'] = None

        if 'eyes_opened' in v:
            out_v['opened'] = v['eyes_opened']
        else:
            out_v['opened'] = None

        if 'eyes_closed' in v:
            out_v['closed'] = v['eyes_closed']
        else:
            out_v['closed'] = None

        g, i = filename_to_group(k)
        if g not in out_data:
            out_data[g] = []

        out_data[g].append(out_v)

        cv2.imwrite(join(output_dir, k), im)

    with open(join(output_dir, 'data.json'), 'w') as f:
        json.dump(out_data, f)
