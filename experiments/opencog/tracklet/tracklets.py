import pickle
import logging as log


class Frame:
    '''
    The BoundingBox object contains parameters of image, bounding box and features

    Parameters
    ----------
    image_id : int
        The image_id is used for referring to image files like NNNNN.jpg

    bbx : tuple of int
        The bbx contains coordinates of bounding box: center (x, y), width and height (w, h)

    feature : ndarray
        The feature contains feature-vector of current bounding box

    Attributes
    ----------
    The same as parameters
    '''
    def __init__(self, image_id, bbx, features):
        self.image_id = image_id
        self.bbx = bbx
        self.feature = feature

    def get_time(self):
        '''Return absolute time when this bounding box were visible

        Returns
        -------
        time : int
            absolute time of the current bounding box
        '''
        return int(self.get_image_id())

    def get_image_id(self):
        '''To get image id of current bounding box

        Returns
        -------
        image_id : int
            image id for current bounding box
        '''
        return self.image_id

    def get_center(self):
        '''To get current bounding box's center coordinate

        Returns
        -------
        center : (int, int)
            current bounding box's center coordinate
        '''
        return (self.bbx[0], self.bbx[1])

    def get_size(self):
        '''To get current bounding box's size

        Returns
        -------
        size : (int, int)
            current bounding box's size
        '''
        return (self.bbx[2], self.bbx[3])

    def get_features(self):
        '''To get current bounding box's features

        Returns
        -------
        features : ndarray
            current bounding box's features
        '''
        return self.feature

    def __str__(self):
        return '<{0} img={1} bbx={2} features={3}>'.format(
            self.__class__.__name__,
            self.image_id, self.bbx, type(self.feature).__name__
        )

    def __repr__(self):
        return str(self)

class Tracklets:
    '''
    The Tracklets object contains lots of BoundingBox's instances

    Parameters
    ----------
    tracklet_pkl_filename : str
        Path to .pkl file formed by data2tracklets.py

    Attributes
    ----------
    tkls : dict (defaultdict)
        contains all information about tracklets by object class and object id
    '''
    def __init__(self, tracklet_pkl_filename):
        with open(tracklet_pkl_filename, 'rb') as f:
            self.tkls = pickle.load(f)
        self.file = tracklet_pkl_filename

    def get_tracklet(self, tracklet_id):
        '''Return list of BoundingBox(s) by tracklet id

        Parameters
        ----------
        tracklet_id : (int, int)
            identifier of tracklet

        Returns
        -------
        tracklet : list of BoundingBox(s)
            list of bounding boxes for current object
        '''
        return self.tkls[tracklet_id]

    def get_ids(self):
        '''Return list of tracklet ids

        Returns
        -------
        identifiers : list of tuples
            list of tuples that you can use with get_tracklet
        '''
        return list(self.tkls.keys())

    def __str__(self):
        return '<{0} {1} tracks from {2}>'.format(
            self.__class__.__name__,
            len(self.tkls.keys()), self.file
        )

    def __repr__(self):
        return str(self)


def load_tracklets(tracklet_pkl_filename):
    """ Returns Tracklets object based on .pkl content.

    Parameters:
        tracklet_pkl_filename (str):Path to .pkl file (from data2tracklets.py)

    Returns:
        tkls (Tracklets):Returns Tracklets object based on .pkl content.

    """
    return Tracklets(tracklet_pkl_filename)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('tklpkl', type=str)
    args = parser.parse_args()

    tkls = load_tracklets(args.tklpkl)
