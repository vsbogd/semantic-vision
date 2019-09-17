# Usage example

```sh
python3 main.py \
	--train '/mnt/fileserver/shared/datasets/streetscene/tracklets/tkls_train001.pkl' \
	--test '/mnt/fileserver/shared/datasets/streetscene/tracklets/tkls_test001.pkl'
```

# Input data structure

Input data is a map of tracklet id to tracklet data. Tracklet id is a tuple
of road user type and tracklet id. The reason why one cannot use tracklet id 
alone is that it can be reused for another road user type.

Tracklet id contains of bounding boxes, each bounding box has:
- id of the frame
- center coordinates
- bounding box dimensions
- list of visual features

# OpenCog representation

Each tracklet is represented in atomspace using instance of
TrackletGroundedObjectNode class. TrackletGroundedObjectNode class contains
tracklet id and list of bounding boxes. As TrackletGroundedObjectNode is usual
Python class to inject it into atomspace it is wrapped by GroundedObjectNode.
GroundedObjectNode is atomspace node which represents reference to some object
in atomspace and allows calling methods of the objects using atomspace
MethodOfLink and ApplyLink.

Beside data TrackletGroundedObjectNode has two methods:
- `compare(TrackletGroundedObjectNode other)` - which returns the distance
  between this and `other` tracklets;
- `is_prefix_of(TrackletGroundedObjectNode tail)` - which returns true if this
  tracklet is prefix of `tail` one.

# Algorithms implemented in OpenCog

## Trackelet reid

Algorithm finds all pairs of GroundedObjectNodes for which `is_prefix_of`
method returns true. Following pattern matcher request is used to implement it:
```
        BindLink(
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
 ``` 

## Anomaly detection

For each tracklet from test dataset it is compared to all tracklets from train
dataset using `compare` method. Tracklet is considered to be anomaly if there
is no tracklet for which distance between it and given tracklet is less than
0.1. Algorithm is implemented using following pattern matcher query:
```
        BindLink(
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
```
Where `is_similar_tracklets` function returns true if input value is less than
0.1.
