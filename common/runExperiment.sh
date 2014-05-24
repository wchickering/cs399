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
            echo "-h, --help                Show brief help"
            echo "-s, --start-stage=NUM     Specify the starting stage"
            echo "-e, --end-stage=NUM       Specify the ending stage"
            echo "--directed                Run experiment on directed graphs"
            echo "--no-popularity-added     Don't add popularity back into graph"
            echo "--no-popularity-removed   Don't remove popularity in graph"
            echo "                          traversal"
            echo "--lda                     Use lda instead of lsi for latent"
            echo "                          space"
            echo "--zero-mean               Subtract mean before lsi"
            echo "--min-component-size=NUM  Specifiy minimum component size"
            echo "                          allowed in graph"
            echo "--max-mapping-connections=NUM   Specify the maximum number"
            echo "                          of topics one topic can map to"
            echo "--eval-k=NUM              Specify k for k-precision and"
            echo "                          k-recall in evaluation"
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
        --no-popularity-added)
            # this should be left undefined by default
            export POPULARITY='false'
            shift
            ;;
        --no-popularity-removed)
            # this should be left undefined by default
            export REMOVE_POP='false'
            shift
            ;;
        --lda)
            export MODEL_TYPE="lda"
            shift
            ;;
        --zero-mean)
            export PCA="--pca"
            shift
            ;;
        --min-component-size*)
            export MIN_COMPONENT_SIZE=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $MIN_COMPONENT_SIZE
            shift
            ;;
        --max-mapping-connections*)
            export MAX_CONN=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $MAX_CONN
            shift
            ;;
        --eval-k*)
            export EVAL_K=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $EVAL_K
            shift
            ;;
        --seed*)
            # this should be left undefined by default
            SEED=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $SEED
            export SEED_OPT="--seed=$SEED"
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
    NUM_TOPICS=8
fi

if [[ -z "$MODEL_TYPE" ]]; then
    MODEL_TYPE="lsi"
fi

if [[ -z "$MIN_COMPONENT_SIZE" ]]; then
    MIN_COMPONENT_SIZE=100
fi

if [[ -z "$MAX_CONN" ]]; then
    MAX_CONN=$NUM_TOPICS
fi

if [[ -z "$EVAL_K" ]]; then
    EVAL_K=2
fi

if [[ -z "$POPULARITY" ]]; then
    POPULARITY='true'
fi

if [ "$REMOVE_POP" = "false" ]; then
    REMOVE_POP=''
else
    REMOVE_POP='--tran2'
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
POP_GRAPH=${GRAPH_BASE}Pop.pickle
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
else
    MODEL=$LSI
    MODEL1=$LSI1
    MODEL2=$LSI2
fi


# Construct recomendation graph from DB
if [ $START_STAGE -le 1 -a $END_STAGE -ge 1 ]; then
    echo "=== 1. Build directed recommender graph for category from DB ==="
    python $SRC/buildRecGraph.py $DIRECTED\
        --min-component-size=$MIN_COMPONENT_SIZE --savefile=$GRAPH\
        --parent-category=$PARENTCAT --category=$CAT $DB
echo
fi

# Construct proximity matrix for k-precision/recall evaluation
if [ $START_STAGE -le 2 -a $END_STAGE -ge 2 ]; then
    echo "=== 2. Build proximity matrix from graph ==="
    python $SRC/buildWalkMatrix.py $SEED_OPT --type=proximity\
        --savefile=$PROX_MAT $GRAPH
echo
fi

# Partition graph
if [ $START_STAGE -le 3 -a $END_STAGE -ge 3 ]; then
    echo "=== 3. Partition category graph ==="
    python $SRC/partitionGraph.py $SEED_OPT --graph1=$GRAPH1 --graph2=$GRAPH2\
        --min-component-size=$MIN_COMPONENT_SIZE --lost_edges=$LOST_EDGES $GRAPH
echo
fi

# Random walk
if [ $START_STAGE -le 4 -a $END_STAGE -ge 4 ]; then
    echo "=== 4. Randomly walk each graph ==="
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK\
        $REMOVE_POP $GRAPH
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK1\
        $REMOVE_POP $GRAPH1
    python $SRC/buildWalkMatrix.py --home=0.05 --steps=50 --savefile=$RWALK2\
        $REMOVE_POP $GRAPH2
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
    else
        python $SRC/svd.py -k $NUM_TOPICS $PCA --savefile=$MODEL $RWALK
        python $SRC/svd.py -k $NUM_TOPICS $PCA --savefile=$MODEL1 $RWALK1
        python $SRC/svd.py -k $NUM_TOPICS $PCA --savefile=$MODEL2 $RWALK2
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
    python $SRC/mapTopics.py --max_connections $MAX_CONN --outputpickle=$MAP\
        $TFIDF1 $TFIDF2
echo
fi

# Predict edges
if [ $START_STAGE -le 9 -a $END_STAGE -ge 9 ]; then
    echo "=== 9. Predict edges ==="
    if [ "$POPULARITY" = "true" ]; then
        echo "Building directed popularity graph"
        python $SRC/buildRecGraph.py $DIRECTED --savefile=$POP_GRAPH\
            --min-component-size=0 \
            --parent-category=$PARENTCAT --category=$CAT $DB
        POP="--popgraph=$POP_GRAPH"
    fi
    echo "Predicting randomly. . ."
    python $SRC/predictEdgesRandomly.py $SEED_OPT --savefile=$PREDICTED_RAND\
        $GRAPH1 $GRAPH2
    echo "Predicting using item-item tfidf. . ."
    python $SRC/predictEdgesTfidf.py --savefile=$PREDICTED_TFIDF --database=$DB\
        --idfname=$IDFS $POP $GRAPH1 $GRAPH2
    echo "Predicting using one model. . ."
    python $SRC/predictEdgesOneModel.py --savefile=$PREDICTED_ONE $POP $MODEL\
        $GRAPH1 $GRAPH2
    echo "Predicting with mapping between models. . ."
    python $SRC/predictEdges.py --savefile=$PREDICTED_EDGES $POP $MAP $MODEL1\
        $MODEL2
echo
fi

# Evaluate predictions
if [ $START_STAGE -le 10 -a $END_STAGE -ge 10 ]; then
    echo "=== 10. Evaluate predictions ==="
    echo
    echo "  RANDOM PREDICTIONS "
    python $SRC/evalPredictedEdges.py -k $EVAL_K $PROX_MAT $PREDICTED_RAND\
        $LOST_EDGES
    echo
    echo "  TFIDF PREDICTIONS "
    python $SRC/evalPredictedEdges.py -k $EVAL_K $PROX_MAT $PREDICTED_TFIDF\
        $LOST_EDGES
    echo
    echo "  ONE MODEL PREDICTIONS "
    python $SRC/evalPredictedEdges.py -k $EVAL_K $PROX_MAT $PREDICTED_ONE\
        $LOST_EDGES
    echo
    echo "  MAPPING MODEL PREDICTIONS "
    python $SRC/evalPredictedEdges.py -k $EVAL_K $PROX_MAT $PREDICTED_EDGES\
        $LOST_EDGES
fi
