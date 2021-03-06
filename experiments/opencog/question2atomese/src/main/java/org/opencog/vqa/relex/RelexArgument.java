package org.opencog.vqa.relex;

import java.util.ArrayList;
import java.util.List;

import relex.feature.FeatureNode;

public class RelexArgument {
    
    private final FeatureNode featureNode;
    private final List<RelexPredicate> relations;
    private final String variableName;

    public RelexArgument(FeatureNode featureNode, String variableName) {
        this.featureNode = featureNode;
        this.relations = new ArrayList<>();
        this.variableName = variableName;
    }

    public String getVariableName() {
        return variableName;
    }
    
    public String getName() {
        String name = "XXXX";
        try {
            name = RelexUtils.getFeatureNodeName(featureNode);
        } catch (IllegalArgumentException e) {
        }
        return name;
    }

    public FeatureNode getFeatureNode() {
        return featureNode;
    }
    
    @Override
    public String toString() {
        return getName();
    }

    int getNumberOfUsages() {
        return relations.size();
    }

    void addRelation(RelexPredicate relation) {
        relations.add(relation);
    }

}