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
        return self.tracklet[0]

    def get_last(self):
        return self.tracklet[-1]

    def speed_is_similar(self, tail):
        head = self
        if len(head.tracklet) < 2 or len(tail.tracklet) < 2:
            return False
        end_speed = speed(head.tracklet)
        begin_speed = speed(tail.tracklet)
        between_speed = speed(head.tracklet +  tail.tracklet)
        average_speed = (end_speed + begin_speed) / 2.0
        diff = abs(average_speed - between_speed)
        similar = diff < 0.1
        log.debug("end_speed: %s, begin_speed: %s, between_speed: %s, " %
                  (end_speed, begin_speed, between_speed) +
                  "average_speed: %s, similar: %s, diff: %s" %
                  (average_speed, similar, diff))
        return similar

    def features_are_similar(self, tail):
        head = self
        min = None
        for h in head.tracklet:
            for t in tail.tracklet:
                distance = features_distance(h.get_features(),
                                             t.get_features())
                if min is None or min > distance:
                    min = distance
        return min

    def is_prefix_of(self, tail):
        head = self

        same_klass = head.get_klass() == tail.get_klass()
        if not same_klass:
            return False

        tail_is_later = head.get_last().get_time() < tail.get_first().get_time()
        if not tail_is_later:
            return False

        distance = head.features_are_similar(tail)
        speed_is_similar = head.speed_is_similar(tail)
        log.debug("head: %s, tail: %s, features_distance: %s, speed_is_similar: %s" %
                  (head.get_name(), tail.get_name(), distance,
                   speed_is_similar))
        log.debug("last frame: %s, first frame: %s" %
                  (head.get_last().get_image_id(),
                  tail.get_first().get_image_id()))
        return (distance < 30
                and speed_is_similar)

def print_atomspace(atomspace):
    for atom in atomspace:
        print(atom)

def euclid_distance(a, b):
    distance = 0.0
    for ai, bi in zip(a, b):
        distance += (ai - bi) ** 2
    distance = math.sqrt(distance)
    return distance

def features_distance(a, b):
    distance = euclid_distance(a, b)
    return distance

def points_distance(a, b):
    distance = euclid_distance(a, b)
    return distance

def speed(track):
    distance = 0
    period = 0
    for (a, b) in zip(track[:-1], track[1:]):
        distance += points_distance(a.get_center(), b.get_center())
        period += b.get_time() - a.get_time()
    log.debug("period: %s, distance: %s" % (period, distance))
    return distance / period

def bool_to_truth_value(atom):
    if atom.get_object():
        return TruthValue(1.0, 1.0)
    else:
        return TruthValue(0.0, 1.0)

def is_similar(atom, delta):
    distance = atom.get_object()
    if distance < delta:
        return TruthValue(1.0, 1.0)
    else:
        return TruthValue(0.0, 1.0)

def is_similar_tracklets(atom):
    return is_similar(atom, 0.1)



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
                EvaluationLink(
                    GroundedPredicateNode("py: bool_to_truth_value"),
                    ApplyLink(MethodOfLink(
                        VariableNode("HEAD"),
                        ConceptNode("is_prefix_of")),
                        ListLink(VariableNode("TAIL"))))),
            ListLink(VariableNode("HEAD"), VariableNode("TAIL")))

    def merge(self):
        result = execute_atom(self.atomspace, self.query())
        print("result:", result.out[0].out[0].get_object().get_last(), "\n",
              result.out[0].out[1].get_object().get_first())

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

