# This folder is for generating a docker image to deploy the sign recognition feature on RPI4.
## Models are quantized to be light weight and work effieciently on RPI 4.
### What is Quantization?
Quantization is the process of reducing the precision of the numerical values (such as weights and activations) in a neural network model. Deep learning models are usually trained using 32-bit floating-point numbers (FP32), but for inference, it is often beneficial to use numbers of lower precision, such as 8-bit integers (INT8). Here is why and how this is done:

    Reducing Model Size: Converting from 32-bit floats to 8-bit integers drastically reduces the model’s memory footprint, which is particularly useful for deployment on low-resource devices (e.g., Raspberry Pi 4).

    Speeding Up Inference: Lower-precision operations require less computational power and can be executed faster on CPUs, resulting in lower latency during inference.

    Dynamic Quantization: This technique applies quantization to the model after it has been trained (post-training quantization). For example, using the quantize_dynamic function from the ONNX Runtime library, the model weights are converted to INT8. This conversion is typically done without retraining and usually has a minimal impact on model accuracy while offering significant improvements in speed and size.

    How It Works: The quantization process involves:

        1.Mapping Float Values to Integers: The model’s high-precision weights and activations are scaled and represented using a lower-precision numeric format.

        2.Maintaining Performance: The quantizer usually calibrates the ranges of your data so that the most important features remain intact. This ensures that the model's predictive performance is maintained as much as possible.

#### The YOLO detection model is first exported to ONNX format, then quantized using dynamic quantization from floating-point precision to INT8 precision.

### What is ONNX Format?
ONNX stands for Open Neural Network Exchange. It is an open standard format designed to represent deep learning models. Here’s what makes ONNX useful:

    Interoperability: ONNX enables you to export a model trained in one framework (e.g., PyTorch, TensorFlow, or YOLOv8 via Ultralytics) into a single format. This model can then be deployed or further optimized using different runtime environments such as ONNX Runtime, TensorRT, or others.

    Optimization for Inference: ONNX models are often easier to optimize for CPU inference. They work well on devices with limited resources (like a Raspberry Pi 4) because ONNX Runtime includes various acceleration libraries.

    Flexibility: By converting your model to ONNX, you create a portable version that can be integrated into diverse environments and deployment pipelines without being locked into a specific deep learning framework.

#### The CNN recognition model using dynamic quantization from floating-point precision to INT8 precision.


