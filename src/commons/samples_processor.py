import numpy

#Adapted from http://zulko.github.io/blog/2014/03/29/soundstretching-and-pitch-shifting-in-python/

class SamplesProcessor(object):
    @staticmethod
    def speed_up(samples, factor):
        indices = numpy.round(numpy.arange(0, samples.shape[0], factor))
        indices = indices[indices < samples.shape[0]].astype(int)
        return samples[indices, :]

    @staticmethod
    def stretch(samples, factor, window_size, hop_size):
        phase  = numpy.zeros(window_size)
        hanning_window = numpy.hanning(window_size)
        result = numpy.zeros(int(round(len(samples)/factor+window_size)), dtype=samples.dtype)

        for i in numpy.arange(0, len(samples)-(window_size+hop_size), int(hop_size*factor)):
            a1 = samples[i: i+window_size]
            a2 = samples[i+hop_size: i+window_size+hop_size]

            s1 =  numpy.fft.fft(hanning_window * a1, )
            s2 =  numpy.fft.fft(hanning_window * a2)
            phase = (phase + numpy.angle(s2/s1)) % 2*numpy.pi
            a2_rephased = numpy.fft.ifft(numpy.abs(s2)*numpy.exp(1j*phase))

            i2 = int(i/factor)
            result[i2 : i2 + window_size] += hanning_window*a2_rephased.real

        return result

    @staticmethod
    def pitch_shift(samples, factor, window_size=2048*24, hop_factor=1./8):
        hop_size = int(window_size*hop_factor)
        #window_size = 2**13
        #hop_size = 2**11
        return SamplesProcessor.speed_up(samples, factor)
        stretched = numpy.zeros(0, dtype=samples.dtype)
        for i in xrange(samples.shape[1]):
            strt = SamplesProcessor.stretch(samples[:, i], 1.0/factor, window_size, hop_size)
            stretched = numpy.append(stretched, strt)
        stretched.shape = (-1, samples.shape[1])
        return SamplesProcessor.speed_up(stretched[window_size:, :], factor)

