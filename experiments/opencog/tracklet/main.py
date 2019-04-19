import enum
import math
import logging as log

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

    def get_first(self):
        log.debug("TrackletGroundedObjectNode.get_first()")
        return self.tracklet[0]

    def get_last(self):
        log.debug("TrackletGroundedObjectNode.get_last()")
        return self.tracklet[-1]

def print_atomspace(atomspace):
    for atom in atomspace:
        print(atom)

def is_similar(atom, delta):
    distance = atom.get_object()
    if distance < delta:
        return TruthValue(1.0, 1.0)
    else:
        return TruthValue(0.0, 1.0)

def is_similar_tracklets(atom):
    return is_similar(atom, 0.1)

def is_similar_points(atom):
    return is_similar(atom, 100)

def is_similar_features(atom):
    return is_similar(atom, 30)

def euclid_distance(a, b):
    log.debug("distance()")
    log.debug("a: %s, b: %s" % (a, b))
    distance = 0.0
    for ai, bi in zip(a, b):
        distance += (ai - bi) ** 2
    distance = math.sqrt(distance)
    log.debug("distance: %s" % distance)
    return distance

def features_distance(a, b):
    distance = euclid_distance(a.get_object(), b.get_object())
    return GroundedObjectNode(str(id(distance)), distance)

def points_distance(a, b):
    distance = euclid_distance(a.get_object(), b.get_object())
    return GroundedObjectNode(str(id(distance)), distance)



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

class TrackletReId:

    def __init__(self, atomspace):
        self.atomspace = atomspace

    def query(self):
        head_last = ApplyLink(MethodOfLink(VariableNode("HEAD"),
                                           ConceptNode("get_last")),
                              ListLink())
        tail_first = ApplyLink(MethodOfLink(VariableNode("TAIL"),
                                            ConceptNode("get_first")),
                               ListLink())
        is_head_similar_to_tail = EvaluationLink(
                    GroundedPredicateNode("py: is_similar_features"),
                    ExecutionOutputLink(
                        GroundedSchemaNode("py: features_distance"),
                        ListLink(
                            ApplyLink(MethodOfLink(
                                head_last,
                                ConceptNode("get_features")),
                                ListLink()),
                            ApplyLink(MethodOfLink(
                                tail_first,
                                ConceptNode("get_features")),
                                ListLink()))))
        is_head_near_tail = EvaluationLink(
                    GroundedPredicateNode("py: is_similar_points"),
                    ExecutionOutputLink(
                        GroundedSchemaNode("py: points_distance"),
                        ListLink(
                            ApplyLink(MethodOfLink(
                                head_last,
                                ConceptNode("get_center")),
                                ListLink()),
                            ApplyLink(MethodOfLink(
                                tail_first,
                                ConceptNode("get_center")),
                                ListLink()))))
        return BindLink(
            VariableList(
                TypedVariableLink(VariableNode("HEAD"),
                                  TypeNode("GroundedObjectNode")),
                TypedVariableLink(VariableNode("TAIL"),
                                  TypeNode("GroundedObjectNode")),
                TypedVariableLink(VariableNode("CLASS"),
                                  TypeNode("ConceptNode"))),
            AndLink(
                NotLink(EqualLink(VariableNode("HEAD"), VariableNode("TAIL"))),
                InheritanceLink(VariableNode("HEAD"), VariableNode("CLASS")),
                InheritanceLink(VariableNode("TAIL"), VariableNode("CLASS")),
                is_head_similar_to_tail,
                is_head_near_tail),
            ListLink(VariableNode("HEAD"), VariableNode("TAIL")))

    def merge(self):
        result = execute_atom(self.atomspace, self.query())
        print("result:", result)

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
                    GroundedPredicateNode("py: is_similar_tracklets"),
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
    parser.add_argument('--log', type=str, default='INFO',
                        help='Log level')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    log.basicConfig(level=log.getLevelName(args.log))

    atomspace = AtomSpace()
    initialize_opencog(atomspace)
    try:
        builder = AtomspaceBuilder(atomspace)
        tracklets = load_tracklets(args.train)
        builder.add_tracklets(tracklets)

        reid = TrackletReId(atomspace)
        reid.merge()

        detector = TrackletAnomalyDetector(atomspace)
        tracklets = load_tracklets(args.test)
        detector.check_anomaly(tracklets)
    finally:
        finalize_opencog()

