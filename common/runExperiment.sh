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

verify_float () {
    re='^[0-9]*\.?[0-9]+$'
    if ! [[ $1 =~ $re ]] ; then
        die "error: Not a float: $1"
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
            echo "--data=DIR                Specify the data directory to use"
            echo "--numtopics=NUM           Number of topics/concepts"
            echo "--edges-per-node          Edge prediction per node"
            echo "--directed                Run experiment on directed graphs"
            echo "--asymmetric              Don't include --symmetric on predictors"
            echo "--no-weight-in            Exclude popularity from KNN search"
            echo "--no-weight-out           Predict outgoing edges uniformaly"
            echo "--no-benchmarks           Don't run benchmark predictors"
            echo "--no-popularity-added     Don't add popularity back into graph"
            echo "--no-popularity-removed   Don't remove popularity in graph"
            echo "                          traversal"
            echo "--lda                     Use lda instead of lsi for latent"
            echo "                          space"
            echo "--no-partition-by-brand   Do not partition graph by brand"
            echo "--brand-only              Only consider brand for TFIDF"
            echo "--no-zero-mean            Do not subtract mean before SVD"
            echo "--min-pop=FLOAT           Specifiy minimum popularity in search"
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
        --data*)
            export DATA=`echo $1 | sed -e 's/^[^=]*=//g'`
            shift
            ;;
        --numtopics*)
            export NUM_TOPICS=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $NUM_TOPICS
            shift
            ;;
        --edges-per-node*)
            export EDGES_PER_NODE=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_float $EDGES_PER_NODE
            shift
            ;;
        --directed)
            # this should be left undefined by default
            export DIRECTED_OPT='--directed'
            shift
            ;;
        --asymmetric)
            export SYMMETRIC=0
            shift
            ;;
        --no-weight-in)
            export WEIGHT_IN=0
            shift
            ;;
        --no-weight-out)
            export WEIGHT_OUT=0
            shift
            ;;
        --no-benchmarks)
            export BENCHMARKS=0
            shift
            ;;
        --no-popularity-added)
            # this should be left undefined by default
            export POPULARITY_FLAG=0
            shift
            ;;
        --no-popularity-removed)
            # this should be left undefined by default
            export REMOVE_POP_FLAG=0
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
            export BRAND_ONLY_OPT="--brand-only"
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
        --min-pop*)
            export MIN_POP=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_float $MIN_POP
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
            export MAX_CONN_OPT="--max_connections=$MAX_CONN"
            shift
            ;;
        --eval-k*)
            export EVAL_K=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $EVAL_K
            shift
            ;;
        --seed*)
            # this should be left undefined by default
            export SEED=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $SEED
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

if [[ -z "$DATA" ]]; then
    DATA=data
fi

if [[ -z "$NUM_TOPICS" ]]; then
    NUM_TOPICS=32
fi

if [[ -z "$EDGES_PER_NODE" ]]; then
    EDGES_PER_NODE="1.8"
fi
if [[ -z "$SYMMETRIC" ]]; then
    SYMMETRIC_OPT="--symmetric"
fi

if [[ -z "$WEIGHT_IN" ]]; then
    WEIGHT_IN_OPT="--weight-in"
fi

if [[ -z "$WEIGHT_OUT" ]]; then
    WEIGHT_OUT_OPT="--weight-out"
fi

if [[ -z "$BENCHMARKS" ]]; then
    BENCHMARKS=1
fi

if [[ -z "$MODEL_TYPE" ]]; then
    MODEL_TYPE="lsi"
fi

if [[ -z "$PARTITION_BY_BRAND_FLAG" ]]; then
    PARTITION_BY_BRAND='--partition-by-brand'
fi

if [[ -z "$ZERO_MEAN_FLAG" ]]; then
    ZERO_MEAN_OPT='--zero-mean'
fi

if [[ -z "$REMOVE_POP_FLAG" ]]; then
    REMOVE_POP_OPT='--tran2'
fi

if [[ -z "$MIN_POP" ]]; then
    MIN_POP="0.0"
fi

if [[ -z "$MIN_COMPONENT_SIZE" ]]; then
    MIN_COMPONENT_SIZE=40
fi

if [[ -z "$EVAL_K" ]]; then
    EVAL_K=2
fi

if [[ -z "$SEED" ]]; then
    SEED=0
fi
SEED_OPT="--seed=$SEED"


######
# Setup environment
##############
CMDTERM='-----'
SRC=../common
SEED_EXT=Seed${SEED}
EXPMT=${MODEL_TYPE}_${NUM_TOPICS}_${CAT}_$SEED_EXT
DB=$DATA/macys.db
STOPWORDS=$DATA/stopwords.txt

# graphs
GRAPH_BASE=$DATA/graph${CAT}
GRAPH=${GRAPH_BASE}.pickle
GRAPH1=${GRAPH_BASE}${SEED_EXT}_1.pickle
GRAPH2=${GRAPH_BASE}${SEED_EXT}_2.pickle
RAND_GRAPH=${GRAPH_BASE}${SEED_EXT}_rand.pickle
POP_GRAPH=${GRAPH_BASE}${SEED_EXT}_popsrc.pickle
TFIDF_GRAPH=${GRAPH_BASE}${SEED_EXT}_tfidf.pickle
ONE_GRAPH=${GRAPH_BASE}${SEED_EXT}_one.pickle
SOURCE_GRAPH=${GRAPH_BASE}${SEED_EXT}_${NUM_TOPICS}_src.pickle

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
LDA1=${LDA_BASE}_one_1.pickle
LDA2=${LDA_BASE}_one_2.pickle

# lsi models
LSI_BASE=$DATA/$EXPMT
LSI=${LSI_BASE}.npz
LSI1=${LSI_BASE}_1.npz
LSI2=${LSI_BASE}_2.npz
LSI_ONE1=${LSI_BASE}_one_1.npz
LSI_ONE2=${LSI_BASE}_one_2.npz

if [ "$MODEL_TYPE" = "lda" ]; then
    MODEL=$LDA
    MODEL1=$LDA1
    MODEL2=$LDA2
    MODEL_ONE1=$LDA_ONE1
    MODEL_ONE2=$LDA_ONE2
else
    MODEL=$LSI
    MODEL1=$LSI1
    MODEL2=$LSI2
    MODEL_ONE1=$LSI_ONE1
    MODEL_ONE2=$LSI_ONE2
fi

# tfidf and map
IDFS=$DATA/idfs${CAT}.pickle
TFIDF_BASE=$DATA/tfidf_${EXPMT}
TFIDF=${TFIDF_BASE}.pickle
TFIDF1=${TFIDF_BASE}_1.pickle
TFIDF2=${TFIDF_BASE}_2.pickle
MAP=$DATA/topicMap_${EXPMT}.pickle
IDENT_MAP=$DATA/identMap_${NUM_TOPICS}.pickle

POP_DICT=$DATA/popDict${CAT}${SEED_EXT}.pickle

# edges
LOST_EDGES=$DATA/lostEdges${CAT}${SEED_EXT}.pickle
PREDICTED_BASE=$DATA/predictedEdges_${EXPMT}
PREDICTED_RAND=${PREDICTED_BASE}_rand.pickle
PREDICTED_POP=${PREDICTED_BASE}_pop.pickle
PREDICTED_TFIDF=${PREDICTED_BASE}_tfidf.pickle
PREDICTED_ONE=${PREDICTED_BASE}_one.pickle
PREDICTED_EDGES=${PREDICTED_BASE}.pickle

# proximity matrices
PROX_MAT_BASE=$DATA/proxMat${CAT}K${EVAL_K}${SEED_EXT}
TARGET_PROX_MAT=${PROX_MAT_BASE}_tgt.npz
RAND_PROX_MAT=${PROX_MAT_BASE}_rand.npz
POP_PROX_MAT=${PROX_MAT_BASE}_pop.npz
TFIDF_PROX_MAT=${PROX_MAT_BASE}_tfidf.npz
ONE_PROX_MAT=${PROX_MAT_BASE}_one.npz
SOURCE_PROX_MAT=${PROX_MAT_BASE}_${NUM_TOPICS}_src.npz

RESULTS=$DATA/results_${EXPMT}_K${EVAL_K}.txt

# Construct recommendation graph from DB
if [ $START_STAGE -le 1 -a $END_STAGE -ge 1 ]; then
    echo "=== 1. Build directed recommender graph for category from DB ==="
    CMD="python $SRC/buildRecGraph.py --savefile=$GRAPH $DIRECTED_OPT\
        --min-component-size=$MIN_COMPONENT_SIZE --parent-category=$PARENTCAT\
        --category=$CAT $DB"
    echo $CMD; eval $CMD; echo $CMDTERM
echo
fi

# Partition graph
if [ $START_STAGE -le 2 -a $END_STAGE -ge 2 ]; then
    echo "=== 2. Partition category graph ==="
    CMD="python $SRC/partitionGraph.py --graph1=$GRAPH1 --graph2=$GRAPH2\
        --lost_edges=$LOST_EDGES $SEED_OPT $PARTITION_BY_BRAND\
        --min-component-size=$MIN_COMPONENT_SIZE $GRAPH"
    echo $CMD; eval $CMD; echo $CMDTERM
echo
fi

# Random walk
if [ $START_STAGE -le 3 -a $END_STAGE -ge 3 ]; then
    HOME="0.1"
    STEPS="30"
    echo "=== 3. Randomly walk each graph ==="
    CMD="python $SRC/buildWalkMatrix.py --savefile=$RWALK --home=$HOME\
        --steps=$STEPS $REMOVE_POP_OPT $GRAPH"
    echo $CMD; eval $CMD; echo $CMDTERM
    CMD="python $SRC/buildWalkMatrix.py --savefile=$RWALK1 --home=$HOME\
        --steps=$STEPS $REMOVE_POP_OPT $GRAPH1"
    echo $CMD; eval $CMD; echo $CMDTERM
    CMD="python $SRC/buildWalkMatrix.py --savefile=$RWALK2 --home=$HOME\
        --steps=$STEPS $REMOVE_POP_OPT $GRAPH2"
    echo $CMD; eval $CMD; echo $CMDTERM
echo
fi

# Train model on each graph
if [ $START_STAGE -le 4 -a $END_STAGE -ge 4 ]; then
    echo "=== 4. Train $MODEL_TYPE model for each graph ==="
    if [ "$MODEL_TYPE" = "lda" ]; then
        CMD="python $SRC/buildLDAModel.py --lda-file=$MODEL"\
            --num-topics=$NUM_TOPICS --matrixfile=$RWALK
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/buildLDAModel.py --lda-file=$MODEL1"\
            --num-topics=$NUM_TOPICS --matrixfile=$RWALK1
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/buildLDAModel.py --lda-file=$MODEL2"\
            --num-topics=$NUM_TOPICS --matrixfile=$RWALK2
        echo $CMD; eval $CMD; echo $CMDTERM
    else
        CMD="python $SRC/svd.py --savefile=$MODEL -k $NUM_TOPICS\
            $ZERO_MEAN_OPT $RWALK"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/svd.py --savefile=$MODEL1 -k $NUM_TOPICS\
            $ZERO_MEAN_OPT $RWALK1"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/svd.py --savefile=$MODEL2 -k $NUM_TOPICS\
            $ZERO_MEAN_OPT $RWALK2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
echo
fi

# Use tourney map if given
if [[ "$TOURNEY_MAPPER" ]]; then
    echo "=== 5-7. Using provided topic map ==="
    MAP=$TOURNEY_MAPPER
else
    # Get idfs for category
    if [ $START_STAGE -le 5 -a $END_STAGE -ge 5 ]; then
        echo "=== 5. Calculate idfs for category ==="
        CMD="python $SRC/idfsByCategory.py --savefile=$IDFS $BRAND_ONLY_OPT\
            $PARENTCAT $CAT"
        echo $CMD; eval $CMD; echo $CMDTERM
    echo
    fi
    
    # Get tfidfs for each graph
    if [ $START_STAGE -le 6 -a $END_STAGE -ge 6 ]; then
        echo "=== 6. Calculate tfidfs for each graph ==="
        CMD="python $SRC/buildTFIDF.py --savefile=$TFIDF1 $BRAND_ONLY_OPT\
            --stopwords=$STOPWORDS --idfname=$IDFS $DB $MODEL1"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/buildTFIDF.py --savefile=$TFIDF2 $BRAND_ONLY_OPT\
            --stopwords=$STOPWORDS --idfname=$IDFS $DB $MODEL2"
        echo $CMD; eval $CMD; echo $CMDTERM
    echo
    fi
    
    # Map tfidf topic spaces
    if [ $START_STAGE -le 7 -a $END_STAGE -ge 7 ]; then
        echo "=== 7. Construct topic map from graph1 to graph2 ==="
        CMD="python $SRC/mapTopics.py --savefile=$MAP $MAX_CONN_OPT\
            $TFIDF1 $TFIDF2"
        echo $CMD; eval $CMD; echo $CMDTERM
    echo
    fi
fi

if [[ -z "$POPULARITY_FLAG" ]]; then
    if [ $START_STAGE -le 8 -a $END_STAGE -ge 8 ]; then
        # Construct popularity dictionary
        echo "=== 8. Popularity Dictionary ==="
        CMD="python $SRC/buildPopDictionary.py --savefile=$POP_DICT --alpha=1.0\
            $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    echo
    fi
    POP_DICT_OPT="--popdict=$POP_DICT"
fi

# Predict edges
if [ $START_STAGE -le 9 -a $END_STAGE -ge 9 ]; then
    echo "=== 9. Predict edges ==="
    if [ $BENCHMARKS -eq 1 ]; then
        echo "** Predicting randomly. . ."
        CMD="python $SRC/predictEdgesRandomly.py --savefile=$PREDICTED_RAND\
            $SEED_OPT $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
        echo "** Predicting based on popularity. . ."
        CMD="python $SRC/predictEdgesPopular.py --savefile=$PREDICTED_POP\
            $SEED_OPT -v --topn=3 -k $EDGES_PER_NODE $WEIGHT_OUT_OPT\
            $SYMMETRIC_OPT $POP_DICT $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
        echo "** Predicting using item-item tfidf. . ."
        CMD="python $SRC/predictEdgesTfidf.py --savefile=$PREDICTED_TFIDF\
            -k $EDGES_PER_NODE $BRAND_ONLY_OPT --idfname=$IDFS $POP_DICT_OPT\
            --stopwords=$STOPWORDS --min-pop=$MIN_POP $WEIGHT_IN_OPT\
            $WEIGHT_OUT_OPT $SYMMETRIC_OPT $DB $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
        echo "** Predicting using one model. . ."
        CMD="python $SRC/partitionModel.py --model1=$MODEL_ONE1\
            --model2=$MODEL_ONE2 --ident-map=$IDENT_MAP\
            $MODEL $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/predictEdges.py --savefile=$PREDICTED_ONE\
            -k $EDGES_PER_NODE $POP_DICT_OPT --min-pop=$MIN_POP $WEIGHT_IN_OPT\
            $WEIGHT_OUT_OPT $SYMMETRIC_OPT --sphere\
            $IDENT_MAP $MODEL_ONE1 $MODEL_ONE2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    echo "** Predicting with mapping between models. . ."
    CMD="python $SRC/predictEdges.py --savefile=$PREDICTED_EDGES\
        -k $EDGES_PER_NODE $POP_DICT_OPT --min-pop=$MIN_POP $WEIGHT_IN_OPT\
        $WEIGHT_OUT_OPT $SYMMETRIC_OPT --sphere $MAP $MODEL1 $MODEL2"
    echo $CMD; eval $CMD; echo $CMDTERM
echo
fi

# Construct source graphs
if [ $START_STAGE -le 10 -a $END_STAGE -ge 10 ]; then
    echo "=== 10. Construct source graphs ==="
    if [ $BENCHMARKS -eq 1 ]; then
        CMD="python $SRC/augmentGraph.py --savefile=$RAND_GRAPH\
            --edges=$PREDICTED_RAND $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/augmentGraph.py --savefile=$POP_GRAPH\
            --edges=$PREDICTED_POP $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/augmentGraph.py --savefile=$TFIDF_GRAPH\
            --edges=$PREDICTED_TFIDF $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/augmentGraph.py --savefile=$ONE_GRAPH\
            --edges=$PREDICTED_ONE $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    CMD="python $SRC/augmentGraph.py --savefile=$SOURCE_GRAPH\
        --edges=$PREDICTED_EDGES $GRAPH1 $GRAPH2"
    echo $CMD; eval $CMD; echo $CMDTERM
    echo
fi

# Construct proximity matrices
if [ $START_STAGE -le 11 -a $END_STAGE -ge 11 ]; then
    echo "=== 11. Construct proximity matrices ==="
    CMD="python $SRC/buildWalkMatrix.py --savefile=$TARGET_PROX_MAT\
        $SEED_OPT --type=proximity --maxdist=$EVAL_K $GRAPH"
    echo $CMD; eval $CMD; echo $CMDTERM
    if [ $BENCHMARKS -eq 1 ]; then
        CMD="python $SRC/buildWalkMatrix.py --savefile=$RAND_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $RAND_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/buildWalkMatrix.py --savefile=$POP_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $POP_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/buildWalkMatrix.py --savefile=$TFIDF_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $TFIDF_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/buildWalkMatrix.py --savefile=$ONE_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $ONE_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    CMD="python $SRC/buildWalkMatrix.py --savefile=$SOURCE_PROX_MAT\
        $SEED_OPT --type=proximity --maxdist=$EVAL_K $SOURCE_GRAPH"
    echo $CMD; eval $CMD; echo $CMDTERM
    echo
fi

# Evaluate predictions
if [ $START_STAGE -le 12 -a $END_STAGE -ge 12 ]; then
    echo "=== 12. Evaluate predictions ===" | tee $RESULTS
    if [ $BENCHMARKS -eq 1 ]; then
        echo | tee -a $RESULTS
        echo "  RANDOM PREDICTIONS " | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py -k $EVAL_K $TARGET_PROX_MAT\
            $RAND_PROX_MAT $LOST_EDGES $PREDICTED_RAND"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
        echo | tee -a $RESULTS
        echo "  POPULAR PREDICTIONS " | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py -k $EVAL_K $TARGET_PROX_MAT\
            $POP_PROX_MAT $LOST_EDGES $PREDICTED_POP"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
        echo | tee -a $RESULTS
        echo "  TFIDF PREDICTIONS " | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py -k $EVAL_K $TARGET_PROX_MAT\
            $TFIDF_PROX_MAT $LOST_EDGES $PREDICTED_TFIDF"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
        echo | tee -a $RESULTS
        echo "  ONE MODEL PREDICTIONS " | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py -k $EVAL_K $TARGET_PROX_MAT\
            $ONE_PROX_MAT $LOST_EDGES $PREDICTED_ONE"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
    fi
    echo | tee -a $RESULTS
    echo "  MAPPING MODEL PREDICTIONS " | tee -a $RESULTS
    CMD="python $SRC/evalPredictedEdges.py -k $EVAL_K $TARGET_PROX_MAT\
        $SOURCE_PROX_MAT $LOST_EDGES $PREDICTED_EDGES"
    echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
    echo $CMDTERM | tee -a $RESULTS
    echo
fi
