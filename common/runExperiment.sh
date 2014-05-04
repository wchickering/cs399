#!/bin/bash

die () {
    echo >&2 "$@"
    exit 1
}

if [ $# -lt 2 ]; then
    die "Usage: $0 ParentCategory Category [StartStage [EndStage]]"
fi

PARENTCAT=$1
CAT=$2
if [ $# -eq 3 ]; then
    START_STAGE=$3
    END_STAGE=1000
elif [ $# -eq 4 ]; then
    START_STAGE=$3
    END_STAGE=$4
else
    START_STAGE=1
    END_STAGE=1000
fi

SRC=../common
DATA=data
DB=$DATA/macys.db
CATGRAPH=$DATA/graph${CAT}.pickle
GRAPH1=$DATA/graph${CAT}1.pickle
GRAPH2=$DATA/graph${CAT}2.pickle
LOST_EDGES=$DATA/lostEdges${CAT}.pickle
RWALK1=$DATA/randomWalk${CAT}1.npz
RWALK2=$DATA/randomWalk${CAT}2.npz
LDA1=$DATA/lda${CAT}1.pickle
LDA2=$DATA/lda${CAT}2.pickle
IDFS=$DATA/idfs${CAT}.pickle
TFIDF1=$DATA/tfidf${CAT}1.pickle
TFIDF2=$DATA/tfidf${CAT}2.pickle
MAP=$DATA/topicMap${CAT}.pickle
PREDICTED_EDGES=$DATA/predictedEdges${CAT}.pickle

# Construct directed recomender graph from DB --> recGraph
if [ $START_STAGE -le 1 -a $END_STAGE -ge 1 ]; then
    echo "=== 1. Build directed recommender graph for category from DB ==="
    python $SRC/buildRecGraph.py --directed --savefile=$CATGRAPH\
        --parent-category=$PARENTCAT --category=$CAT $DB
echo
fi
# Partition graph
if [ $START_STAGE -le 3 -a $END_STAGE -ge 3 ]; then
    echo "=== 3. Partition category graph ==="
    python $SRC/partitionGraph.py -g $CATGRAPH --graph1=$GRAPH1\
        --graph2=$GRAPH2 --lost_edges=$LOST_EDGES
echo
fi
# Random walk
if [ $START_STAGE -le 4 -a $END_STAGE -ge 4 ]; then
    echo "=== 4. Randomly walk each graph ==="
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK1\
        $GRAPH1
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK2\
        $GRAPH2
echo
fi
# Train model on each graph
if [ $START_STAGE -le 5 -a $END_STAGE -ge 5 ]; then
    echo "=== 5. Train LDA model for each graph ==="
    python $SRC/buildLDAModel.py -m $RWALK1 -l $LDA1
    python $SRC/buildLDAModel.py -m $RWALK2 -l $LDA2
echo
fi
# Get idfs for category
if [ $START_STAGE -le 6 -a $END_STAGE -ge 6 ]; then
    echo "=== 6. Calculate idfs for category ==="
    python $SRC/idfsByCategory.py -o $IDFS $PARENTCAT $CAT
echo
fi
# Get tfidfs for each graph
if [ $START_STAGE -le 7 -a $END_STAGE -ge 7 ]; then
    echo "=== 7. Calculate tfidfs for each graph ==="
    python $SRC/topicWords.py -d $DB -i $IDFS -o $TFIDF1 $LDA1
    python $SRC/topicWords.py -d $DB -i $IDFS -o $TFIDF2 $LDA2
echo
fi
# Map tfidf topic spaces
if [ $START_STAGE -le 8 -a $END_STAGE -ge 8 ]; then
    echo "=== 8. Construct topic map from graph1 to graph2 ==="
    python $SRC/mapTopics.py -o $MAP $TFIDF1 $TFIDF2
echo
fi
# Predict edges
if [ $START_STAGE -le 9 -a $END_STAGE -ge 9 ]; then
    echo "=== 9. Predict edges ==="
    python $SRC/predictEdges.py --graph1=$GRAPH1 --graph2=$GRAPH2 --lda1=$LDA1\
            --lda2=$LDA2 --topicmap=$MAP -o $PREDICTED_EDGES
echo
fi
# Predict edges
if [ $START_STAGE -le 10 -a $END_STAGE -ge 10 ]; then
    echo "=== 10. Evaluate predictions ==="
    python $SRC/evalPredictedEdges.py $LOST_EDGES $PREDICTED_EDGES
fi
