import random
from os import makedirs
from os.path import exists

import h5py

#from tensorflow import keras
import keras

import sys
from properties import DATASET, POPSIZE, MODEL, MODEL2, EXPLABEL
import numpy as np
from utils import input_reshape, reshape
import time
import csv
import os

def calculate_dist(index_item1, index_item2):

    def memoized_dist(index_item1, index_item2):
        index_str = tuple(sorted([index_item1, index_item2]))
        if index_str in cache:
            return cache[index_str]
        ind = reshape(x_train[index_item1])
        initial_ind = reshape(x_train[index_item2])
        result = np.linalg.norm(initial_ind - ind)
        cache.update({index_str : result})
        return result

    return memoized_dist(index_item1, index_item2)


def olddist_(index_item1, index_item2):
    ind = reshape(x_train[index_item1])
    initial_ind = reshape(x_train[index_item2])
    return np.linalg.norm(initial_ind - ind)


def get_min_distance_from_set(ind_index, initial_pop):
    distances = list()
    for initial_ind_index in initial_pop:
        d = calculate_dist(ind_index, initial_ind_index)
        distances.append(d)
    distances.sort()
    return distances[0]


def generate(diversity=True):
    if EXPLABEL is None:
        correct_set = range(len(x_train))
    else:
        correct_set = np.argwhere(y_train == EXPLABEL)

    print("Evaluating with model "+MODEL)
    model = keras.models.load_model(MODEL)
    prediction = model.predict_classes(input_reshape(x_train))
    correctly_predicted = np.argwhere(prediction == y_train)
    correct_set = np.intersect1d(correctly_predicted, correct_set)

    print("Evaluating with model " + MODEL2)
    model = keras.models.load_model(MODEL2)
    prediction = model.predict_classes(input_reshape(x_train))
    correctly_predicted = np.argwhere(prediction == y_train)
    correct_set = np.intersect1d(correctly_predicted, correct_set)

    if diversity:
        print("Calculating diverse set")
        original_set = list()
        print("Finding element 1")
        starting_point = random.choice(correct_set)
        original_set.append(starting_point.item())
        correct_set = np.setdiff1d(correct_set, original_set)

        popsize = POPSIZE

        i = 0
        while i < popsize-1:
            print("Finding element "+str(i+2))
            max_dist = 0
            for ind in correct_set:
                dist = get_min_distance_from_set(ind, original_set)
                if dist > max_dist:
                    max_dist = dist
                    best_ind = ind
            original_set.append((best_ind))
            correct_set = np.setdiff1d(correct_set, best_ind).tolist()
            i += 1
        xn = x_train[original_set]
        yn = y_train[original_set]
    else:
        xn = x_train[correct_set]
        yn = y_train[correct_set]


    print('Checking correctness...')
    for item in range(len(xn)):
       assert(model.predict_classes(reshape(xn[int(item)])) == yn[int(item)])
       print (model.predict_classes(reshape(xn[int(item)])))

    dst = "original_dataset"
    if not exists(dst):
        makedirs(dst)
    print('Creating dataset...')
    f = h5py.File(DATASET, 'w')
    f.create_dataset("xn", shape=(len(xn),28,28), data=xn)
    f.create_dataset("yn", data=yn)
    f.close()

    print('Done')


if __name__ == "__main__":
    time1 = time.time()
    # load the MNIST dataset
    cache = dict()
    mnist = keras.datasets.mnist
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    if len(sys.argv) == 1:
        generate()
    else:
        generate(diversity=False)

    time2 = time.time()
    elapsed_time = (time2 - time1)

    info_file = 'pop_info.csv'

    if os.path.exists(info_file):
        append_write = 'a'  # append if already exists
    else:
        append_write = 'w'  # make a new file if not

    with open(info_file, append_write) as f1:
        writer = csv.writer(f1, delimiter=',', lineterminator='\n', )
        writer.writerow([str(elapsed_time)])
    print("Time spent: " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))

