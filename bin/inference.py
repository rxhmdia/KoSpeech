import argparse
import torch
import torch.nn as nn
import sys
import numpy as np
import torchaudio
sys.path.append('..')
from torch import Tensor
from kospeech.models.deepspeech2.model import DeepSpeech2
from kospeech.models.las.model import ListenAttendSpell
from kospeech.vocabs.ksponspeech import KsponSpeechVocabulary
from kospeech.data.audio.core import load_audio


def parse_audio(audio_path: str, del_silence: bool = False, audio_extension: str = 'pcm') -> Tensor:
    signal = load_audio(audio_path, del_silence, extension=audio_extension)
    feature_vector = torchaudio.compliance.kaldi.fbank(
        waveform=Tensor(signal).unsqueeze(0),
        num_mel_bins=80,
        frame_length=20,
        frame_shift=10,
        window_type='hamming'
    ).transpose(0, 1).numpy()

    feature_vector -= feature_vector.mean()
    feature_vector /= np.std(feature_vector)

    return torch.FloatTensor(feature_vector).transpose(0, 1)


model_path = 'MODEL_PATH'
audio_path = 'AUDIO_PATH'
device = 'cpu'

feature_vector = parse_audio(audio_path, del_silence=True)
input_length = torch.IntTensor([len(feature_vector)])
vocab = KsponSpeechVocabulary('../data/vocab/aihub_character_vocabs.csv')

model = torch.load(model_path, map_location=lambda storage, loc: storage).to(device)
if isinstance(model, nn.DataParallel):
    model = model.module
model.eval()

if isinstance(model, ListenAttendSpell):
    model.encoder.device = device
    model.decoder.device = device

    y_hats = model.greedy_decode(feature_vector.unsqueeze(0), input_length, device)
elif isinstance(model, DeepSpeech2):
    model.device = device
    y_hats = model.greedy_decode(feature_vector.unsqueeze(0), input_length, device)

sentence = vocab.label_to_string(y_hats.cpu().detach().numpy())
print(sentence)
