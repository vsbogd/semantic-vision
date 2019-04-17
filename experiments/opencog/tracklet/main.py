from tracklets import load_tracklets
import enum
from opencog.type_constructors import *
from opencog.atomspace import AtomSpace
from opencog.utilities import initialize_opencog, finalize_opencog

class RoadUserType(enum.Enum):
    PERSON = 0
    BIKE = 1
    CAR = 2

class TrackletGroundedObjectNode:

    def __init__(self, id, tracklet):
        self.id = id
        self.tracklet = tracklet

    def get_name(self):
        return str(self.id)

    def get_klass(self):
        return RoadUserType(self.id[0])

def concept_of_klass(klass):
    return ConceptNode(str(klass))

def print_atomspace(atomspace):
    for atom in atomspace:
        print(atom)



def add_tracklets_to_atomspace(tracklets):
    atomspace = AtomSpace()
    initialize_opencog(atomspace)
    try:
        for id in tracklets.get_ids():
            tracklet = tracklets.get_tracklet(id)
            add_tracklet_to_atomspace(TrackletGroundedObjectNode(id, tracklet))
        print_atomspace(atomspace)
    finally:
        finalize_opencog()

def add_tracklet_to_atomspace(tracklet):
    gon = GroundedObjectNode(tracklet.get_name(), tracklet, unwrap_args = True)
    klass = ConceptNode(str(tracklet.get_klass()))
    InheritanceLink(gon, klass)



def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pkl', type=str)
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    tracklets = load_tracklets(args.pkl)
    add_tracklets_to_atomspace(tracklets)

