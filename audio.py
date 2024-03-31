import wave
import librosa
import numpy as np
import soundfile as sf
from scipy.io import wavfile

class StereoAudioFile:
    """
    Class used for interacting with a stereo audio file
    """
    def __init__(self, name):
        """
        Parameters:
        name : str
            Name of the file
        """
        self.name = name
        
    def read(self) -> None:
        """
        Reads the file and extracts the data
        """
        wav_file = wave.open(self.name, 'rb')
        
        self.sample_rate = wav_file.getframerate()
        self.n_channels = wav_file.getnchannels()
        self.n_frames = wav_file.getnframes()
        
        self.duration = wav_file.getnframes() / wav_file.getframerate()
        
        data = wav_file.readframes(wav_file.getnframes())
        self.channels = np.frombuffer(data, np.int16)
        self.channels.shape = (wav_file.getnframes(), wav_file.getnchannels())
        self.channels = self.channels.T
    
    def write(self, channels, sampwidth, sample_rate) -> None:
        """
        Overwrites the audio file

        Paramters:
        channels: ndarray
            The channel data
        sampwidth: int
            The sample width
        sample_rate: int
            The sample rate

        """
        wave_file = wave.open(self.name, 'wb')
        wave_file.setnchannels(2)
        wave_file.setsampwidth(sampwidth)
        wave_file.setframerate(sample_rate)
        wave_file.writeframes(channels.astype(np.int16).tobytes())
        
    
    def convert_to_mono(self) -> list:
        """
        Converts the stero audio into mono audio

        Returns:
        --------
        mono : list
            The mono samples
        """
        mono = []
        
        for i in range(0, self.n_frames):
            mono.append((np.int16)(((int)(self.channels[0][i]) + (int)(self.channels[1][i])) / 2))
        
        return mono

class MonoAudioFile:
    """
    Class used for interacting with a mono audio file
    """
    def __init__(self, name):
        """
        Parameters:
        -----------
        name: str
            The name of the audio file
        """
        self.name = name
        
    def write(self, sample_rate, mono_data) -> None:
        """
        Writes the mono audio file

        Parameters:
        -----------
        sample_rate: int
            The sample rate
        mono_data: list
            The sample list
        """
        mono_data = np.array(mono_data)
        wavfile.write(self.name, sample_rate, mono_data.astype(np.int16))
    
    def read(self):
        """
        Reads the mono audio file and extracts the data
        """
        wav_file = wave.open(self.name)
        
        self.sample_rate = wav_file.getframerate()
        self.n_channels = wav_file.getnchannels()
        self.n_frames = wav_file.getnframes()
        self.duration = wav_file.getnframes() / wav_file.getframerate()
        self.data = wav_file.readframes(self.n_frames)
        
    def resample_and_save(self, new_name, osr, tsr):
        """
        Resamples and saves the mono audio file

        Parameters:
        -----------
        new_name : str
            The new audio file name
        osr: int
            The original sample rate
        tsr: int
            The target sample rate
        """
        x, sr = librosa.load(self.name, sr=osr)
        y = librosa.resample(x, orig_sr=osr, target_sr=tsr)
        sf.write(new_name, y, tsr, subtype="PCM_16")

class Segment:
    """
    Class used for modeling an audio segment
    """
    def __init__(self, data, timestamp, duration):
        """
        Parameters:
        -----------
        data: ndarray
            The channel data
        timestamp: int
            The starting time of the segment
        duration:
            The length of the segment
        """
        self.data = data
        self.timestamp = timestamp
        self.duration = duration