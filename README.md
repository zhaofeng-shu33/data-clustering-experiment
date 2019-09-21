[![Build Status](https://travis-ci.com/zhaofeng-shu33/data-clustering-experiment.svg?branch=master)](https://travis-ci.com/zhaofeng-shu33/data-clustering-experiment)

# Prerequisite
To run the Python code in the directory, you need to install packages listed in `requirements.txt`. You need also to create a directory `build` in the current directory and copy `parameter.json` to the build directory.

Then you can run `python empirical_compare.py`  which loads `parameter.json` to generate the LaTeX table files. After the program finishes, check your result in `compare.tex` in the build directory.

## Parameter tuning

Generally, you do not need to tune the parameters since it is a tedious task and you should try a lot of combinations of different hyper parameters. But sometimes you need to do so. To start tuning your parameter in this experiment, first make sure you finish the steps in prerequisite. Then you need run once

```
python schema.py 
```
This step generates tuning configure file `tuning.json`, then you should modify the parameter combination in this file. The program `fine_tuning.py` just combines them using nested for loop.

By running `python fine_tuning.py` .  Check how to use this problem by providing `--help` switch.

If a better parameter combination is found, The `parameter.json` will be updated automatically.



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
