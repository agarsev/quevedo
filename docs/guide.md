# Building a Dataset

In this guide, we give an example of the commands and steps needed to create and
use a Quevedo dataset. It might be helpful to have an environment available
where you can test the different commands as you read the guide, and maybe some
data that you can import. The process of creating a dataset is often not
straightforward or works out on the first step, so don't worry about making
mistakes and having to repeat the process (but please don't delete your original
data! Keep those safe in some backup or cloud. Quevedo only works with data it
has copied, so deleting a Quevedo dataset is safe as long as you keep copies of
your original data somewhere).

In this guide we use [git] and [DVC] to manage repository versions and
workflows, but that is not necessary, so you can ignore those steps if you don't
use them. Also, we assume Quevedo is installed and available as the `quevedo`
command, if not, please follow the steps [here](index.md#installation).

## Create repo

To initialize the directory where the data and annotations will live, use the
[`create`](cli.md#create) command:

```shell
$ quevedo -D dataset_name create
```

It will offer you the opportunity to customize the [configuration
file](config.md) for the repository, and set your [annotation
schema](config.md#annotation-schema) and other information. You can modify it
later by editing the `config.toml` file, or using the [`config`](cli.md#config)
command.

From this point on, we will run commands with the dataset directory as working
dir, so change to it with `cd dataset_name`, and we won't need the `-D` flag
anymore.

If you want to use git and/or DVC, initialize the repository with the commands:

```shell
$ git init
$ git add -A .
$ git commit -m "Created quevedo repository"
$ dvc init
$ git commit -m "Initialize DVC"
```

## Add data

Once we have the structure, the first step is to import our data. This can be
done using the [`add_images`](cli.md#add_images) command, specifying both the
source directory and target subset. To specify the target subset, use the `-l`
flag if it's a logogram subset, or `-g` for graphemes. You can specify multiple
source directories, which will be imported to the same subset.

```shell
$ quevedo add_images -i source_image_directory -l logogram_set
```

To track these data with DVC, run:

```shell
$ dvc add logograms/*
$ git add logograms/logogram_set.dvc logograms/.gitignore
$ git commit -m "Imported logograms"
```

## Automatically process the data

After the images are imported, we may want to use some preliminary automatic
processing, like adding some tags that can be determined by code, preprocessing
the images, etc. Create a `scripts` directory if it doesn't exist, and write
your code there according to the [user script
documentation](dev.md#user-scripts). Then you can run it on the appropriate
subsets with the [`run_script`](cli.md#run_script) command.

```shell
$ mkdir scripts
$ vim scripts/script_name.py
$ quevedo run_script -s script_name -l logogram_set
$ dvc add logograms
```

## Annotate the data

Most of the important information in a dataset, apart to the source data, are
the human annotations on these data (otherwise, why bother, right?). Since
Quevedo deals with visual data, a graphical interface is needed for annotation,
and is provided in the form of a [web interface](web.md). Remember to first set
in the configuration file the annotation schema that you want to use, and then
you can lanch the server with the [`web`](cli.md#web) command. If using git and
dvc, remember to add and commit any modifications.

```shell
$ quevedo web
$ dvc add logograms
$ git commit -m "Annotated logograms"
```

## Augment the data

Once logograms are manually annotated, Quevedo can extract the graphemes
included within them to augment the number of grapheme instances available to
us, with the [`extract`](cli.md#extract) command. If what we have are graphemes,
we can generate artificial examples of logograms with the
[`generate`](cli.md#command). With these two commands, the data available for
training increase, hopefully improving our algorithms.

```shell
$ quevedo extract -f logogram_set -t extracted_grapheme_set
$ quevedo generate -f grapheme_set -t generated_logogram_set
```

These steps can be added to a [DVC pipelines
file](https://dvc.org/doc/user-guide/project-structure/pipelines-files) so that
DVC tracks the procedure and the results, and when we distribute the dataset
other people can reproduce the full process. To have dvc automatically fill the
pipelines file, run the commands with
[`dvc run`](https://dvc.org/doc/start/data-pipelines):

```shell
$ dvc run -n extract \
          -d logograms/logogram_set \
          -o graphemes/extracted_set \
          quevedo extract -f logogram_set -t extracted_set
```

## Split

For experimentation, we often need to divide our files into a **train** test on
which to train the algorithms, and a **test** or evaluation set which acts as a
stand-in for "new" or "unknown" data. To have Quevedo perform this split
randomly, use the [`split`](cli.md#split) command:

```shell
$ quevedo split -l logogram_set -p 70
```

This will split the annotations in logogram_set into roughly 70% train files and
30% test files. Depending on your needs, you might want to store this
permanently with DVC by using `dvc add`, or add it as a procedural step in a
pipeline. If you choose this last option, the split command understands a `seed`
parameter so you can make your experiments reproducible.

## Train and test the neural network

Now that our data are properly organized and annotated, we can try training a
neural network and evaluating its results. The first step is to
[`prepare`](cli.md#prepare) the files needed for training, then calling the
darknet binary with the [`train`](cli.md#train) command. Finally, the
[`test`](cli.md#test) command evalates some quick metrics on the trained neural
networks, and can also print all predictions so you can use your statistical
software to get a more in-depth analysis.

The commands can also be chained, so it is enough to run (but it will probably
take some time):

```shell
$ quevedo prepare train test
```

Remember that first you must have [installed darknet](nets.md#installation) and
[configured the neural network](nets.md#network-configuration) in the Quevedo
configuration file. If you have more than one network, specify which one to use
with the `-N` flag:

```shell
$ quevedo -N other_network prepare train test
```

To keep track of the neural network in DVC, we recommend setting preparation,
training and test as different stages in the pipeline, so that intermediate
artifacts can be cached and the expensive process of training only performed if
necessary, and letting DVC track the produced metrics. If you have different
networks, they can be set up as [template
parameters](https://dvc.org/doc/user-guide/project-structure/pipelines-files#templating)
in the pipelines file to keep things
[DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself).

```shell
$ dvc run -n prepare_detect \
          -d logograms \
          -o networks/detect/train.txt \
          quevedo -N detect prepare
$ dvc run -n train_detect \
          -d networks/detect/train.txt \
          -o networks/detect/darknet_final.weights \
          quevedo -N detect train
$ dvc run -n test_detect \
          -d networks/detect/darknet_final.weights \
          -m networks/detect/results.json \
          quevedo -N detect test --results-json
```

## Exploitation

When doing data science, sometimes it is enough to stop at this step. Data are
annotated, neural networks trained, experiments run and conclusions obtained.
But often the results are actually useful beyond the science, and we want to
somehow peruse them. The trained neural network weights are stored in the
[network directory](nets.md#at-the-command-line), and can be used with darknet in other
applications or loaded by
[OpenCV](https://docs.opencv.org/3.4/d6/d0f/group__dnn.html#gafde362956af949cce087f3f25c6aff0d)
for example. If access to the dataset data is needed, and not only the training
results, Quevedo can also be [used as a library](dev.md) from your own code.

[git]: https://git-scm.com/
[DVC]: https://dvc.org/
