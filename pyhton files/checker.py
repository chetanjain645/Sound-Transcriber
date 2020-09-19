from pydub import AudioSegment
song = AudioSegment.from_wav("english.wav")
song.export("testme.flac",format = "flac")
