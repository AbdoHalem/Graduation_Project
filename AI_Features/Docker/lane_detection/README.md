## Dataset
#### For fully convolutional network
You can download the full training set of images I used [here](https://www.dropbox.com/s/rrh8lrdclzlnxzv/full_CNN_train.p?dl=0) and the full set of 'labels' (which are just the 'G' channel from an RGB image of a re-drawn lane with an extra dimension added to make use in Keras easier) [here](https://www.dropbox.com/s/ak850zqqfy6ily0/full_CNN_labels.p?dl=0) (157 MB).

#### Images with coefficient labels
If you just want the original training images with no flips or rotations (downsized to 80x160x3) you can find them [here](https://www.dropbox.com/s/1bnp70bhaz5kma9/coeffs_train.p?dl=0). You can also find the related coefficient labels (i.e. not the drawn lane labels, but the cofficients for a polynomial line) [here](https://www.dropbox.com/s/ieulvrcooetrlmd/coeffs_labels.p?dl=0).

## Software Requirements
You can use [this conda environment file](lane_environment.yml). In the command line, use `conda env create -f lane_environment.yml` and then `source activate lane_environment` (or just `activate` with the environment name on Windows) to use the environment.

Notice that the req_2.txt file is the one we use to install the libraries on RPI4

On **DockerHub**, you will find 2 images:
1- halem10/lane_publisher:1.0 for receiving frames via socket from RPI4 host
2- halem10/lane_publisher:1.1 for receiving frames from RAM through IPC