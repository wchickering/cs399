#!/bin/bash

# exit script if a command returns nonzero exit value
set -e

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
            echo "--no-partition-by-brand   Do not partition graph by brand"
            echo "--brand-only              Only consider brand for TFIDF"
            echo "--no-zero-mean            Do not subtract mean before SVD"
            echo "--min-component-size=NUM  Specifiy minimum component size"
            echo "                          allowed in graph"
            echo "--max-mapping-connections=NUM"  
            echo "                          Specify the maximum number of"
            echo "                          topics one topic can map to"
            echo "--tourney-mapper=FILE     Use mapper created from tourney"  
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
        --no-partition-by-brand)
            export PARTITION_BY_BRAND_FLAG=0
            shift
            ;;
        --brand-only)
            export BRAND_ONLY="--brand-only"
            shift
            ;;
        --tourney-mapper*)
            export TOURNEY_MAPPER=`echo $1 | sed -e 's/^[^=]*=//g'`
            shift
            ;;
        --no-zero-mean)
            export ZERO_MEAN_FLAG=0
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

if [[ -z "$PARTITION_BY_BRAND_FLAG" ]]; then
    PARTITION_BY_BRAND='--partition-by-brand'
fi

if [[ -z "$ZERO_MEAN_FLAG" ]]; then
    ZERO_MEAN='--zero-mean'
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


######
# Setup environment
##############
SRC=../common
DATA=data
SEED_EXT=Seed${SEED}
EXPMT=${MODEL_TYPE}_${NUM_TOPICS}_${CAT}_$SEED_EXT
DB=$DATA/macys.db

# proximity matrices
PROX_MAT_BASE=$DATA/proxMat${CAT}K${EVAL_K}${SEED_EXT}
TARGET_PROX_MAT=${PROX_MAT_BASE}_tgt.npz
RAND_PROX_MAT=${PROX_MAT_BASE}_rand.npz
TFIDF_PROX_MAT=${PROX_MAT_BASE}_tfidf.npz
ONE_PROX_MAT=${PROX_MAT_BASE}_one.npz
SOURCE_PROX_MAT=${PROX_MAT_BASE}_src.npz

# graphs
GRAPH_BASE=$DATA/graph${CAT}
GRAPH=${GRAPH_BASE}.pickle
GRAPH1=${GRAPH_BASE}${SEED_EXT}_1.pickle
GRAPH2=${GRAPH_BASE}${SEED_EXT}_2.pickle
POP_GRAPH=${GRAPH_BASE}Pop.pickle
RAND_GRAPH=${GRAPH_BASE}${SEED_EXT}_rand.pickle
TFIDF_GRAPH=${GRAPH_BASE}${SEED_EXT}_tfidf.pickle
ONE_GRAPH=${GRAPH_BASE}${SEED_EXT}_one.pickle
SOURCE_GRAPH=${GRAPH_BASE}${SEED_EXT}_src.pickle

LOST_EDGES=$DATA/lostEdges${CAT}${SEED_EXT}.pickle

# random walks
RWALK_BASE=$DATA/randomWalk${CAT}
RWALK=${RWALK_BASE}.npz
RWALK1=${RWALK_BASE}${SEED_EXT}_1.npz
RWALK2=${RWALK_BASE}${SEED_EXT}_2.npz

# lda models
LDA_BASE=$DATA/$EXPMT
LDA=${LDA_BASE}.pickle
LDA1=${LDA_BASE}_1.pickle
LDA2=${LDA_BASE}_2.pickle

# lsi models
LSI_BASE=$DATA/$EXPMT
LSI=${LSI_BASE}.npz
LSI1=${LSI_BASE}_1.npz
LSI2=${LSI_BASE}_2.npz

# tfidf
IDFS=$DATA/idfs${CAT}.pickle
TFIDF_BASE=$DATA/tfidf_${EXPMT}
TFIDF=${TFIDF_BASE}.pickle
TFIDF1=${TFIDF_BASE}_1.pickle
TFIDF2=${TFIDF_BASE}_2.pickle

MAP=$DATA/topicMap_${EXPMT}.pickle

# predicted edges
PREDICTED_BASE=$DATA/predictedEdges_${EXPMT}
PREDICTED_RAND=${PREDICTED_BASE}_rand.pickle
PREDICTED_TFIDF=${PREDICTED_BASE}_tfidf.pickle
PREDICTED_ONE=${PREDICTED_BASE}_one.pickle
PREDICTED_EDGES=${PREDICTED_BASE}.pickle

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
    CMD="python $SRC/buildRecGraph.py $DIRECTED\
        --min-component-size=$MIN_COMPONENT_SIZE --savefile=$GRAPH\
        --parent-category=$PARENTCAT --category=$CAT $DB"
    echo $CMD; eval $CMD
echo
fi

# Construct proximity matrix for k-precision/recall evaluation
if [ $START_STAGE -le 2 -a $END_STAGE -ge 2 ]; then
    echo "=== 2. Build proximity matrix from graph ==="
    CMD="python $SRC/buildWalkMatrix.py $SEED_OPT --type=proximity\
        --maxdist=$EVAL_K --savefile=$TARGET_PROX_MAT $GRAPH"
    echo $CMD; eval $CMD
echo
fi

# Partition graph
if [ $START_STAGE -le 3 -a $END_STAGE -ge 3 ]; then
    echo "=== 3. Partition category graph ==="
    CMD="python $SRC/partitionGraph.py $SEED_OPT $PARTITION_BY_BRAND\
        --graph1=$GRAPH1 --graph2=$GRAPH2\
        --min-component-size=$MIN_COMPONENT_SIZE --lost_edges=$LOST_EDGES\
        $GRAPH"
    echo $CMD; eval $CMD
echo
fi

# Random walk
if [ $START_STAGE -le 4 -a $END_STAGE -ge 4 ]; then
    echo "=== 4. Randomly walk each graph ==="
    CMD="python $SRC/buildWalkMatrix.py --home=0.05 --steps=50\
        --savefile=$RWALK $REMOVE_POP $GRAPH"
    echo $CMD; eval $CMD
    CMD="python $SRC/buildWalkMatrix.py --home=0.05 --steps=50\
        --savefile=$RWALK1 $REMOVE_POP $GRAPH1"
    echo $CMD; eval $CMD
    CMD="python $SRC/buildWalkMatrix.py --home=0.05 --steps=50\
        --savefile=$RWALK2 $REMOVE_POP $GRAPH2"
    echo $CMD; eval $CMD
echo
fi

# Train model on each graph
if [ $START_STAGE -le 5 -a $END_STAGE -ge 5 ]; then
    echo "=== 5. Train $MODEL_TYPE model for each graph ==="
    if [ "$MODEL_TYPE" = "lda" ]; then
        CMD="python $SRC/buildLDAModel.py --num-topics=$NUM_TOPICS\
            --matrixfile=$RWALK --lda-file=$MODEL"
        echo $CMD; eval $CMD
        CMD="python $SRC/buildLDAModel.py --num-topics=$NUM_TOPICS\
            --matrixfile=$RWALK1 --lda-file=$MODEL1"
        echo $CMD; eval $CMD
        CMD="python $SRC/buildLDAModel.py --num-topics=$NUM_TOPICS\
            --matrixfile=$RWALK2 --lda-file=$MODEL2"
        echo $CMD; eval $CMD
    else
        CMD="python $SRC/svd.py -k $NUM_TOPICS $ZERO_MEAN --savefile=$MODEL\
            $RWALK"
        echo $CMD; eval $CMD
        CMD="python $SRC/svd.py -k $NUM_TOPICS $ZERO_MEAN --savefile=$MODEL1\
            $RWALK1"
        echo $CMD; eval $CMD
        CMD="python $SRC/svd.py -k $NUM_TOPICS $ZERO_MEAN --savefile=$MODEL2\
            $RWALK2"
        echo $CMD; eval $CMD
    fi
echo
fi

# Use tourney map if given
if [[ "$TOURNEY_MAPPER" ]]; then
    echo "=== 6-8. Using provided topic map ==="
    MAP=$TOURNEY_MAPPER
else
    # Get idfs for category
    if [ $START_STAGE -le 6 -a $END_STAGE -ge 6 ]; then
        echo "=== 6. Calculate idfs for category ==="
        CMD="python $SRC/idfsByCategory.py $BRAND_ONLY --savefile=$IDFS\
            $PARENTCAT $CAT"
        echo $CMD; eval $CMD
    echo
    fi
    
    # Get tfidfs for each graph
    if [ $START_STAGE -le 7 -a $END_STAGE -ge 7 ]; then
        echo "=== 7. Calculate tfidfs for each graph ==="
        CMD="python $SRC/topicWords.py $BRAND_ONLY --database=$DB\
            --idfname=$IDFS --savefile=$TFIDF1 $MODEL1"
        echo $CMD; eval $CMD
        CMD="python $SRC/topicWords.py $BRAND_ONLY --database=$DB\
            --idfname=$IDFS --savefile=$TFIDF2 $MODEL2"
        echo $CMD; eval $CMD
    echo
    fi
    
    # Map tfidf topic spaces
    if [ $START_STAGE -le 8 -a $END_STAGE -ge 8 ]; then
        echo "=== 8. Construct topic map from graph1 to graph2 ==="
        CMD="python $SRC/mapTopics.py -v --max_connections $MAX_CONN\
            --savefile=$MAP $TFIDF1 $TFIDF2"
        echo $CMD; eval $CMD
    echo
    fi
fi

# Predict edges
if [ $START_STAGE -le 9 -a $END_STAGE -ge 9 ]; then
    echo "=== 9. Predict edges ==="
    if [ "$POPULARITY" = "true" ]; then
        echo "Building directed popularity graph"
        CMD="python $SRC/buildRecGraph.py $DIRECTED --savefile=$POP_GRAPH\
            --min-component-size=0 \
            --parent-category=$PARENTCAT --category=$CAT $DB"
        echo $CMD; eval $CMD
        POP="--popgraph=$POP_GRAPH"
    fi
    echo "Predicting randomly. . ."
    CMD="python $SRC/predictEdgesRandomly.py $SEED_OPT\
        --savefile=$PREDICTED_RAND $GRAPH1 $GRAPH2"
    echo $CMD; eval $CMD
    echo "Predicting using item-item tfidf. . ."
    CMD="python $SRC/predictEdgesTfidf.py $BRAND_ONLY\
        --savefile=$PREDICTED_TFIDF --database=$DB --idfname=$IDFS $POP $GRAPH1\
        $GRAPH2"
    echo $CMD; eval $CMD
    echo "Predicting using one model. . ."
    CMD="python $SRC/predictEdgesOneModel.py --savefile=$PREDICTED_ONE $POP\
        $MODEL $GRAPH1 $GRAPH2"
    echo $CMD; eval $CMD
    echo "Predicting with mapping between models. . ."
    CMD="python $SRC/predictEdges.py --savefile=$PREDICTED_EDGES $POP $MAP\
        $MODEL1 $MODEL2"
    echo $CMD; eval $CMD
echo
fi

# Construct source graphs
if [ $START_STAGE -le 10 -a $END_STAGE -ge 10 ]; then
    echo "=== 10. Construct source graphs ==="
    CMD="python $SRC/augmentGraph.py --savefile=$RAND_GRAPH\
        --edges=$PREDICTED_RAND $GRAPH1 $GRAPH2"
    echo $CMD; eval $CMD
    CMD="python $SRC/augmentGraph.py --savefile=$TFIDF_GRAPH\
        --edges=$PREDICTED_TFIDF $GRAPH1 $GRAPH2"
    echo $CMD; eval $CMD
    CMD="python $SRC/augmentGraph.py --savefile=$ONE_GRAPH\
        --edges=$PREDICTED_ONE $GRAPH1 $GRAPH2"
    echo $CMD; eval $CMD
    CMD="python $SRC/augmentGraph.py --savefile=$SOURCE_GRAPH\
        --edges=$PREDICTED_EDGES $GRAPH1 $GRAPH2"
    echo $CMD; eval $CMD
    echo
fi

# Construct source proximity matrices
if [ $START_STAGE -le 11 -a $END_STAGE -ge 11 ]; then
    echo "=== 11. Construct source proximity matrices ==="
    CMD="python $SRC/buildWalkMatrix.py $SEED_OPT --type=proximity\
        --maxdist=$EVAL_K --savefile=$RAND_PROX_MAT $RAND_GRAPH"
    echo $CMD; eval $CMD
    CMD="python $SRC/buildWalkMatrix.py $SEED_OPT --type=proximity\
        --maxdist=$EVAL_K --savefile=$TFIDF_PROX_MAT $TFIDF_GRAPH"
    echo $CMD; eval $CMD
    CMD="python $SRC/buildWalkMatrix.py $SEED_OPT --type=proximity\
        --maxdist=$EVAL_K --savefile=$ONE_PROX_MAT $ONE_GRAPH"
    echo $CMD; eval $CMD
    CMD="python $SRC/buildWalkMatrix.py $SEED_OPT --type=proximity\
        --maxdist=$EVAL_K --savefile=$SOURCE_PROX_MAT $SOURCE_GRAPH"
    echo $CMD; eval $CMD
    echo
fi

# Evaluate predictions
if [ $START_STAGE -le 12 -a $END_STAGE -ge 12 ]; then
    echo "=== 12. Evaluate predictions ==="
    echo
    echo "  RANDOM PREDICTIONS "
    CMD="python $SRC/evalPredictedEdges.py -k $EVAL_K $TARGET_PROX_MAT\
        $RAND_PROX_MAT $LOST_EDGES $PREDICTED_RAND"
    echo $CMD; eval $CMD
    echo
    echo "  TFIDF PREDICTIONS "
    CMD="python $SRC/evalPredictedEdges.py -k $EVAL_K $TARGET_PROX_MAT\
        $TFIDF_PROX_MAT $LOST_EDGES $PREDICTED_TFIDF"
    echo $CMD; eval $CMD
    echo
    echo "  ONE MODEL PREDICTIONS "
    CMD="python $SRC/evalPredictedEdges.py -k $EVAL_K $TARGET_PROX_MAT\
        $ONE_PROX_MAT $LOST_EDGES $PREDICTED_ONE"
    echo $CMD; eval $CMD
    echo
    echo "  MAPPING MODEL PREDICTIONS "
    CMD="python $SRC/evalPredictedEdges.py -k $EVAL_K $TARGET_PROX_MAT\
        $SOURCE_PROX_MAT $LOST_EDGES $PREDICTED_EDGES"
    echo $CMD; eval $CMD
    echo
fi
