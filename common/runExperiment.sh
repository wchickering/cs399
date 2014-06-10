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
            echo "--num-topics=NUM          Number of topics/concepts"
            echo "--edges-per-node=FLOAT    Edge predictions per node"
            echo "--directed                Run experiment on directed graphs"
            echo "--asymmetric              Don't include --symmetric for predictors"
            echo "--no-sphere               Don't include --sphere for predictors"
            echo "--normalize               Include --normalize for mapTopics"
            echo "--no-ortho                Don't include --ortho for mapTopics"
            echo "--short-coeff=FLOAT       Coeff for TF-IDF from short descriptions"
            echo "--bigrams-coeff=FLOAT     Coeff for TF-IDF from bigrams"
            echo "--hood-coeff=FLOAT        Coeff for TF-IDF from neighborhood"
            echo "--alpha=FLOAT             Popularity scaling factor."
            echo "--beta=FLOAT              Sigmoid parameter for mapTopics."
            echo "--tau=FLOAT               Coefficient for TF-IDF in KNN search"
            echo "--no-weight-in            Exclude popularity from KNN search"
            echo "--no-weight-out           Predict outgoing edges uniformaly"
            echo "--no-benchmarks           Don't run benchmark predictors"
            echo "--benchmark-random        Only do random benchmark"
            echo "--benchmark-popular       Only do popular benchmark"
            echo "--benchmark-tfidf-nopop   Only do TF-IDF NoPop benchmark"
            echo "--benchmark-tfidf         Only do TF-IDF benchmark"
            echo "--benchmark-randommap     Only do random-map benchmark"
            echo "--benchmark-onemodel      Only do OneModel benchmark"
            echo "--no-main                 Don't do main experiment"
            echo "--no-popularity-added     Don't add popularity back into graph"
            echo "--no-popularity-removed   Don't remove popularity in graph traversal"
            echo "--lda (BROKEN!)           Use lda instead of lsi for latent space"
            echo "--no-partition-by-brand   Do not partition graph by brand"
            echo "--no-zero-mean            Do not subtract mean before SVD"
            echo "--min-pop=FLOAT           Min popularity for KNN search"
            echo "--neighbor-limit=NUM      Limit for weighted KNN serch"
            echo "--min-component-size=NUM  Min component size allowed in graph"
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
        --num-topics*)
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
            export DIRECTED_OPT='--directed'
            shift
            ;;
        --asymmetric)
            export SYMMETRIC=0
            shift
            ;;
        --no-sphere)
            export SPHERE=0
            shift
            ;;
        --normalize)
            export NORMALIZE_OPT="--normalize"
            shift
            ;;
        --no-ortho)
            export ORTHO=0
            shift
            ;;
        --short-coeff*)
            export SHORT_COEFF=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_float $SHORT_COEFF
            shift
            ;;
        --bigrams-coeff*)
            export BIGRAMS_COEFF=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_float $BIGRAMS_COEFF
            shift
            ;;
        --hood-coeff*)
            export HOOD_COEFF=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_float $HOOD_COEFF
            shift
            ;;
        --alpha*)
            export ALPHA=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_float $ALPHA
            shift
            ;;
        --beta*)
            export BETA=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_float $BETA
            export BETA_OPT="--beta=$BETA"
            shift
            ;;
        --tau*)
            export TAU=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_float $TAU
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
            export BENCHMARK_RANDOM=0
            export BENCHMARK_POPULAR=0
            export BENCHMARK_TFIDF_NOPOP=0
            export BENCHMARK_TFIDF=0
            export BENCHMARK_RANDMAP=0
            export BENCHMARK_ONE=0
            shift
            ;;
        --benchmark-random)
            export BENCHMARK_RANDOM=1
            export BENCHMARK_POPULAR=0
            export BENCHMARK_TFIDF_NOPOP=0
            export BENCHMARK_TFIDF=0
            export BENCHMARK_RANDMAP=0
            export BENCHMARK_ONE=0
            shift
            ;;
        --benchmark-popular)
            export BENCHMARK_RANDOM=0
            export BENCHMARK_POPULAR=1
            export BENCHMARK_TFIDF_NOPOP=0
            export BENCHMARK_TFIDF=0
            export BENCHMARK_RANDMAP=0
            export BENCHMARK_ONE=0
            shift
            ;;
        --benchmark-tfidf-nopop)
            export BENCHMARK_RANDOM=0
            export BENCHMARK_POPULAR=0
            export BENCHMARK_TFIDF_NOPOP=1
            export BENCHMARK_TFIDF=0
            export BENCHMARK_RANDMAP=0
            export BENCHMARK_ONE=0
            shift
            ;;
        --benchmark-tfidf)
            export BENCHMARK_RANDOM=0
            export BENCHMARK_POPULAR=0
            export BENCHMARK_TFIDF_NOPOP=0
            export BENCHMARK_TFIDF=1
            export BENCHMARK_RANDMAP=0
            export BENCHMARK_ONE=0
            shift
            ;;
        --benchmark-randonmap)
            export BENCHMARK_RANDOM=0
            export BENCHMARK_POPULAR=0
            export BENCHMARK_TFIDF_NOPOP=0
            export BENCHMARK_TFIDF=0
            export BENCHMARK_RANDMAP=1
            export BENCHMARK_ONE=0
            shift
            ;;
        --benchmark-onemodel)
            export BENCHMARK_RANDOM=0
            export BENCHMARK_POPULAR=0
            export BENCHMARK_TFIDF_NOPOP=0
            export BENCHMARK_TFIDF=0
            export BENCHMARK_RANDMAP=0
            export BENCHMARK_ONE=1
            shift
            ;;
        --no-main)
            export MAIN_EXPERIMENT=0
            shift
            ;;
        --no-popularity-added)
            export POPULARITY_FLAG=0
            shift
            ;;
        --no-popularity-removed)
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
        --neighbor-limit*)
            export NEIGHBOR_LIMIT=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $NEIGHBOR_LIMIT
            export NEIGHBOR_LIMIT_OPT="--neighbor-limit=$NEIGHBOR_LIMIT"
            shift
            ;;
        --min-component-size*)
            export MIN_COMPONENT_SIZE=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $MIN_COMPONENT_SIZE
            shift
            ;;
        --eval-k*)
            export EVAL_K=`echo $1 | sed -e 's/^[^=]*=//g'`
            verify_number $EVAL_K
            shift
            ;;
        --seed*)
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
    NUM_TOPICS=16
fi

if [[ -z "$EDGES_PER_NODE" ]]; then
    EDGES_PER_NODE="1.8"
fi

if [[ -z "$SYMMETRIC" ]]; then
    SYMMETRIC_OPT="--symmetric"
fi

if [[ -z "$SPHERE" ]]; then
    SPHERE_OPT="--sphere"
fi

if [[ -z "$ORTHO" ]]; then
    ORTHO_OPT="--ortho"
fi

if [[ -z "$SHORT_COEFF" ]]; then
    SHORT_COEFF="0.0"
else
    SHORT_OPT="--short"
fi

if [[ -z "$BIGRAMS_COEFF" ]]; then
    BIGRAMS_COEFF="0.3"
fi

if [[ -z "$HOOD_COEFF" ]]; then
    HOOD_COEFF="0.0"
fi

if [[ -z "$ALPHA" ]]; then
    ALPHA="1.0"
fi

if [[ -z "$WEIGHT_IN" ]]; then
    WEIGHT_IN_OPT="--weight-in"
fi

if [[ -z "$WEIGHT_OUT" ]]; then
    WEIGHT_OUT_OPT="--weight-out"
fi

if [[ -z "$BENCHMARK_RANDOM" ]]; then
    BENCHMARK_RANDOM=1
fi

if [[ -z "$BENCHMARK_POPULAR" ]]; then
    BENCHMARK_POPULAR=1
fi

if [[ -z "$BENCHMARK_TFIDF_NOPOP" ]]; then
    BENCHMARK_TFIDF_NOPOP=1
fi

if [[ -z "$BENCHMARK_TFIDF" ]]; then
    BENCHMARK_TFIDF=1
fi

if [[ -z "$BENCHMARK_RANDMAP" ]]; then
    BENCHMARK_RANDMAP=1
fi

if [[ -z "$BENCHMARK_ONE" ]]; then
    BENCHMARK_ONE=1
fi

if [[ -z "$MAIN_EXPERIMENT" ]]; then
    MAIN_EXPERIMENT=1
fi

if [[ -z "$MODEL_TYPE" ]]; then
    MODEL_TYPE="lsi"
fi

if [[ -z "$PARTITION_BY_BRAND_FLAG" ]]; then
    PARTITION_BY_BRAND_OPT='--partition-by-brand'
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
SRC=../common
DB=$DATA/macys.db
STOPWORDS=$DATA/stopwords.txt
SEED_EXT=Seed${SEED}
CMDTERM='-----'

# escape/replace special characters in category
ESC_CAT=${PARENTCAT}_${CAT}
ESC_CAT=${ESC_CAT// /_}
ESC_CAT=${ESC_CAT//,/}
ESC_CAT=${ESC_CAT//&/AND}

EXPMT=${MODEL_TYPE}_${NUM_TOPICS}_${ESC_CAT}_$SEED_EXT

# graphs
GRAPH_BASE=$DATA/graph${ESC_CAT}
GRAPH=${GRAPH_BASE}.pickle
GRAPH1=${GRAPH_BASE}${SEED_EXT}_1.pickle
GRAPH2=${GRAPH_BASE}${SEED_EXT}_2.pickle
COMBINED_GRAPHS=${GRAPH_BASE}${SEED_EXT}_combined.pickle
RAND_GRAPH=${GRAPH_BASE}${SEED_EXT}_rand.pickle
POP_GRAPH=${GRAPH_BASE}${SEED_EXT}_popsrc.pickle
TFIDF_NOPOP_GRAPH=${GRAPH_BASE}${SEED_EXT}_tfidfNoPop.pickle
TFIDF_GRAPH=${GRAPH_BASE}${SEED_EXT}_tfidf.pickle
RANDMAP_GRAPH=${GRAPH_BASE}${SEED_EXT}_randmap.pickle
ONE_GRAPH=${GRAPH_BASE}${SEED_EXT}_one.pickle
SOURCE_GRAPH=${GRAPH_BASE}${SEED_EXT}_${NUM_TOPICS}_src.pickle

# random walks
RWALK_BASE=$DATA/randomWalk${ESC_CAT}
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

# TF-IDF and maps
TFIDF=$DATA/tfidf${ESC_CAT}.pickle
MAP=$DATA/topicMap_${EXPMT}.pickle
IDENT_MAP=$DATA/identMap_${NUM_TOPICS}.pickle
RAND_MAP=$DATA/randMap_${NUM_TOPICS}.pickle

# tau parameter used to incorporate TF-IDF directly into predictEdges.py
if [[ ! -z "$TAU" ]]; then
    TAU_OPT="--tfidfs=$TFIDF --short-coeff=$SHORT_COEFF\
             --bigrams-coeff=$BIGRAMS_COEFF --hood-coeff=$HOOD_COEFF\
             --tau=$TAU"
fi

POP_DICT=$DATA/popDict${ESC_CAT}${SEED_EXT}.pickle

# edges
LOST_EDGES=$DATA/lostEdges${ESC_CAT}${SEED_EXT}.pickle
PREDICTED_BASE=$DATA/predictedEdges_${EXPMT}
PREDICTED_RAND=${PREDICTED_BASE}_rand.pickle
PREDICTED_POP=${PREDICTED_BASE}_pop.pickle
PREDICTED_TFIDF_NOPOP=${PREDICTED_BASE}_tfidfNoPop.pickle
PREDICTED_TFIDF=${PREDICTED_BASE}_tfidf.pickle
PREDICTED_RANDMAP=${PREDICTED_BASE}_randmap.pickle
PREDICTED_ONE=${PREDICTED_BASE}_one.pickle
PREDICTED_EDGES=${PREDICTED_BASE}.pickle

# proximity matrices
PROX_MAT_BASE=$DATA/proxMat${ESC_CAT}K${EVAL_K}${SEED_EXT}
TARGET_PROX_MAT=${PROX_MAT_BASE}_tgt.npz
RAND_PROX_MAT=${PROX_MAT_BASE}_rand.npz
POP_PROX_MAT=${PROX_MAT_BASE}_pop.npz
TFIDF_NOPOP_PROX_MAT=${PROX_MAT_BASE}_tfidfNoPop.npz
TFIDF_PROX_MAT=${PROX_MAT_BASE}_tfidf.npz
RANDMAP_PROX_MAT=${PROX_MAT_BASE}_randmap.npz
ONE_PROX_MAT=${PROX_MAT_BASE}_one.npz
SOURCE_PROX_MAT=${PROX_MAT_BASE}_${NUM_TOPICS}_src.npz

RESULTS=$DATA/results_${EXPMT}_K${EVAL_K}.txt
APPENDFILE=$DATA/experimentResults.csv

echo

# Construct recommendation graph from DB
if [ $START_STAGE -le 1 -a $END_STAGE -ge 1 ]; then
    echo "=== 1. Build directed recommender graph for category from DB ==="
    CMD="python $SRC/buildRecGraph.py --savefile=$GRAPH $DIRECTED_OPT\
        --min-component-size=$MIN_COMPONENT_SIZE\
        --parent-category='$PARENTCAT' --category='$CAT' $DB"
    echo $CMD; eval $CMD; echo $CMDTERM
    echo
fi

# Partition graph
if [ $START_STAGE -le 2 -a $END_STAGE -ge 2 ]; then
    echo "=== 2. Partition category graph ==="
    CMD="python $SRC/partitionGraph.py --graph1=$GRAPH1 --graph2=$GRAPH2\
        --lost_edges=$LOST_EDGES $SEED_OPT $PARTITION_BY_BRAND_OPT\
        --min-component-size=$MIN_COMPONENT_SIZE $DB $GRAPH"
    echo $CMD; eval $CMD; echo $CMDTERM
    CMD="python $SRC/augmentGraph.py --savefile=$COMBINED_GRAPHS $GRAPH1\
        $GRAPH2"
    echo $CMD; eval $CMD; echo $CMDTERM
    echo
fi

# Construct TF-IDF vectors for category items
if [ $START_STAGE -le 3 -a $END_STAGE -ge 3 ]; then
    echo "=== 3. Construct TF-IDF vectors for category items ==="
    CMD="python $SRC/buildTFIDF.py --savefile=$TFIDF --stopwords=$STOPWORDS\
        --graph=$COMBINED_GRAPHS $SHORT_OPT --bigrams $DB '$PARENTCAT' '$CAT'"
    echo $CMD; eval $CMD; echo $CMDTERM
    echo
fi

# Random walk
if [ $START_STAGE -le 4 -a $END_STAGE -ge 4 ]; then
    HOME="0.05"
    STEPS="30"
    echo "=== 4. Randomly walk each graph ==="
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
if [ $START_STAGE -le 5 -a $END_STAGE -ge 5 ]; then
    echo "=== 5. Train $MODEL_TYPE model for each graph ==="
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

if [[ "$TOURNEY_MAPPER" ]]; then
    # Use tourney map if given
    echo "=== 6. Using provided topic map ==="
    MAP=$TOURNEY_MAPPER
else
    # Map topic spaces using TF-IDF vectors
    if [ $START_STAGE -le 6 -a $END_STAGE -ge 6 ]; then
        echo "=== 6. Map topic spaces ==="
        CMD="python $SRC/mapTopics.py --savefile=$RAND_MAP --random\
            $SEED_OPT $NORMALIZE_OPT $ORTHO_OPT $TFIDF $MODEL1 $MODEL2"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/mapTopics.py --savefile=$IDENT_MAP --identity\
            $NORMALIZE_OPT $ORTHO_OPT $TFIDF $MODEL1 $MODEL2"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/mapTopics.py --savefile=$MAP\
            --short-coeff=$SHORT_COEFF --bigrams-coeff=$BIGRAMS_COEFF\
            --hood-coeff=$HOOD_COEFF $NORMALIZE_OPT $ORTHO_OPT\
            $BETA_OPT $TFIDF $MODEL1 $MODEL2"
        echo $CMD; eval $CMD; echo $CMDTERM
        echo
    fi
fi

if [[ -z "$POPULARITY_FLAG" ]]; then
    if [ $START_STAGE -le 7 -a $END_STAGE -ge 7 ]; then
        # Construct popularity dictionary
        echo "=== 7. Construct popularity dictionary ==="
        CMD="python $SRC/buildPopDictionary.py --savefile=$POP_DICT\
            --alpha=$ALPHA $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
        echo
    fi
    POP_DICT_OPT="--popdict=$POP_DICT"
fi

# Predict edges
if [ $START_STAGE -le 8 -a $END_STAGE -ge 8 ]; then
    echo "=== 8. Predict edges ==="
    if [ $BENCHMARK_RANDOM -eq 1 ]; then
        echo "** Predicting randomly. . ."
        CMD="python $SRC/predictEdgesRandomly.py --savefile=$PREDICTED_RAND\
            $SEED_OPT --edges-per-node=$EDGES_PER_NODE $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_POPULAR -eq 1 ]; then
        echo "** Predicting based on popularity. . ."
        CMD="python $SRC/predictEdgesPopular.py --savefile=$PREDICTED_POP\
            $SEED_OPT -v --topn=3 --edges-per-node=$EDGES_PER_NODE\
            $WEIGHT_OUT_OPT $SYMMETRIC_OPT $POP_DICT $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_TFIDF_NOPOP -eq 1 ]; then
        echo "** Predicting using item-item TF-IDF without popularity. . ."
        CMD="python $SRC/predictEdgesTfidf.py --savefile=$PREDICTED_TFIDF_NOPOP\
            --edges-per-node=$EDGES_PER_NODE $SYMMETRIC_OPT\
            --short-coeff=$SHORT_COEFF --bigrams-coeff=$BIGRAMS_COEFF\
            --hood-coeff=$HOOD_COEFF $TFIDF $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_TFIDF -eq 1 ]; then
        echo "** Predicting using item-item TF-IDF. . ."
        CMD="python $SRC/predictEdgesTfidf.py --savefile=$PREDICTED_TFIDF\
            --edges-per-node=$EDGES_PER_NODE $POP_DICT_OPT --min-pop=$MIN_POP\
            $WEIGHT_IN_OPT $WEIGHT_OUT_OPT $SYMMETRIC_OPT\
            --short-coeff=$SHORT_COEFF --bigrams-coeff=$BIGRAMS_COEFF\
            --hood-coeff=$HOOD_COEFF $TFIDF $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_RANDMAP -eq 1 ]; then
        echo "** Predicting using random map. . ."
        CMD="python $SRC/predictEdges.py --savefile=$PREDICTED_RANDMAP\
            --edges-per-node=$EDGES_PER_NODE $POP_DICT_OPT --min-pop=$MIN_POP\
            $NEIGHBOR_LIMIT_OPT $WEIGHT_IN_OPT $WEIGHT_OUT_OPT $SYMMETRIC_OPT\
            $SPHERE_OPT $RAND_MAP $MODEL1 $MODEL2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_ONE -eq 1 ]; then
        echo "** Predicting using one model. . ."
        CMD="python $SRC/partitionModel.py --model1=$MODEL_ONE1\
            --model2=$MODEL_ONE2 $MODEL $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
        CMD="python $SRC/predictEdges.py --savefile=$PREDICTED_ONE\
            --edges-per-node=$EDGES_PER_NODE $POP_DICT_OPT --min-pop=$MIN_POP\
            $NEIGHBOR_LIMIT_OPT $WEIGHT_IN_OPT $WEIGHT_OUT_OPT $SYMMETRIC_OPT\
            $SPHERE_OPT $IDENT_MAP $MODEL_ONE1 $MODEL_ONE2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $MAIN_EXPERIMENT -eq 1 ]; then
        echo "** Predicting with mapping between models. . ."
        CMD="python $SRC/predictEdges.py --savefile=$PREDICTED_EDGES\
            --edges-per-node=$EDGES_PER_NODE $POP_DICT_OPT --min-pop=$MIN_POP\
            $NEIGHBOR_LIMIT_OPT $WEIGHT_IN_OPT $WEIGHT_OUT_OPT $TAU_OPT\
            $SYMMETRIC_OPT $SPHERE_OPT $MAP $MODEL1 $MODEL2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    echo
fi

# Construct source graphs
if [ $START_STAGE -le 9 -a $END_STAGE -ge 9 ]; then
    echo "=== 9. Construct source graphs ==="
    if [ $BENCHMARK_RANDOM -eq 1 ]; then
        CMD="python $SRC/augmentGraph.py --savefile=$RAND_GRAPH\
            --edges=$PREDICTED_RAND $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_POPULAR -eq 1 ]; then
        CMD="python $SRC/augmentGraph.py --savefile=$POP_GRAPH\
            --edges=$PREDICTED_POP $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_TFIDF_NOPOP -eq 1 ]; then
        CMD="python $SRC/augmentGraph.py --savefile=$TFIDF_NOPOP_GRAPH\
            --edges=$PREDICTED_TFIDF_NOPOP $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_TFIDF -eq 1 ]; then
        CMD="python $SRC/augmentGraph.py --savefile=$TFIDF_GRAPH\
            --edges=$PREDICTED_TFIDF $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_RANDMAP -eq 1 ]; then
        CMD="python $SRC/augmentGraph.py --savefile=$RANDMAP_GRAPH\
            --edges=$PREDICTED_RANDMAP $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_ONE -eq 1 ]; then
        CMD="python $SRC/augmentGraph.py --savefile=$ONE_GRAPH\
            --edges=$PREDICTED_ONE $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $MAIN_EXPERIMENT -eq 1 ]; then
        CMD="python $SRC/augmentGraph.py --savefile=$SOURCE_GRAPH\
            --edges=$PREDICTED_EDGES $GRAPH1 $GRAPH2"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    echo
fi

# Construct proximity matrices
if [ $START_STAGE -le 10 -a $END_STAGE -ge 10 ]; then
    echo "=== 10. Construct proximity matrices ==="
    CMD="python $SRC/buildWalkMatrix.py --savefile=$TARGET_PROX_MAT\
        $SEED_OPT --type=proximity --maxdist=$EVAL_K $GRAPH"
    echo $CMD; eval $CMD; echo $CMDTERM
    if [ $BENCHMARK_RANDOM -eq 1 ]; then
        CMD="python $SRC/buildWalkMatrix.py --savefile=$RAND_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $RAND_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_POPULAR -eq 1 ]; then
        CMD="python $SRC/buildWalkMatrix.py --savefile=$POP_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $POP_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_TFIDF_NOPOP -eq 1 ]; then
        CMD="python $SRC/buildWalkMatrix.py --savefile=$TFIDF_NOPOP_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $TFIDF_NOPOP_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_TFIDF -eq 1 ]; then
        CMD="python $SRC/buildWalkMatrix.py --savefile=$TFIDF_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $TFIDF_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_RANDMAP -eq 1 ]; then
        CMD="python $SRC/buildWalkMatrix.py --savefile=$RANDMAP_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $RANDMAP_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $BENCHMARK_ONE -eq 1 ]; then
        CMD="python $SRC/buildWalkMatrix.py --savefile=$ONE_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $ONE_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    if [ $MAIN_EXPERIMENT -eq 1 ]; then
        CMD="python $SRC/buildWalkMatrix.py --savefile=$SOURCE_PROX_MAT\
            $SEED_OPT --type=proximity --maxdist=$EVAL_K $SOURCE_GRAPH"
        echo $CMD; eval $CMD; echo $CMDTERM
    fi
    echo
fi

# Evaluate predictions
if [ $START_STAGE -le 11 -a $END_STAGE -ge 11 ]; then
    echo "=== 11. Evaluate predictions ===" | tee $RESULTS
    if [ $BENCHMARK_RANDOM -eq 1 ]; then
        echo | tee -a $RESULTS
        EXPNAME="RANDOM"
        echo "  $EXPNAME PREDICTIONS" | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py --append-file=$APPENDFILE\
            --data='$EXPNAME,$ESC_CAT' -k $EVAL_K $TARGET_PROX_MAT\
            $RAND_PROX_MAT $LOST_EDGES $PREDICTED_RAND"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
    fi
    if [ $BENCHMARK_POPULAR -eq 1 ]; then
        echo | tee -a $RESULTS
        EXPNAME="POPULAR"
        echo "  $EXPNAME PREDICTIONS" | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py --append-file=$APPENDFILE\
            --data='$EXPNAME,$ESC_CAT' -k $EVAL_K $TARGET_PROX_MAT\
            $POP_PROX_MAT $LOST_EDGES $PREDICTED_POP"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
    fi
    if [ $BENCHMARK_TFIDF_NOPOP -eq 1 ]; then
        echo | tee -a $RESULTS
        EXPNAME="TF-IDF NOPOP"
        echo "  $EXPNAME PREDICTIONS" | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py --append-file=$APPENDFILE\
            --data='$EXPNAME,$ESC_CAT' -k $EVAL_K $TARGET_PROX_MAT\
            $TFIDF_NOPOP_PROX_MAT $LOST_EDGES $PREDICTED_TFIDF_NOPOP"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
    fi
    if [ $BENCHMARK_TFIDF -eq 1 ]; then
        echo | tee -a $RESULTS
        EXPNAME="TF-IDF"
        echo "  $EXPNAME PREDICTIONS" | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py --append-file=$APPENDFILE\
            --data='$EXPNAME,$ESC_CAT' -k $EVAL_K $TARGET_PROX_MAT\
            $TFIDF_PROX_MAT $LOST_EDGES $PREDICTED_TFIDF"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
    fi
    if [ $BENCHMARK_RANDMAP -eq 1 ]; then
        echo | tee -a $RESULTS
        EXPNAME="RANDOM MAP"
        echo "  $EXPNAME PREDICTIONS" | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py --append-file=$APPENDFILE\
           --data='$EXPNAME,$ESC_CAT' -k $EVAL_K $TARGET_PROX_MAT\
           $RANDMAP_PROX_MAT $LOST_EDGES $PREDICTED_RANDMAP"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
    fi
    if [ $BENCHMARK_ONE -eq 1 ]; then
        echo $CMDTERM | tee -a $RESULTS
        EXPNAME="ONE MODEL"
        echo "  $EXPNAME PREDICTIONS" | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py --append-file=$APPENDFILE\
            --data='$EXPNAME,$ESC_CAT' -k $EVAL_K $TARGET_PROX_MAT\
            $ONE_PROX_MAT $LOST_EDGES $PREDICTED_ONE"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
    fi
    if [ $MAIN_EXPERIMENT -eq 1 ]; then
        echo | tee -a $RESULTS
        EXPNAME="MAPPING MODEL"
        echo "  $EXPNAME PREDICTIONS" | tee -a $RESULTS
        CMD="python $SRC/evalPredictedEdges.py --append-file=$APPENDFILE\
             --data='$EXPNAME,$ESC_CAT' -k $EVAL_K $TARGET_PROX_MAT\
             $SOURCE_PROX_MAT $LOST_EDGES $PREDICTED_EDGES"
        echo $CMD | tee -a $RESULTS; eval $CMD | tee -a $RESULTS
        echo $CMDTERM | tee -a $RESULTS
    fi
    echo
fi
