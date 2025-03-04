from enum import Enum

class OpCodes(Enum):
    TERMINATE = 0x00000000
    SIMULATE = 0x00000001
    AGENT_CREATE = 0x01000000
    AGENT_DELETE = 0x01000001
    AGENT_CURRENT_NODE = 0x01100000
    AGENT_PREV_NODE =  0x01100001

MAGIC_NUMBER = 0x4D4D4752.to_bytes(4, 'big')
VERSION = 0x00000001.to_bytes(4, 'big')