import enum

from tracklets import load_tracklets

from opencog.type_constructors import *
from opencog.atomspace import AtomSpace
from opencog.utilities import initialize_opencog, finalize_opencog
from opencog.bindlink import execute_atom

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

    def compare(self, other):
        # TODO: implement propely
        return 0.01

def print_atomspace(atomspace):
    for atom in atomspace:
        print(atom)

def is_similar(atom):
    distance = atom.get_object()
    if distance < 0.1:
        return TruthValue(1.0, 1.0)
    else:
        return TruthValue(0.0, 1.0)

class AtomspaceBuilder:

    def __init__(self, atomspace):
        self.atomspace = atomspace

    def add_tracklets(self, tracklets):
        for id in tracklets.get_ids():
            tracklet = tracklets.get_tracklet(id)
            self.add_tracklet(TrackletGroundedObjectNode(id, tracklet))
        print_atomspace(atomspace)

    def add_tracklet(self, tracklet):
        gon = GroundedObjectNode(tracklet.get_name(), tracklet, unwrap_args = True)
        klass = ConceptNode(str(tracklet.get_klass()))
        InheritanceLink(gon, klass)

    def get_atomspace(self):
        return self.atomspace

class TrackletAnomalyDetector:

    def __init__(self, atomspace):
        self.atomspace = atomspace

    def check_anomaly(self, tracklets):
        id = tracklets.get_ids()[100]
        tracklet = tracklets.get_tracklet(id)
        anomaly = self.check_tracklet(TrackletGroundedObjectNode(id, tracklet))
        print("tracklet:", id, tracklet, "anomaly:", anomaly)

    def check_tracklet(self, tracklet):
        query = BindLink(
            VariableNode("X"),
            AndLink(
                InheritanceLink(VariableNode("X"),
                                ConceptNode(str(tracklet.get_klass()))),
                EvaluationLink(
                    GroundedPredicateNode("py: is_similar"),
                    ApplyLink(
                        MethodOfLink(
                            GroundedObjectNode(tracklet.get_name(), tracklet,
                                               unwrap_args = True),
                            ConceptNode("compare")),
                            ListLink(VariableNode("X"))))),
            VariableNode("X"))
        similar = execute_atom(self.atomspace, query)
        print("similar:", similar)
        return similar.arity < 1




def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', type=str,
                        help='Pickle database with train set')
    parser.add_argument('--test', type=str,
                        help='Pickle database with test set')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    atomspace = AtomSpace()
    initialize_opencog(atomspace)
    try:
        builder = AtomspaceBuilder(atomspace)
        tracklets = load_tracklets(args.train)
        builder.add_tracklets(tracklets)

        detector = TrackletAnomalyDetector(atomspace)
        tracklets = load_tracklets(args.test)
        detector.check_anomaly(tracklets)
    finally:
        finalize_opencog()

