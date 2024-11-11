import librosa
import numpy as np
import io
from six.moves.urllib.request import urlopen


class AudioAnalyzer:
    def __init__(self):
        self.frequencies_index_ratio = 0
        self.time_index_ratio = 0
        self.spectrogram = None

        self.file = None
        self.file_type = None

    def load(self, file_url: str):
        self.file_type = file_url.split(".")[-1]
        self.file = io.BytesIO(urlopen(file_url).read())
        self.time_series, self.sample_rate = librosa.load(self.file)

        stft = np.abs(librosa.stft(self.time_series, hop_length=512, n_fft=2048 * 4))

        self.spectrogram = librosa.amplitude_to_db(stft, ref=np.max)

        frequencies = librosa.core.fft_frequencies(n_fft=2048 * 4)

        times = librosa.core.frames_to_time(
            np.arange(self.spectrogram.shape[1]),
            sr=self.sample_rate,
            hop_length=512,
            n_fft=2048 * 4,
        )

        self.time_index_ratio = len(times) / times[len(times) - 1]

        self.frequencies_index_ratio = (
            len(frequencies) / frequencies[len(frequencies) - 1]
        )

    def get_decibel(self, target_time, freq):
        return self.spectrogram[int(freq * self.frequencies_index_ratio)][
            int(target_time * self.time_index_ratio)
        ]
