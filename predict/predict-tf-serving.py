"""
Create a text sequence in Galician by continuing with the text entered
in the command line.
We use a GRU model serving by tensorflow-serving

Library needed: tensorflow_serving,grpc and numpy
Files needed :
    model_weights/best_beiras_gru_textdata_weights.hdf5 .- Network weights
    dictionaries.pkl .- Dictionaries to convert char to int and int to char
    using in learning.
"""

import sys
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc
import tensorflow as tf
import grpc
import numpy as np
sys.path.insert(0, '../aux/')
from beiras_aux import load_coded_dictionaries, predict_next_chars, clean_text


# Input size of the network, the entry text must have the same length
window_size = 100
IP = "localhost:"


def predict_one(text_predict, stub, window_size, number_chars,
                chars_to_indices, indices_to_chars
                ):
    """
    Generate one charazter from text_predict
    params:
        text_predict .- Init text
        stub .-PredictionServiceStub
        window_size .- Size window used by the model
        number_chars .- Number of chars used in train
        chars_to_indices .- Dictionary use for training
        indiced_to_chars.- Dictionary use for training
    return:
        char next in secuence
    """
    # Create nu np input array fron text_predict
    x_test = np.zeros((1, window_size, number_chars))
    for t, char in enumerate(text_predict):
        x_test[0, t, chars_to_indices[char]] = 1.

    # Request prepare
    request = predict_pb2.PredictRequest()
    request.model_spec.name = 'default'
    request.model_spec.signature_name = 'serving_default'
    request.inputs['sequence'].CopyFrom(
            tf.contrib.util.make_tensor_proto(
                                x_test, dtype='float32'
                                )
        )
    # Do the request
    try:
        result = stub.Predict(request)
    except Excep ion as inst:
        print("Fail call tf-serving: " + str(inst))
        sys.exit()
    # Transform response array to char
    test_predict = np.array(result.outputs["scores"].float_val)

    r = np.argmax(test_predict)  # predict class of each test input
    return (indices_to_chars[r])


def predict_window(text_predict, number_predict, window_size):
    """
    Generate a secuence to continue text_predict of len number_predict
    param:
        text_predict .- Init text
        number_predict .- Number chars to generate
        window_size .- The same that used in trainig
   return
        text_predict + number_predict chars
    """
    # Get values used in trainig
    chars_to_indices, indices_to_chars = load_coded_dictionaries()
    number_chars = len(chars_to_indices)
    # Clean input
    input_clean = clean_text(text_predict.lower())
    # Get the stub
    channel = grpc.insecure_channel(IP + str(9000))
    stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
    # Call the service n times
    for i in range(number_predict):
        d = predict_one(
                    input_clean[i:], stub, window_size, number_chars,
                    chars_to_indices, indices_to_chars
                    )
        input_clean += d
    return input_clean


def predict(sentence, number_predict, window_size):
    """
    Return a text sequence predicted by the GRU network continuing
    the input sentence
    :param
        sentence: Input sentence
    :return:
        text sequence
    """
    chars_to_indices, indices_to_chars = load_coded_dictionaries()
    return predict_window(sentence, number_predict, window_size)


if __name__ == "__main__":
    """
    Create a text sequence in Galician by continuing with the text
    entered in the command line.
    Input text must have at least window_size charazters
    (we only use window_size charazters).
    """
    # Read the input sentence
    input_sentence = ' '.join(sys.argv[1:])
    input_sentence = clean_text(input_sentence.lower())

    # Control input sentence len
    if len(input_sentence) < window_size:
        print("Sentence must have ", window_size, len(input_sentence))
        sys.exit(0)
    input_sentence = input_sentence[:window_size]
    # Predict
    predicted = predict(input_sentence, window_size, window_size)
    # Print
    print(predicted)
