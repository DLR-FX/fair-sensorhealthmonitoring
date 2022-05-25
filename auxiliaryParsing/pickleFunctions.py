import bz2
import pickle
import _pickle as cPickle


# Saves the "data" with the "title" and adds the .pickle
def full_pickle(title, data):
    with open(title, 'wb') as pikd:
        pickle.dump(data, pikd)


# loads and returns a pickled objects
def loosen(file):
    with open(file, 'rb') as pikd:
        return pickle.load(pikd)


# Pickle a file and then compress it into a file with extension
def compressed_pickle(title, data):
    with bz2.BZ2File(title + '.pbz2', 'w') as f:
        cPickle.dump(data, f)


# Load any compressed pickle file
def decompress_pickle(file):
    with bz2.BZ2File(file, 'rb') as data:
        return cPickle.load(data)
