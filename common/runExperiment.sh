#!/bin/bash

die () {
    echo >&2 "$@"
    exit 1
}

verify_number () {
    re='^[0-9]+$'
    if ! [[ $1 =~ $re ]] ; then
        die "error: Not a number: $1"
    fi
}

while test $# -gt 0; do
    case "$1" in
        -h|--help)
            echo "$package - run experiment"
            echo " "
            echo "$package [options] application [arguments]"
            echo " "
            echo "options:"
            echo "-h, --help                show brief help"
            echo "-s, --start-stage=NUM     specify the starting stage"
            echo "-e, --end-stage=NUM       specify the ending stage"
            exit 0
            ;;
        -s)
            shift
            if test $# -gt 0; then
                export START_STAGE=$1
                verify_number $START_STAGE
            else
                die "no starting stage specified"
            fi
            shift
            ;;
        --start-stage*)
            export START_STAGE=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $START_STAGE
            shift
            ;;
        -e)
            shift
            if test $# -gt 0; then
                export END_STAGE=$1
                verify_number $END_STAGE
            else
                die "no ending stage specified"
            fi
            shift
            ;;
        --end-stage*)
            export END_STAGE=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $END_STAGE
            shift
            ;;
        --lda)
            export MODEL_TYPE="LDA"
            shift
            ;;
        --lsi)
            export MODEL_TYPE="LSI"
            shift
            ;;
        *)
            break
            ;;
    esac
done

if [ $# -lt 2 ]; then
    die "Usage: $0 [options] ParentCategory Category"
fi

PARENTCAT=$1
CAT=$2

# Assign default values
if [[ -z "$START_STAGE" ]]; then
    START_STAGE=1
fi

if [[ -z "$END_STAGE" ]]; then
    END_STAGE=1000
fi

if [[ -z "$MODEL_TYPE" ]]; then
    MODEL_TYPE="LDA"
fi

# Setup environment
SRC=../common
DATA=data
DB=$DATA/macys.db
CATGRAPH=$DATA/graph${CAT}.pickle
UNDIRECTED_GRAPH=$DATA/graph${CAT}Undirected.pickle
PROX_MAT=$DATA/proxMat${CAT}.npz
GRAPH1=$DATA/graph${CAT}1.pickle
GRAPH2=$DATA/graph${CAT}2.pickle
LOST_EDGES=$DATA/lostEdges${CAT}.pickle
RWALK=$DATA/randomWalk${CAT}.npz
RWALK1=$DATA/randomWalk${CAT}1.npz
RWALK2=$DATA/randomWalk${CAT}2.npz
LDA=$DATA/lda${CAT}.pickle
LDA1=$DATA/lda${CAT}1.pickle
LDA2=$DATA/lda${CAT}2.pickle
LSI=$DATA/svd${CAT}.npz
LSI1=$DATA/svd${CAT}1.npz
LSI2=$DATA/svd${CAT}2.npz
IDFS=$DATA/idfs${CAT}.pickle
TFIDF1=$DATA/tfidf${CAT}1.pickle
TFIDF2=$DATA/tfidf${CAT}2.pickle
MAP=$DATA/topicMap${CAT}.pickle
PREDICTED_RAND=$DATA/predictedEdgesRand${CAT}.pickle
PREDICTED_TFIDF=$DATA/predictedEdgesTfidf${CAT}.pickle
PREDICTED_ONE=$DATA/predictedEdgesOneModel${CAT}.pickle
PREDICTED_EDGES=$DATA/predictedEdges${CAT}.pickle

# Construct directed recomender graph from DB --> recGraph
if [ $START_STAGE -le 1 -a $END_STAGE -ge 1 ]; then
    echo "=== 1. Build directed recommender graph for category from DB ==="
    python $SRC/buildRecGraph.py --directed --savefile=$CATGRAPH\
        --parent-category=$PARENTCAT --category=$CAT $DB
echo
fi

# Construct proximity matrix for k-precision/recall evaluation
if [ $START_STAGE -le 2 -a $END_STAGE -ge 2 ]; then
    echo "=== 2. Build proximity matrix from graph ==="
    python $SRC/buildRecGraph.py --savefile=$UNDIRECTED_GRAPH\
        --parent-category=$PARENTCAT --category=$CAT $DB
    python $SRC/buildWalkMatrix.py --type=proximity --savefile=$PROX_MAT\
        $UNDIRECTED_GRAPH
echo
fi

# Partition graph
if [ $START_STAGE -le 3 -a $END_STAGE -ge 3 ]; then
    echo "=== 3. Partition category graph ==="
    python $SRC/partitionGraph.py --graph1=$GRAPH1 --graph2=$GRAPH2\
        --lost_edges=$LOST_EDGES $CATGRAPH
echo
fi

# Random walk
if [ $START_STAGE -le 4 -a $END_STAGE -ge 4 ]; then
    echo "=== 4. Randomly walk each graph ==="
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK1\
        $GRAPH1
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK2\
        $GRAPH2
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK\
        $UNDIRECTED_GRAPH
echo
fi

# Train model on each graph
if [ $START_STAGE -le 5 -a $END_STAGE -ge 5 ]; then
    echo "=== 5. Train $MODEL_TYPE model for each graph ==="
    if [ "$MODEL_TYPE" = "LDA" ]; then
        python $SRC/buildLDAModel.py --matrixfile=$RWALK1 --lda-file=$LDA1
        python $SRC/buildLDAModel.py --matrixfile=$RWALK2 --lda-file=$LDA2
        python $SRC/buildLDAModel.py --matrixfile=$RWALK --lda-file=$LDA
        MODEL1=$LDA1
        MODEL2=$LDA2
        MODEL=$LDA
    elif [ "$MODEL_TYPE" = "LSI" ]; then
        python $SRC/svd.py --savefile=$LSI1 -k 20 $RWALK1
        python $SRC/svd.py --savefile=$LSI2 -k 20 $RWALK2
        python $SRC/svd.py --savefile=$LSI -k 20 $RWALK
        MODEL1=$LSI1
        MODEL2=$LSI2
        MODEL=$LSI
    else
        die "Invalid model type: $MODEL_TYPE"
    fi
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
    python $SRC/topicWords.py --database=$DB --idfname=$IDFS\
        --outputpickle=$TFIDF1 $MODEL1
    python $SRC/topicWords.py --database=$DB --idfname=$IDFS\
        --outputpickle=$TFIDF2 $MODEL2
echo
fi

# Map tfidf topic spaces
if [ $START_STAGE -le 8 -a $END_STAGE -ge 8 ]; then
    echo "=== 8. Construct topic map from graph1 to graph2 ==="
    python $SRC/mapTopics.py --outputpickle=$MAP $TFIDF1 $TFIDF2
echo
fi

# Predict edges
if [ $START_STAGE -le 9 -a $END_STAGE -ge 9 ]; then
    echo "=== 9. Predict edges ==="
    echo "Predicting randomly. . ."
    python $SRC/predictEdgesRandomly.py --savefile=$PREDICTED_RAND\
        $GRAPH1 $GRAPH2
    echo "Predicting using item-item tfidf. . ."
    python $SRC/predictEdgesTfidf.py --savefile=$PREDICTED_TFIDF --database=$DB\
        --idfname=$IDFS $GRAPH1 $GRAPH2
    echo "Predicting using one model. . ."
    python $SRC/predictEdgesOneModel.py --savefile=$PREDICTED_ONE $MODEL\
        $GRAPH1 $GRAPH2
    echo "Predicting with mapping between models. . ."
    python $SRC/predictEdges.py --savefile=$PREDICTED_EDGES $MAP $MODEL1 $MODEL2
echo
fi

# Evaluate predictions
if [ $START_STAGE -le 10 -a $END_STAGE -ge 10 ]; then
    echo "=== 10. Evaluate predictions ==="
    echo
    echo "  RANDOM PREDICTIONS "
    python $SRC/evalPredictedEdges.py -k 2 $PROX_MAT $PREDICTED_RAND\
        $LOST_EDGES
    echo
    echo "  TFIDF PREDICTIONS "
    python $SRC/evalPredictedEdges.py -k 2 $PROX_MAT $PREDICTED_TFIDF\
        $LOST_EDGES
    echo
    echo "  ONE MODEL PREDICTIONS "
    python $SRC/evalPredictedEdges.py -k 2 $PROX_MAT $PREDICTED_ONE\
        $LOST_EDGES
    echo
    echo "  MAPPING MODEL PREDICTIONS "
    python $SRC/evalPredictedEdges.py -k 2 $PROX_MAT $PREDICTED_EDGES\
        $LOST_EDGES
fi
