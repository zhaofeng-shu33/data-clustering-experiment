[![Build Status](https://travis-ci.com/zhaofeng-shu33/data-clustering-experiment.svg?branch=master)](https://travis-ci.com/zhaofeng-shu33/data-clustering-experiment)

# Prerequisite
To run the Python code in the directory, you need to install packages listed in `requirements.txt`, the package `oss2` is optional but currently the package control is under progress, so you need to install optional package as well.

To start freshly, you need run
```
python schema.py 
```
to generate tuning configure files.

* Use `python fine_tuning.py` to generate or update `parameter.json`.
* Use `python empirical_compare.py` which loads `parameter.json` to generate the LaTeX table files.

## Choices
you can filter out which datasets and methods to use when generating LaTeX table. For example,
```shell
python empirical_compare.py --ignore_computing --dataset Gaussian Circle Iris --method agglomerative affinity_propagation info-clustering --custom_table_name compare_3.tex
```

## About cloud file storage
`TUNING_FILE` and `PARAMETER_FILE` defined in `schema.yaml` can be obtained from and uploaded to the aliyun oss server.
This is used to share the computation results between different workstation.
The upload operation needed authentication.
The GET method does not need authentication.
Download link is [parameter.json](http://data-visualization.leidenschaft.cn/research/info-clustering/code/utility/parameter.json).
If you are impatient, after downloading `parameter.json` and put it in `build/` directory. You can just run the `empirical_compare.py` without `fine_tuning`.

## Basic Plotting
Plotting routines are provided to visualize the clustering result in `plot_art` directory.
You need to install matplotlib package before using it. (`requirements.txt` is not required)
Usage: `python plot_art/plot_art.py --show_pic`. 
