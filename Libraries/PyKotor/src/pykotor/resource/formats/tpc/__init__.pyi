from .io_bmp import TPCBMPWriter as TPCBMPWriter
from .io_tga import TPCTGAReader as TPCTGAReader, TPCTGAWriter as TPCTGAWriter
from .io_tpc import TPCBinaryReader as TPCBinaryReader, TPCBinaryWriter as TPCBinaryWriter
from .tpc_auto import bytes_tpc as bytes_tpc, detect_tpc as detect_tpc, read_tpc as read_tpc, write_tpc as write_tpc
from .tpc_data import TPC as TPC, TPCTextureFormat as TPCTextureFormat
