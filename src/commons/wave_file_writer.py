import struct, sys

class WaveFileWriter(object):
    def __init__(self, filename=None, fileob=None, sample_rate=None):
        self.filename = filename
        self.fileob = fileob
        self.sample_rate = sample_rate
        self.write_started = False

    def write(self, data):
        #data = data.transpose().astype("f")
        if self.fileob is None:
            fid = self.fileob = open(self.filename, "wb")
        else:
            fid = self.fileob

        if not self.write_started:
            dkind = data.dtype.kind
            if not (dkind == 'i' or dkind == 'f' or (dkind == 'u' and data.dtype.itemsize == 1)):
                raise ValueError("Unsupported data type '%s'" % data.dtype)

            fid.write(b'RIFF')
            fid.write(b'\x00\x00\x00\x00')
            fid.write(b'WAVE')
            # fmt chunk
            fid.write(b'fmt ')
            if dkind == 'f':
                comp = 3
            else:
                comp = 1
            if data.ndim == 1:
                noc = 1
            else:
                noc = data.shape[1]
            bits = data.dtype.itemsize * 8
            sbytes = self.sample_rate*(bits // 8)*noc
            ba = noc * (bits // 8)
            fmt_chunk = struct.pack('<ihHIIHH', 16, comp, noc, self.sample_rate, sbytes, ba, bits)
            fid.write(fmt_chunk)
            # data chunk
            fid.write(b'data')
            fid.flush()
            self.data_start_pos = fid.tell() #12 + len(fmt_chunk) + 4
            self.file_size = None
            self.data_nbytes_total = 0
            self.write_started = True

        fid.seek(self.data_start_pos)
        self.data_nbytes_total += data.nbytes
        fid.write(struct.pack('<i', self.data_nbytes_total))
        fid.flush()

        if self.file_size is not None:
            fid.seek(self.file_size)

        if data.dtype.byteorder == '>' or (data.dtype.byteorder == '=' and sys.byteorder == 'big'):
            data = data.byteswap()
        _array_tofile(fid, data)
        fid.flush()

        self.file_size = fid.tell()
        fid.seek(4)
        fid.write(struct.pack('<i', self.file_size-8))

    def close(self):
        if self.fileob:
            self.fileob.close()
            self.fileob = None

    def get_fileobject(self):
        return self.fileob

if sys.version_info[0] >= 3:
    def _array_tofile(fid, data):
        # ravel gives a c-contiguous buffer
        fid.write(data.ravel().view('b').data)
else:
    def _array_tofile(fid, data):
        fid.write(data.tostring())

