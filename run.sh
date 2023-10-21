#!/bin/bash

export WORK_DIR=/data3/yufenggu/aiqos/inference_results_v1.1/closed/Intel/code
export DLRM_DIR=$WORK_DIR/dlrm-99.9/pytorch-cpu/python/model
export DATASETS_DIR=$WORK_DIR/../../../../datasets
export MODELS_DIR=$WORK_DIR/../../../../models
export CONDA_ENVS_DIR=/data3/yufenggu/anaconda3/envs
export TEMP_OUTDIR=/data3/ydil/aiqos/inference_results_v1.1/closed/Intel/code

percentage=99


for resnet_qps in 75
do
for bert_qps in 6
do
folder=test_$resnet_qps"_"$bert_qps
mkdir -p $TEMP_OUTDIR/result_resnet_bert/$folder
models=resnet_bert
resnet_core_start=0
resnet_core_end=12
resnet_c=4
resnet_llc=0x0ff
resnet_mb=100
bert_core_start=13
bert_core_end=23
bert_c=8
bert_llc=0x700
bert_mb=100


bash $TEMP_OUTDIR/collocation_resnet_bert.sh $folder $resnet_qps $resnet_core_start $resnet_core_end $resnet_c $resnet_llc $resnet_mb $bert_qps $bert_core_start $bert_core_end $bert_c $bert_llc $bert_mb

python3 $TEMP_OUTDIR/generate_data_point_collocation.py --models $models --folder $folder --resnet-qps $resnet_qps --resnet-core-start $resnet_core_start --resnet-core-end $resnet_core_end --resnet-c $resnet_c --resnet-llc $resnet_llc --resnet-mb $resnet_mb --bert-qps $bert_qps --bert-core-start $bert_core_start --bert-core-end $bert_core_end --bert-c $bert_c --bert-llc $bert_llc --bert-mb $bert_mb --total-cores 24 > $TEMP_OUTDIR/data_point/$models"_search/"$folder.data

# python3 $WORK_DIR/generate_data_point_resnet_bert.py --models $models --folder $folder --resnet-qps $resnet_qps --resnet-core-start $resnet_core_start --resnet-core-end $resnet_core_end --resnet-c $resnet_c --resnet-llc $resnet_llc --resnet-mb $resnet_mb --bert-qps $bert_qps --bert-core-start $bert_core_start --bert-core-end $bert_core_end --bert-c $bert_c --bert-llc $bert_llc --bert-mb $bert_mb --total-cores 24 > $WORK_DIR/data_point/resnet_bert_search/$folder.data
done
done