# Neural networks

One of the difficulties of processing visual languages automatically is input,
when it is presented in the form of images. Images are represented digitally as
collections of pixels, arrayed in memory in a way that makes sense for display
and storage, but which is completely disconnected to the meaning these images
have to humans. Additionally, if input is hand written, graphemes can present
variations which don't affect human understanding but which mean completely
different pixel patterns are present. And positioning of objects is again not
based on hard rules, but rather on visual interpretation.

For these reasons, machine learning techniques developed in the field of
computer vision are necessary to adequately process logograms and graphemes.
While the researcher can use any toolkit and algorithm they prefer, Quevedo
includes a module to facilitate using neural networks with Quevedo datasets.

## Darknet

[Darknet] is "an open source neural network framework written in C and CUDA",
developed by the inventor of the [YOLO] algorithm, Joseph Redmon. This framework
includes a binary and linked library which make configuring, training, and using
neural networks for computer vision straightforward and efficient.

The neural network module included with Quevedo needs darknet to be available.
This module automatically prepares network configuration and training files from
the metadata in the dataset, and can manage the training and prediction
process.

### Installation

We recommend using [this fork by Alexey
Bochkovskiy](https://github.com/AlexeyAB/darknet). Installation can vary
depending on your environment, including the CUDA and OpenCV (optional)
libraries installed, but with luck, the following will work:

```shell
$ git clone https://github.com/AlexeyAB/darknet
$ cd darknet
<edit the Makefile>
$ make
```

In the Makefile, you probably want to enable `GPU=1` and `CUDNN=1`, otherwise
training will be too slow. Depending on the GPU available and CUDA installation,
you might need to change the `ARCH` and `NVCC` variables. For Quevedo to use
Darknet, it is also necessary to set `LIBSO=1` so the linked library is built.
Finally, if you want to use Darknet's data augmentation, you probably want to
set `OPENCV=1` to make it faster.

After darknet is compiled, a binary (named `darknet`) and library
(`libdarknet.so` in linux) will be built. Quevedo needs to know where these
files are, so in the `[darknet]` section of the configuration, the path to the
binary and library must be set. By default, these point to a darknet
directory in the current directory. Some additional arguments to the darknet
binary for training can be set in the `options` key.

## Network configuration

Section in config

## Usage

## Detector

## Classifier

[Darknet]: http://pjreddie.com/darknet/
[YOLO]: https://pjreddie.com/darknet/yolo/
