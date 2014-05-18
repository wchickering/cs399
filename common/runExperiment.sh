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
        -k)
            shift
            if test $# -gt 0; then
                export NUM_TOPICS=$1
                verify_number $NUM_TOPICS
            else
                die "number of topics not specified"
            fi
            shift
            ;;
        --numtopics*)
            export NUM_TOPICS=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $NUM_TOPICS
            shift
            ;;
        --directed)
            # this should be left undefined by default
            export DIRECTED='--directed'
            shift
            ;;
        --lda)
            export MODEL_TYPE="lda"
            shift
            ;;
        --lsi)
            export MODEL_TYPE="lsi"
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

if [[ -z "$NUM_TOPICS" ]]; then
    NUM_TOPICS=16
fi

if [[ -z "$MODEL_TYPE" ]]; then
    MODEL_TYPE="lsi"
fi

# Setup environment
SRC=../common
DATA=data
EXPMT=${MODEL_TYPE}_${NUM_TOPICS}_${CAT}
DB=$DATA/macys.db
PROX_MAT=$DATA/proxMat${CAT}.npz
GRAPH_BASE=$DATA/graph${CAT}
GRAPH=${GRAPH_BASE}.pickle
GRAPH1=${GRAPH_BASE}1.pickle
GRAPH2=${GRAPH_BASE}2.pickle
LOST_EDGES=$DATA/lostEdges${CAT}.pickle
RWALK_BASE=$DATA/randomWalk${CAT}
RWALK=${RWALK_BASE}.npz
RWALK1=${RWALK_BASE}1.npz
RWALK2=${RWALK_BASE}2.npz
LDA_BASE=$DATA/$EXPMT
LDA=${LDA_BASE}.pickle
LDA1=${LDA_BASE}1.pickle
LDA2=${LDA_BASE}2.pickle
LSI_BASE=$DATA/$EXPMT
LSI=${LSI_BASE}.npz
LSI1=${LSI_BASE}1.npz
LSI2=${LSI_BASE}2.npz
IDFS=$DATA/idfs${CAT}.pickle
TFIDF_BASE=$DATA/tfidf_${EXPMT}
TFIDF=${TFIDF_BASE}.pickle
TFIDF1=${TFIDF_BASE}1.pickle
TFIDF2=${TFIDF_BASE}2.pickle
MAP=$DATA/topicMap_${EXPMT}.pickle
PREDICTED_RAND=$DATA/predictedEdgesRand_${EXPMT}.pickle
PREDICTED_TFIDF=$DATA/predictedEdgesTfidf_${EXPMT}.pickle
PREDICTED_ONE=$DATA/predictedEdgesOneModel_${EXPMT}.pickle
PREDICTED_EDGES=$DATA/predictedEdges_${EXPMT}.pickle

if [ "$MODEL_TYPE" = "lda" ]; then
    MODEL=$LDA
    MODEL1=$LDA1
    MODEL2=$LDA2
elif [ "$MODEL_TYPE" = "lsi" ]; then
    MODEL=$LSI
    MODEL1=$LSI1
    MODEL2=$LSI2
fi


# Construct directed recomender graph from DB --> recGraph
if [ $START_STAGE -le 1 -a $END_STAGE -ge 1 ]; then
    echo "=== 1. Build directed recommender graph for category from DB ==="
    python $SRC/buildRecGraph.py $DIRECTED --savefile=$GRAPH\
        --parent-category=$PARENTCAT --category=$CAT $DB
echo
fi

# Construct proximity matrix for k-precision/recall evaluation
if [ $START_STAGE -le 2 -a $END_STAGE -ge 2 ]; then
    echo "=== 2. Build proximity matrix from graph ==="
    python $SRC/buildWalkMatrix.py --type=proximity --savefile=$PROX_MAT\
        $GRAPH
echo
fi

# Partition graph
if [ $START_STAGE -le 3 -a $END_STAGE -ge 3 ]; then
    echo "=== 3. Partition category graph ==="
    python $SRC/partitionGraph.py --graph1=$GRAPH1 --graph2=$GRAPH2\
        --lost_edges=$LOST_EDGES $GRAPH
echo
fi

# Random walk
if [ $START_STAGE -le 4 -a $END_STAGE -ge 4 ]; then
    echo "=== 4. Randomly walk each graph ==="
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK\
        $GRAPH
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK1\
        $GRAPH1
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK2\
        $GRAPH2
echo
fi

# Train model on each graph
if [ $START_STAGE -le 5 -a $END_STAGE -ge 5 ]; then
    echo "=== 5. Train $MODEL_TYPE model for each graph ==="
    if [ "$MODEL_TYPE" = "lda" ]; then
        python $SRC/buildLDAModel.py --num-topics=$NUM_TOPICS\
            --matrixfile=$RWALK --lda-file=$MODEL
        python $SRC/buildLDAModel.py --num-topics=$NUM_TOPICS\
            --matrixfile=$RWALK1 --lda-file=$MODEL1
        python $SRC/buildLDAModel.py --num-topics=$NUM_TOPICS\
            --matrixfile=$RWALK2 --lda-file=$MODEL2
    elif [ "$MODEL_TYPE" = "lsi" ]; then
        python $SRC/svd.py -k $NUM_TOPICS --savefile=$MODEL $RWALK
        python $SRC/svd.py -k $NUM_TOPICS --savefile=$MODEL1 $RWALK1
        python $SRC/svd.py -k $NUM_TOPICS --savefile=$MODEL2 $RWALK2
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
    python $SRC/mapTopics.py --max_connections 1 --outputpickle=$MAP $TFIDF1\
        $TFIDF2
echo
fi

# Predict edges
if [ $START_STAGE -le 9 -a $END_STAGE -ge 9 ]; then
    echo "=== 9. Predict edges ==="
    echo "Predicting randomly. . ."
    python $SRC/predictEdgesRandomly.py --savefile=$PREDICTED_RAND $GRAPH1\
        $GRAPH2
    echo "Predicting using item-item tfidf. . ."
    python $SRC/predictEdgesTfidf.py --savefile=$PREDICTED_TFIDF --database=$DB\
        --idfname=$IDFS $GRAPH1 $GRAPH2
    echo "Predicting using one model. . ."
    python $SRC/predictEdgesOneModel.py --savefile=$PREDICTED_ONE $MODEL\
        $GRAPH1 $GRAPH2
    echo "Predicting with mapping between models. . ."
    python $SRC/predictEdges.py --savefile=$PREDICTED_EDGES $MAP $MODEL1 $MODEL2
    echo python $SRC/predictEdges.py --savefile=$PREDICTED_EDGES $MAP $MODEL1\
        $MODEL2
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
