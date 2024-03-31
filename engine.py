import numpy as np
from webrtcvad import Vad
import speech_recognition as sr
from numpy.fft import fft
from audio import MonoAudioFile, Segment, StereoAudioFile

def segment_generator(frame_duration_ms, data, sample_rate) -> list:
    """
    Generates segments

    Parameters:
    -----------
    frame_duration_ms : int
        The frame duration is milliseconds
    data : list
        The audio data to be split
    sample_rate : int
        The sample rate
    """
    # number of bytes that represent a segment
    n_bytes = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    #in seconds
    duration = (float(n_bytes) / sample_rate) / 2.0
    result = []
    while offset + n_bytes < len(data):
        result.append(Segment(data[offset:offset + n_bytes], timestamp, duration))
        timestamp += duration
        offset += n_bytes

    return result

def is_speech(data) -> bool:
    """
    Decides if the audio data is speech

    Parameters:
    -----------
    data : list
        The audio data

    Returns:
    --------
    bool: true, if the audio is predicted as being speech
    """
    x = np.frombuffer(data, np.int16)
    X = fft(x)

    N = len(X)
    n = np.arange(N)
    T = N/16000
    freq = n/T

    all_freq_sum = 0
    voice_freq_sum = 0
    
    # Sum all the samples below 3500 Hz
    for i in range(0, N):
        if freq[i] < 3500:
            voice_freq_sum += np.abs(X[i])
        all_freq_sum += np.abs(X[i])

    # make the decision based on the threshold
    if (voice_freq_sum / all_freq_sum) > 0.4:
        return True
    else:
        return False

def detect_audio_segment(data, sample_rate, frame_duration=10):
    """
    Detects all the segments that contain speech

    Parameters:
    -----------
    data : list
        The data to be processed
    sample_rate : int
        The sample rate
    frame_duration : int
        The frame duration in milliseconds

    Returns:
    --------
    list : the timestamps of the segments that contain speech
    """
    vad = Vad(3)
    
    frames = segment_generator(frame_duration, data, sample_rate)
    frames = list(frames)

    vad_segment = []
    for i, frame in enumerate(frames):
        is_speech1 = vad.is_speech(frame.data, sample_rate)
        if is_speech1:
            vad_segment.append([frame.timestamp, frame.timestamp+frame.duration])

    if len(vad_segment) == 0:
        return []

    start_time = 0
    duration_s = 0.5
    counter = 0
    
    timestamps = []
    
    for x in vad_segment:
        if (x[1] < (start_time + duration_s)):
            counter = counter + 1
        else:
            if counter > 15:
                timestamps.append(start_time)
            counter = 0
            start_time = start_time + duration_s
    
    return timestamps

def generate_intervals(timestamps) -> list:
    """
    Generates the speech intervals based on timestamps

    Parameters:
    -----------
    timestamps : list
        The timestamps that indicate a speech segment

    Returns:
    --------
    list: the intervals
    """
    t1 = timestamps[0]
    t2 = timestamps[0]

    max_pause = 0.5
    max_time = 4.0
    intervals = []

    for i in range(1, len(timestamps)):
        if timestamps[i] - timestamps[i-1] <= max_pause:
            t2 = timestamps[i] + 0.5
        else:
            if t2 - t1 == 0.5:
                intervals.append([t1, t2 + 0.5])
                t1 = timestamps[i]
            else:
                duration = t2 - t1
                if duration <= 0:
                    continue
                n_intervals = (int) ((duration / max_time) + 1)
                mini_segment_duration = duration / n_intervals

                t1_mini = t1

                for j in range(0, n_intervals-1):
                    t2_mini = round(t1_mini + mini_segment_duration)
                    intervals.append([t1_mini, t2_mini])
                    t1_mini = t2_mini
                intervals.append([t1_mini, t2])
                t1 = timestamps[i]

    return intervals

def save_interval_audio(stereo_object, interval, file_name) -> None:
    """
    Saves the audio given to be send for speech recognition

    Parameters:
    -----------
    stereo_object : StereoAudioFile
        The stero object that contains the interval to be processed
    interval : list
        The time points of the segment
    file_name : str
        The file name in which the data will be saved
    """
    start_frame = (int) (interval[0] * stereo_object.n_frames / stereo_object.duration)
    end_frame = (int) (interval[1] * stereo_object.n_frames / stereo_object.duration)
    
    new_channels = stereo_object.channels[:, start_frame : end_frame]
    
    interval_file = StereoAudioFile(file_name)
    interval_file.write(new_channels.T, 2, 44100)

def generate_interval_subtitle(stereo_object, interval) -> None:
    """
    Calls the recognizer

    Parameters:
    -----------
    stereo_object : StereoAudioFile
        The audio to be processed
    interval : list
        The interval to be processed
    """
    save_interval_audio(stereo_object, interval, "./media/temp.wav")
    
    r = sr.Recognizer()
    with sr.AudioFile("./media/temp.wav") as source:
        audio = r.record(source)
    text = r.recognize_google(audio)
    
    return interval, text

def generate_subtitles(audio_file) -> list:
    """
    Generates subtitiles from the audio file

    Parameters:
    ----------
    audio_file : str
        The name of the audio file

    Returns:
    --------
    list : the subtitles generated
    """
    main_audio_file = StereoAudioFile(audio_file)
    main_audio_file.read()

    mono_audio_file = MonoAudioFile("./media/audio_mono.wav")
    mono_data = main_audio_file.convert_to_mono()
    mono_audio_file.write(44100,  mono_data)
    mono_audio_file.resample_and_save("./media/audio_mono_resampled.wav", 44100, 16000)

    mono_resampled_file = MonoAudioFile("./media/audio_mono_resampled.wav")
    mono_resampled_file.read()

    timestamps = detect_audio_segment(mono_resampled_file.data, 16000)

    intervals = generate_intervals(timestamps)
    
    output = []

    for interval in intervals:
        try:
            output.append(generate_interval_subtitle(main_audio_file, interval))
        except:
            output.append([interval, ""])
    
    return output